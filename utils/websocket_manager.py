from fastapi import WebSocket
from database.connection import engine_url
from sqlmodel import Session
from models import User, Message, MessageRead
from auth import encrypt_data
import os
from subprocess import run, PIPE
from utils.utils import *


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        self.active_connections.pop(username)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def save_encrypted_message(self, message: dict):
        with Session(engine_url) as session:
            # Get users
            sender_user = User.first_by_field(session, "username", message["sender_username"])
            receiver_user = User.first_by_field(session, "username", message["receiver_username"])

            # Get encryption parameters
            sender_m = str(encrypt_data.decrypt(sender_user.sender_params.m))
            sender_n = str(encrypt_data.decrypt(sender_user.sender_params.n))
            receiver_curve = receiver_user.receiver_params.elliptic_curve
            receiver_phi_point_p = receiver_user.receiver_params.phi_other_p
            receiver_phi_point_q = receiver_user.receiver_params.phi_other_q

            script_path = os.getcwd() + os.sep + "utils" + os.sep + "get_hash.sage"
            process = run(
                ['sage', script_path, sender_m, sender_n, receiver_curve, str(receiver_phi_point_p),
                 str(receiver_phi_point_q)],
                stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.stdout, process.stderr
            hash_val = stdout.decode().strip()
            bin_msg = str_to_bin(message["message"])
            encrypted_message = xor(hash_val, bin_msg)

            # Save in database
            new_message = Message(content=encrypted_message, sender_id=sender_user.id, receiver_id=receiver_user.id)
            new_message = Message.create(session, new_message)

            # Send message to both users (to show it instantly in the UI)
            message_to_send = {
                "id": new_message.id,
                "sender_user": {"username": sender_user.username},
                "receiver_user": {"username": receiver_user.username},
                "content": message["message"]
            }
            message_to_send = MessageRead(**message_to_send)

            sender_socket = self.active_connections.get(sender_user.username)
            receiver_socket = self.active_connections.get(receiver_user.username)

            if sender_socket:
                await self.send_personal_message(message_to_send.dict(), sender_socket)

            if receiver_socket:
                await self.send_personal_message(message_to_send.dict(), receiver_socket)
