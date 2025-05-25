import asyncio

from sqlalchemy import Integer, String, Float, ForeignKey, Boolean, Enum, Table, Column
from sqlalchemy.orm import DeclarativeBase, foreign
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import registry
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from enum import Enum as PyEnum, unique
from sqlalchemy.orm import polymorphic_union, with_polymorphic

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = Column(Integer(), primary_key=True)
    name: Mapped[str] = Column(String())
    user_id: Mapped[int] = Column(Integer())
    edit_3d: Mapped[Boolean] = Column(Boolean())
    edit_electronics: Mapped[Boolean] = Column(Boolean())
    review_3d: Mapped[Boolean] = Column(Boolean())
    review_electronics: Mapped[Boolean] = Column(Boolean())


class Administrator(Base):
    __tablename__ = 'administrators'

    id: Mapped[int] = Column(Integer(), primary_key=True)
    user_id: Mapped[int] = Column(Integer())

class SpecialPerson(Base):
    __tablename__ = 'special_persons'



    id: Mapped[int] = Column(Integer(), primary_key=True)
    name: Mapped[String] = Column(String())


    # __mapper_args__ = {
    #     'order_by': count
    # }

class Parts3d(Base):
    __tablename__ = 'parts3d'

    id: Mapped[int] = Column(Integer(), primary_key=True)
    image: Mapped[str] = Column(String())
    three_mf: Mapped[str] = Column(String())
    old_three_mf: Mapped[str] = Column(String())
    name: Mapped[str] = Column(String())
    count: Mapped[Integer] = Column(Integer())
    weight: Mapped[Float] = Column(Float())
    time_on_A1mini: Mapped[Float] = Column(Float())
    time_on_P1S: Mapped[Float] = Column(Float())
    filling: Mapped[Float] = Column(Float())


engine = create_async_engine("sqlite+aiosqlite:///database.db", echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> async_sessionmaker:
    session = async_sessionmaker(engine)
    return session

if __name__ == "__main__":
    asyncio.run(init_db())