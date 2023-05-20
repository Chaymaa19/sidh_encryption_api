from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from database.connection import get_session
from models import User, Message, MessageRead
from auth.authenticate import authenticate
from utils.utils import *
from subprocess import run, PIPE
import os
from auth import encrypt_data
from sqlmodel import select, or_
from typing import List

messages_router = APIRouter(tags=["messages"])


@messages_router.get("/", response_model=List[MessageRead])
async def retrieve_conversation(receiver_username: str, user: User = Depends(authenticate),
                                session=Depends(get_session)):
    friend = User.first_by_field(session, "username", receiver_username)
    query = select(Message).where(or_(Message.sender_id == user.id, Message.sender_id == friend.id)) \
        .where(or_(Message.receiver_id == friend.id, Message.receiver_id == user.id))
    result = session.exec(query).all()
    return result


@messages_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # data = await websocket.receive_text()
        await websocket.send_text(f"Hola wenas, el mundo es cruel")


@messages_router.post("/encrypt")
async def encrypt(receiver: str, message: str, user: User = Depends(authenticate), session=Depends(get_session)):
    receiver_user = User.first_by_field(session, "username", receiver)
    if not receiver_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Receiver with supplied username doesn't exist!"
        )
    # Get encryption parameters
    sender_m = str(encrypt_data.decrypt(user.sender_params.m))
    sender_n = str(encrypt_data.decrypt(user.sender_params.n))
    receiver_curve = receiver_user.receiver_params.elliptic_curve
    receiver_phi_point_p = receiver_user.receiver_params.phi_other_p
    receiver_phi_point_q = receiver_user.receiver_params.phi_other_q

    # Compute encrypted message
    script_path = os.getcwd() + os.sep + "utils" + os.sep + "get_hash.sage"
    process = run(
        ['sage', script_path, sender_m, sender_n, receiver_curve, str(receiver_phi_point_p), str(receiver_phi_point_q)],
        stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.stdout, process.stderr
    if stderr:
        print(stderr.decode())
    hash_val = stdout.decode().strip()
    bin_msg = str_to_bin(message)
    result = xor(hash_val, bin_msg)

    return {"result": result}


@messages_router.post("/decrypt")
async def decrypt(sender: str, cipher_message: str, user: User = Depends(authenticate), session=Depends(get_session)):
    sender_user = User.first_by_field(session, "username", sender)
    if not sender_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Receiver with supplied username doesn't exist!"
        )
    # Get encryption parameters
    receiver_m = str(encrypt_data.decrypt(user.receiver_params.m))
    receiver_n = str(encrypt_data.decrypt(user.receiver_params.n))
    sender_curve = sender_user.sender_params.elliptic_curve
    sender_phi_point_p = sender_user.sender_params.phi_other_p
    sender_phi_point_q = sender_user.sender_params.phi_other_q

    script_path = os.getcwd() + os.sep + "utils" + os.sep + "get_hash.sage"
    process = run(['sage', script_path, receiver_m, receiver_n, sender_curve, str(sender_phi_point_p),
                   str(sender_phi_point_q)], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.stdout, process.stderr
    if stderr:
        print(stderr.decode())
    hash_val = stdout.decode().strip()
    result = xor(hash_val, cipher_message)

    return {"result": bits_to_string(result)}


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("wss://sidhencryptionapi-production.up.railway.app:8000/messages/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

from fastapi.responses import HTMLResponse


@messages_router.get("/template")
async def get():
    return HTMLResponse(html)
