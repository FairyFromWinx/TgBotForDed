from pyexpat.errors import messages
from typing import Union, Type

from aiogram import types
from aiogram.methods import SendMessage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Session

from bot import bot
from database import Administrator, get_session, User, Parts3d


async def send_register_query(username, userurl, user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text='Позволить', callback_data='user_registration_allow')
    builder.button(text='Запретить', callback_data='user_registration_deny')
    session = await get_session()
    async with session.begin() as session:
        administrators = await session.scalars(select(Administrator))
        for administrator in administrators:
            await bot.send_message(chat_id=administrator.user_id,
                              text=f"Пользователь:\n{user_id}\n{userurl}\n{username} желает зарегестрироваться. Принять?",
                              reply_markup=builder.as_markup(resize_keyboard=True))

async def allow_register_query(username, user_id, **kwargs):
    session = await get_session()
    async with session.begin() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        if user:
            return
        else:
            new_user = User(
                            name=username,
                            user_id=user_id,
                            review_3d=kwargs['review_3d'],
                            review_electronics=kwargs['review_electronics'],
                            edit_3d=kwargs['edit_3d'],
                            edit_electronics=kwargs['edit_electronics'],)
            session.add(new_user)
            await session.commit()

async def add_item(table, **kwargs):
    session = await get_session()
    async with session.begin() as session:
        record = table(**kwargs)
        session.add(record)
        await session.commit()

async def generate_rights_keyboard(review_3d, edit_3d,
                                   review_electronics, edit_electronics):
    inline_keyboard = InlineKeyboardBuilder()
    inline_keyboard.button(text=f"Просмотр 3д: "+ ("Да" if review_3d else "Нет"),
                           callback_data="review_3d")
    inline_keyboard.button(text=f"Редактирование 3д: "+ ("Да" if edit_3d else "Нет"),
                           callback_data="edit_3d")
    inline_keyboard.button(text=f"Просмотр электроники "+ ("Да" if review_electronics else "Нет"),
                           callback_data="review_electronics")
    inline_keyboard.button(text=f"Редактирование электроники: "+ ("Да" if edit_electronics else "Нет"),
                           callback_data="edit_electronics")
    inline_keyboard.adjust(1)
    return inline_keyboard.as_markup(resize_keyboard=True)


# noinspection PyStatementEffect
async def parts_keyboard_constructor(class_: Union[Type[Parts3d]]):
    text = 'Список деталей'
    keyboard = ReplyKeyboardBuilder()
    inline_keyboard = InlineKeyboardBuilder()
    session = await get_session()
    keyboard.button(text="Добавить")
    keyboard.button(text="Назад")
    async with session.begin() as session:
        data = await session.scalars(select(Parts3d))
        for part in data:
            print(part.name)
            inline_keyboard.button(text=part.name + f" x{part.count}", callback_data=part.name)
        #all(inline_keyboard.button(text=part.name, callback_data=part.name) for part in data)
    keyboard.adjust(1)
    return text, keyboard.as_markup(resize_keyboard=True), inline_keyboard.as_markup(resize_keyboard=True)


async def get_part_info(part_name, part_class: Union[Type[Parts3d]]):
    session = await get_session()
    async with (session.begin() as session):
        part_info = await session.scalar(select(part_class).where(part_class.name == part_name))
        if isinstance(part_info, Parts3d):
            return {'name': part_info.name,
                    'count': part_info.count,
                    'weight': part_info.weight,
                    'A1mini': part_info.time_on_A1mini,
                    'P1S': part_info.time_on_P1S,
                    'filling': part_info.filling,}

async def send_3mf(message: types.Message, part_name, part_class: Union[Type[Parts3d]]):
    session = await get_session()
    async with session.begin() as session:
        part = await session.scalar(select(part_class).where(part_class.name == part_name))
        three_mf: str = part.three_mf
        old_three_mf: str = part.old_three_mf
    if three_mf:
        await message.answer(".3mf:")
        await message.answer_document(three_mf)
    else:
        await message.answer("Не обнаружено")
        return False
    if old_three_mf:
        await message.answer("Старый .3mf:")
        await message.answer_document(old_three_mf)
    return True


async def upload_3mf(three_mf_id, part_name, part_class: Union[Type[Parts3d]]):
    session = await get_session()
    async with session.begin() as session:
        part = await session.scalar(select(part_class).where(part_class.name == part_name))
        old_three_mf = part.three_mf
        part.three_mf = three_mf_id
        part.old_three_mf = old_three_mf
        await session.commit()

async def get_image(part_name, part_class: Union[Type[Parts3d]]):
    session = await get_session()
    async with session.begin() as session:
        part = await session.scalar(select(part_class).where(part_class.name == part_name))
        return part.image

async def construct_part_info_keyboard(part_name, part_class: Union[Type[Parts3d]]):
    part_info = await get_part_info(part_name, part_class)
    inline_keyboard = InlineKeyboardBuilder()
    #if isinstance(part_class, Parts3d):
    inline_keyboard.button(text=f'Имя: {part_info["name"]}', callback_data='name')
    inline_keyboard.button(text=f'Изображение', callback_data='image')
    inline_keyboard.button(text=f'Количество: x{part_info["count"]}', callback_data='count')
    inline_keyboard.button(text=f'Вес: {part_info["weight"]}', callback_data='weight')
    inline_keyboard.button(text=f'Время на А1mini: {part_info["A1mini"]}', callback_data='A1mini')
    inline_keyboard.button(text=f'Время на P1S: {part_info["P1S"]}', callback_data='P1S')
    inline_keyboard.button(text=f'Заполнение: {part_info["filling"]}', callback_data='filling')
    inline_keyboard.button(text=f'.3mf', callback_data='three_mf')
    inline_keyboard.adjust(1)
    return inline_keyboard.as_markup(resize_keyboard=True)
