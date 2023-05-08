import logging
from typing import Any, Union, Optional
from sqlmodel import select, SQLModel
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import FlushError


class ActiveRecordMixin:
    __config__ = None

    @classmethod
    def one_by_id(cls, session, id: int):
        return session.get(cls, id)

    @classmethod
    def first_by_field(cls, session, field: str, value: Any):
        return cls.first_by_fields(session, {field: value})

    @classmethod
    def first_by_fields(cls, session, fields: dict):
        statement = select(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)
        return session.exec(statement).first()

    @classmethod
    def create(cls, session, source: Union[dict, SQLModel]) -> Optional[SQLModel]:
        obj = cls.convert_without_saving(source)
        if obj is None:
            return None
        if obj.save(session):
            return obj
        return None

    @classmethod
    def convert_without_saving(cls, source: Union[dict, SQLModel]) -> Optional[SQLModel]:
        if isinstance(source, SQLModel):
            obj = cls.from_orm(source)
        elif isinstance(source, dict):
            obj = cls.parse_obj(source)
        return obj

    def save(self, session) -> bool:
        session.add(self)
        try:
            session.commit()
            session.refresh(self)
            return True
        except (IntegrityError, OperationalError, FlushError) as e:
            logging.error(e)
            session.rollback()
            return False

    def update(self, session, source: Union[dict, SQLModel]):
        if isinstance(source, SQLModel):
            source = source.dict(exclude_unset=True)
        for key, value in source.items():
            setattr(self, key, value)
        self.save(session)