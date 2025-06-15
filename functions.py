from typing import Union, Type

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select, inspect
from sqlalchemy.orm import NO_VALUE

from bot import bot
from database import Administrator, get_session, User, Parts3d, Electronics


params = {
    "name": "Имя",
    "image": "Изображение",
    "three_mf": ".3mf",
    "weight": "Вес",
    "time_on_A1mini": "Время на A1mini",
    "time_on_P1S": "Время на P1S",
    "filling": "Заполнение",
    "processor": "Процессор",
    "count": "Количество",
    "firm": "Фирма",
    "KW": "KW",
    "size": "Размер",
    "frequencies": "Частоты",
    "frequency": "Частота",
    "voltage": "Вольтаж",
    "model": "Модель",
    "potushnost": "Мощность",
}

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
async def parts_keyboard_constructor(class_: Union[Type[Parts3d], Type[Electronics]], parts_type = None):
    text = 'Список деталей'
    keyboard = ReplyKeyboardBuilder()
    inline_keyboard = InlineKeyboardBuilder()
    session = await get_session()
    keyboard.button(text="Добавить")
    keyboard.button(text="Назад")
    async with session.begin() as session:
        if class_.__tablename__ == Parts3d.__tablename__:
            data = await session.scalars(select(class_))
        else:
            data = await session.scalars(select(class_).where(class_.type == parts_type))
        parts = {}
        for part in data:
            parts.update({part.name: part.count})
        parts = dict(sorted(parts.items())[::-1])
        for name, count in parts.items():
            inline_keyboard.button(text=name + f" x{count}", callback_data=name)
        #all(inline_keyboard.button(text=part.name, callback_data=part.name) for part in data)
    keyboard.adjust(1)
    inline_keyboard.adjust(1)
    return text, keyboard.as_markup(resize_keyboard=True), inline_keyboard.as_markup(resize_keyboard=True)


async def get_part_attrs(part_class: Union[Type[Parts3d], Type[Electronics]]):
    inspected_class = inspect(part_class)
    output_params = {}
    for column in inspected_class.columns.keys():
        if column in params.keys():
            output_params.update({column: "Нет"})
    return output_params

async def get_part_info(part_name, part_class: Union[Type[Parts3d], Type[Electronics]]):
    session = await get_session()
    async with (session.begin() as session):
        # print(part_name, part_class)
        part_info = await session.scalar(select(part_class).where(part_class.name == part_name))
        inspect_obj = inspect(part_info)
        attributes = {}
        for attr in inspect_obj.attrs:
            value = attr.value
            if value is NO_VALUE:
                value = None
            attributes[attr.key] = value
        output = {}
        for attr, value in attributes.items():
            output.update({attr: value})
        return output

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

async def get_image(part_name, part_class: Union[Type[Parts3d], Type[Electronics]]):
    session = await get_session()
    async with session.begin() as session:
        part = await session.scalar(select(part_class).where(part_class.name == part_name))
        return part.image

async def construct_part_info_keyboard(part_name, part_class: Union[Type[Parts3d], Type[Electronics]]):
    part_info = await get_part_info(part_name, part_class)
    inline_keyboard = InlineKeyboardBuilder()
    for attr, value in part_info.items():
        if attr in ["image", "three_mf"]:
            inline_keyboard.button(text=params[attr], callback_data=attr)
        else:
            # print(attr)
            if attr in params.keys():
                inline_keyboard.button(text=f"{params[attr]}: {value}", callback_data=attr)
    inline_keyboard.adjust(1)
    return inline_keyboard.as_markup(resize_keyboard=True)
