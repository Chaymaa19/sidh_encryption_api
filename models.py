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
                                                 sa_relationship_kwargs={"uselist": False,
                                                                         "primaryjoin": "UserParams.sender_user_id == User.id"})
    receiver_user: Optional["User"] = Relationship(back_populates="receiver_params",
                                                   sa_relationship_kwargs={"uselist": False,
                                                                           "primaryjoin": "UserParams.receiver_user_id == User.id"})


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


# PYDANTIC MODELS

class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str


class ConventionalUserCreate(UserCreate):
    is_verified: bool = False
    verification_code: str = random.randbytes(5).hex()
    code_creation_date: datetime = datetime.now()


class Message(SQLModel):
    message: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str
