from cryptography.fernet import Fernet
from utils.config import get_settings

key = get_settings().ENCRYPTION_KEY
fernet = Fernet(key)


def encrypt(data: str):
    return fernet.encrypt(data.encode())


def decrypt(encrypted_data: str):
    return fernet.decrypt(encrypted_data).decode()
