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

from keyboards_makets import ElectronicsTypeMarkUp


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
    old_three_mf: Mapped[str] = Column(String())
    name: Mapped[str] = Column(String())
    count: Mapped[Integer] = Column(Integer())
    image: Mapped[str] = Column(String())
    three_mf: Mapped[str] = Column(String())
    weight: Mapped[Float] = Column(Float())
    time_on_A1mini: Mapped[Float] = Column(Float())
    time_on_P1S: Mapped[Float] = Column(Float())
    filling: Mapped[Float] = Column(Float())


class Electronics(Base):
    __tablename__ = "electronics"

    id: Mapped[int] = Column(Integer(), primary_key=True)
    type: Mapped[str] = Column(String())
    name: Mapped[str] = Column(String())
    count: Mapped[int] = Column(Integer())

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'electronics',
        'polymorphic_load': 'selectin'
    }

class ESC(Electronics):
    __tablename__ = 'esc'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.esc.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    potushnost: Mapped[int] = Column(Integer())
    amperage: Mapped[int] = Column(Integer())
    voltage: Mapped[int] = Column(Integer())


class PoleteStacks(Electronics):
    __tablename__ = 'polete_stacks'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.polete_stacks.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    firm: Mapped[str] = Column(String())
    processor: Mapped[str] = Column(String())


class Motors(Electronics):
    __tablename__ = 'motors'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.motors.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    firm: Mapped[str] = Column(String())
    size: Mapped[int] = Column(Integer())
    KW: Mapped[str] = Column(String())

class Servs(Electronics):
    __tablename__ = 'servs'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.servs.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    firm: Mapped[str] = Column(String())

class Antennas(Electronics):
    __tablename__ = 'antennas'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.antennas.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    firm: Mapped[str] = Column(String())
    frequencies: Mapped[int] = Column(Integer())

class Cameras(Electronics):
    __tablename__ = 'cameras'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.cameras.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    firm: Mapped[str] = Column(String())

class VideoTransmitters(Electronics):
    __tablename__ = 'videotransmitters'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.video_transmitters.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    firm: Mapped[str] = Column(String())
    potushnost: Mapped[int] = Column(Integer())
    frequency: Mapped[int] = Column(Integer())

class Batky(Electronics):
    __tablename__ = 'batky'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.batky.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    firm: Mapped[str] = Column(String())
    amperage: Mapped[int] = Column(Integer())


class AirScrews(Electronics):
    __tablename__ = 'airscrews'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.air_screws.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    size: Mapped[int] = Column(Integer())


class Razbery(Electronics):
    __tablename__ = 'razbery'
    __mapper_args__ = {'polymorphic_identity': ElectronicsTypeMarkUp.razbery.name,
                       'polymorphic_load': 'selectin'}
    id: Mapped[int] = mapped_column(ForeignKey('electronics.id'), primary_key=True)
    model: Mapped[str] = Column(String())

engine = create_async_engine("sqlite+aiosqlite:///database.db", echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> async_sessionmaker:
    session = async_sessionmaker(engine)
    return session

async def add_test_esc():
    session = await get_session()
    async with session.begin() as session:
        session.add(ESC(
            name="TEST",
            count=1,
            potushnost=1,
            amperage=1,
            voltage=1

        ))
        await session.commit()

if __name__ == "__main__":
    asyncio.run(add_test_esc())