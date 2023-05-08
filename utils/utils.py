import re
from auth.encrypt_data import encrypt
from subprocess import run, PIPE
import os


def setup():
    script_path = os.getcwd() + os.sep + "utils" + os.sep + "setup.sage"
    process = run(['sage', script_path], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.stdout, process.stderr
    if stderr:
        print(stderr.decode())
    return stdout.decode().strip().split("\n")


def create_params(result, sender_id=None, receiver_id=None):
    m, n, my_E, phi_other_p, phi_other_q = result.split('_')
    phi_other_p = re.findall(r"[0-9a*+ ]+", phi_other_p)
    phi_other_p = [x.strip() for x in phi_other_p]
    phi_other_q = re.findall(r"[0-9a*+ ]+", phi_other_q)
    phi_other_q = [x.strip() for x in phi_other_q]

    param_dict = {
        "m": encrypt(m),
        "n": encrypt(n),
        "elliptic_curve": my_E,
        "phi_other_p": phi_other_p,
        "phi_other_q": phi_other_q,
        "sender_user_id": sender_id,
        "receiver_user_id": receiver_id,
    }
    return param_dict


def str_to_bin(message: str):
    return ''.join('{0:08b}'.format(ord(x)) for x in message)


def make_same_length(a, b):
    if len(a) < len(b):
        a = a * (len(b) // len(a)) + a[:len(b) % len(a)]
    else:
        b = b * (len(a) // len(b)) + b[:len(a) % len(b)]
    return a, b


def xor(a, b):
    if len(a) != len(b):
        a, b = make_same_length(a, b)
    return ''.join('1' if x != y else '0' for x, y in zip(a, b))


def bits_to_string(b):
    return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(b)] * 8))
