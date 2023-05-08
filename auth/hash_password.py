from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_hash(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_hash(password: str):
    return pwd_context.hash(password)

