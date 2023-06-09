from sqlmodel import SQLModel, Field, Relationship, String, ARRAY
from sqlalchemy.sql.schema import Column
from typing import Optional, List
from pydantic import EmailStr
from crud import ActiveRecordMixin
from datetime import datetime
import random


# SQL TABLES
class UserParams(SQLModel, ActiveRecordMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    m: str
    n: str
    elliptic_curve: str
    phi_other_p: List[str] = Field(sa_column=Column(ARRAY(String())))
    phi_other_q: List[str] = Field(sa_column=Column(ARRAY(String())))

    sender_user_id: Optional[int] = Field(foreign_key="user.id")
    receiver_user_id: Optional[int] = Field(foreign_key="user.id")
    sender_user: Optional["User"] = Relationship(back_populates="sender_params",
                                                 sa_relationship_kwargs={"uselist": False, "cascade": "delete",
                                                                         "primaryjoin": "UserParams.sender_user_id == User.id"})
    receiver_user: Optional["User"] = Relationship(back_populates="receiver_params",
                                                   sa_relationship_kwargs={"uselist": False, "cascade": "delete",
                                                                           "primaryjoin": "UserParams.receiver_user_id == User.id"})


class Friendship(SQLModel, ActiveRecordMixin, table=True):
    user_id: int = Field(primary_key=True, foreign_key="user.id")
    friend_id: int = Field(primary_key=True, foreign_key="user.id")


class User(SQLModel, ActiveRecordMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: EmailStr
    password: str
    is_verified: bool
    verification_code: Optional[str]
    code_creation_date: Optional[datetime]

    sender_params: "UserParams" = Relationship(back_populates="sender_user",
                                               sa_relationship_kwargs={"uselist": False, "cascade": "delete",
                                                                       "primaryjoin": "UserParams.sender_user_id == User.id",
                                                                       "lazy": "subquery"})
    receiver_params: "UserParams" = Relationship(back_populates="receiver_user",
                                                 sa_relationship_kwargs={"uselist": False, "cascade": "delete",
                                                                         "primaryjoin": "UserParams.receiver_user_id == User.id",
                                                                         "lazy": "subquery"})
    messages_sent: List["Message"] = Relationship(back_populates="sender_user",
                                                  sa_relationship_kwargs={"cascade": "delete", "lazy": "subquery",
                                                                          "primaryjoin": "Message.sender_id == User.id"})
    messages_received: List["Message"] = Relationship(back_populates="receiver_user",
                                                      sa_relationship_kwargs={"cascade": "delete", "lazy": "subquery",
                                                                              "primaryjoin": "Message.receiver_id == User.id"})

    friends: List["User"] = Relationship(link_model=Friendship, sa_relationship_kwargs={
        "primaryjoin": "User.id == Friendship.user_id", "secondaryjoin": "User.id == Friendship.friend_id",
    })


class Message(SQLModel, ActiveRecordMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    sender_user: "User" = Relationship(back_populates="messages_sent",
                                       sa_relationship_kwargs={"cascade": "delete",
                                                               "primaryjoin": "Message.sender_id == User.id"})
    receiver_user: "User" = Relationship(back_populates="messages_received",
                                         sa_relationship_kwargs={"cascade": "delete",
                                                                 "primaryjoin": "Message.receiver_id == User.id"})


# PYDANTIC MODELS

class UserRead(SQLModel):
    username: str


class UserCreate(UserRead):
    email: EmailStr
    password: str


class ConventionalUserCreate(UserCreate):
    is_verified: bool = False
    verification_code: str = random.randbytes(5).hex()
    code_creation_date: datetime = datetime.now()


class Result(SQLModel):
    message: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str


class MessageRead(SQLModel):
    id: int
    content: str
    sender_user: UserRead
    receiver_user: UserRead
