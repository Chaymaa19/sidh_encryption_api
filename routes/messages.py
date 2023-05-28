from fastapi import APIRouter, Depends
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
    receiver = User.first_by_field(session, "username", receiver_username)
    query = select(Message).where(or_(Message.sender_id == user.id, Message.sender_id == receiver.id)) \
        .where(or_(Message.receiver_id == receiver.id, Message.receiver_id == user.id)).order_by(
        Message.id.desc()).limit(100)
    result = session.exec(query).all()

    # Decrypt each message
    for i in range(len(result)):
        message = result[i]
        sender_user = User.one_by_id(session, message.sender_id)
        receiver_user = User.one_by_id(session, message.receiver_id)
        # Get encryption parameters
        receiver_m = str(encrypt_data.decrypt(receiver_user.receiver_params.m))
        receiver_n = str(encrypt_data.decrypt(receiver_user.receiver_params.n))
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
        decrypted_message = xor(hash_val, message.content)
        result[i].content = bits_to_string(decrypted_message)

    return result[::-1]
