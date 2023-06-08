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
        .where(or_(Message.receiver_id == receiver.id, Message.receiver_id == user.id)).order_by(Message.id)
    conversation = session.exec(query).all()

    # User's messages params
    receiver_m1 = str(encrypt_data.decrypt(receiver.receiver_params.m))
    receiver_n1 = str(encrypt_data.decrypt(receiver.receiver_params.n))
    sender_curve1 = user.sender_params.elliptic_curve
    sender_phi_point_p1 = user.sender_params.phi_other_p
    sender_phi_point_q1 = user.sender_params.phi_other_q

    # Receiver's messages params
    receiver_m2 = str(encrypt_data.decrypt(user.receiver_params.m))
    receiver_n2 = str(encrypt_data.decrypt(user.receiver_params.n))
    sender_curve2 = receiver.sender_params.elliptic_curve
    sender_phi_point_p2 = receiver.sender_params.phi_other_p
    sender_phi_point_q2 = receiver.sender_params.phi_other_q
    script_path = os.getcwd() + os.sep + "utils" + os.sep + "get_hash.sage"

    # Get both hashes
    process = run(['sage', script_path, receiver_m1, receiver_n1, sender_curve1, str(sender_phi_point_p1),
                   str(sender_phi_point_q1), receiver_m2, receiver_n2, sender_curve2, str(sender_phi_point_p2),
                   str(sender_phi_point_q2)], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.stdout, process.stderr
    user_hash, receiver_hash = stdout.decode().strip().split("\n")

    # Decrypt messages
    for i in range(len(conversation)):
        message = conversation[i]
        hash_val = user_hash if message.sender_id == user.id else receiver_hash
        decrypted_message = xor(hash_val, message.content)
        conversation[i].content = bits_to_string(decrypted_message)

    return conversation
