from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy import create_engine

from sqlalchemy.sql import expression


Base = declarative_base()
DB_URL = 'postgresql://root:password@localhost:5432/sber_test'
engine = create_engine(DB_URL)


class Student(Base):

    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    active = Column(Boolean, server_default=expression.true(), nullable=False)
