from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy import select

from database import get_session, User


class Registered(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        async with (await get_session()).begin() as session:
            query = select(User).where(User.user_id == message.from_user.id)
            result = await session.scalar(query)
            return bool(result)

class Review3d(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        async with (await get_session()).begin() as session:
            query = select(User).where(User.user_id == message.from_user.id)
            result = await session.scalar(query)
            return result.review_3d


class Edit3d(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        async with (await get_session()).begin() as session:
            query = select(User).where(User.user_id == message.from_user.id)
            result = await session.scalar(query)
            return result.edit_3d


class ReviewElectronics(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        async with (await get_session()).begin() as session:
            query = select(User).where(User.user_id == message.from_user.id)
            result = await session.scalar(query)
            return result.review_electronics


class EditElectronics(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        async with (await get_session()).begin() as session:
            query = select(User).where(User.user_id == message.from_user.id)
            result = await session.scalar(query)
            return result.edit_electronics
