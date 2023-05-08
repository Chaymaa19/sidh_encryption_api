from fastapi import APIRouter, Depends, HTTPException, status
from database.connection import get_session
from models import User
from auth.authenticate import authenticate
from utils.utils import *
from subprocess import run, PIPE
import os
from auth import encrypt_data

messages_router = APIRouter(tags=["messages"])


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
