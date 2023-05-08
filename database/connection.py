from sqlmodel import SQLModel, Session, create_engine
from utils.config import get_settings
from models import User, UserParams
from utils.utils import setup, create_params
from auth.hash_password import create_hash

settings = get_settings()
engine_url = create_engine(settings.DATABASE_URL)


def conn():
    SQLModel.metadata.create_all(engine_url)


def get_session():
    with Session(engine_url) as session:
        yield session


def populate_database():
    with Session(engine_url) as session:
        alice = User(username="alice", email="alice@example.com",
                     password=create_hash(get_settings().TEST_PASSWORD), is_verified=True)
        if User.first_by_field(session, "username", "alice") is None:
            User.create(session, alice)
            result1, result2 = setup()
            UserParams.create(session, create_params(result1, receiver_id=1))
            UserParams.create(session, create_params(result2, sender_id=1))

        bob = User(username="bob", email="bob@example.com", password=create_hash(get_settings().TEST_PASSWORD),
                   is_verified=True)
        if User.first_by_field(session, "username", "bob") is None:
            User.create(session, bob)
            result1, result2 = setup()
            UserParams.create(session, create_params(result1, receiver_id=2))
            UserParams.create(session, create_params(result2, sender_id=2))
