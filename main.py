import asyncio
from enum import Enum

from aiogram import Dispatcher, Router, types, filters, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.methods import SendMessage
from aiogram.types import ReplyKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import false, select
from sqlalchemy.util import await_only

from bot import bot
from database import Parts3d, get_session, Electronics, ESC, PoleteStacks, Motors, Servs, Cameras, Antennas, \
    VideoTransmitters, Batky, AirScrews, Razbery
from filters import Registered, Review3d, Edit3d, EditElectronics, ReviewElectronics
from functions import send_register_query, allow_register_query, generate_rights_keyboard, parts_keyboard_constructor, \
    get_part_info, construct_part_info_keyboard, upload_3mf, send_3mf, get_image, get_part_attrs, params
from keyboards_makets import MainMenuMarkUp, ElectronicsTypeMarkUp, KeyboardBase

main_router = Router()

dp = Dispatcher()


async def start():
    dp.include_routers(main_router)
    await dp.start_polling(bot)

class MainStates(StatesGroup):
    property_edit = State()
    in_part3d_info = State()
    in_parts3d = State()
    prepairing_quote = State()
    accepting_quote = State()
    in_main_menu = State()
    in_parts3d_creating = State()
    edit_param_in_creating = State()


class ElectronicsStatesGroup(StatesGroup):
    property_edit = State()
    in_part_info = State()
    in_types_info = State()
    in_types = State()
    in_electronics_creating = State()
    edit_param_in_creating = State()


electronics_types_classes = {
    'part3d': Parts3d,
    ElectronicsTypeMarkUp.esc.name: ESC,
    ElectronicsTypeMarkUp.polete_stacks.name: PoleteStacks,
    ElectronicsTypeMarkUp.motors.name: Motors,
    ElectronicsTypeMarkUp.servs.name: Servs,
    ElectronicsTypeMarkUp.antennas.name: Antennas,
    ElectronicsTypeMarkUp.cameras.name: Cameras,
    ElectronicsTypeMarkUp.video_transmitters.name: VideoTransmitters,
    ElectronicsTypeMarkUp.batky.name: Batky,
    ElectronicsTypeMarkUp.air_screws.name: AirScrews,
    ElectronicsTypeMarkUp.razbery.name: Razbery}




# РЕГИСТРАЦИЯ ---------

@main_router.message(~Registered(), filters.CommandStart(),
                     filters.StateFilter(None))
async def prepare_registration_quote(message: types.Message, state: FSMContext):
    await message.answer("Подготовка к отправке запроса. Введите ФИО")
    await state.set_state(MainStates.prepairing_quote)

@main_router.message(filters.StateFilter(MainStates.prepairing_quote))
async def send_quote(message: types.Message, state: FSMContext):
    if any(i in message.text for i in "'\";!@#$%^&*()_/|+=-`~1234567890"):
        await message.answer("Введенный набор символов не похож на ваше имя")
    else:
        await send_register_query(message.text,
                                  message.from_user.url, message.from_user.id)
        await message.answer("Запрос на регистрацию отправлен успешно!")
    await state.clear()

@main_router.callback_query(F.data == "user_registration_allow")
async def accept_query(query: types.CallbackQuery, state: FSMContext):
    message: types.Message = query.message
    text = message.text.split()
    user_id, userurl, username = text[1], text[2], text[3]
    rights = [False]*4
    markup = ReplyKeyboardBuilder()
    markup.button(text="Подтвердить")
    markup.adjust(1)
    await state.set_state(MainStates.accepting_quote)
    await state.update_data(user_id=user_id, userurl=userurl, username=username, rights=rights)
    await message.answer(".", reply_markup=markup.as_markup(resize_keyboard=True))
    await message.answer("Настройте права для пользователя:", reply_markup=await generate_rights_keyboard(*rights))


@main_router.callback_query(StateFilter(MainStates.accepting_quote))
async def set_right(query: types.CallbackQuery, state: FSMContext):
    message: types.Message = query.message
    rights = await state.get_value("rights")
    match query.data:
        case "review_3d":
            rights[0] = not rights[0]
        case "edit_3d":
            rights[1] = not rights[1]
        case "review_electronics":
            rights[2] = not rights[2]
        case "edit_electronics":
            rights[3] = not rights[3]
    await state.update_data(rights=rights)
    await message.edit_reply_markup(reply_markup=await generate_rights_keyboard(*rights))

@main_router.message(StateFilter(MainStates.accepting_quote), F.text == "Подтвердить")
async def register_user_from_query(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rights = data["rights"]
    await allow_register_query(data['username'], data['user_id'],
                               review_3d=rights[0], edit_3d=rights[1],
                               review_electronics=rights[2], edit_electronics=rights[3])
    await message.answer("Успешно!")
    await state.clear()

@main_router.callback_query(F.data == "user_registration_deny")
async def decline_query(query: types.CallbackQuery, state: FSMContext):
    await query.message.delete()

# --------------------------

# ОСНОВНОЕ МЕНЮ

@main_router.message(StateFilter(None), Registered())
async def send_main_menu(message: types.Message, state: FSMContext):
    await state.set_state(MainStates.in_main_menu)
    await message.answer("Добро пожаловать в главное меню!", reply_markup=MainMenuMarkUp.as_markup())

# 3Д детали --------
@main_router.message(Review3d(), StateFilter(MainStates.in_main_menu), F.text == MainMenuMarkUp.modules3d.value)
async def open_3d_model(message: types.Message, state: FSMContext):
    await state.set_state(MainStates.in_parts3d)
    text, text_keyboard, inline_keyboard = await parts_keyboard_constructor(Parts3d)
    await state.update_data(part_type='part3d')
    await message.answer(".", reply_markup=text_keyboard)
    await message.answer(text, reply_markup=inline_keyboard)

@main_router.callback_query(StateFilter(MainStates.in_parts3d, ElectronicsStatesGroup.in_types_info))
async def get_options(query: types.CallbackQuery, state: FSMContext):
    if await state.get_state() in [MainStates.in_parts3d.state, MainStates.property_edit.state]:
        state_to_set = MainStates.in_part3d_info
        part_class = Parts3d
    else:
        state_to_set = ElectronicsStatesGroup.in_part_info
        part_class = Electronics
    await state.set_state(state_to_set)
    await state.update_data(part_name=query.data, part_query=query)
    keyboard = await construct_part_info_keyboard(query.data, part_class)
    text_keyboard = ReplyKeyboardBuilder().button(text="Назад").button(text="Удалить").as_markup(resize_keyboard=True)
    await query.message.answer('.', reply_markup=text_keyboard)
    # print(await get_image(query.data, part_class))
    if part_class.__tablename__ == Parts3d.__tablename__:
        await query.message.answer_photo(await get_image(query.data, part_class), caption=query.data, reply_markup=keyboard)
        await send_3mf(query.message, query.data, Parts3d)
    else:
        await query.message.answer(query.data, reply_markup=keyboard)

@main_router.callback_query(Edit3d(), StateFilter(MainStates.in_part3d_info))
async def edit_option(query: types.CallbackQuery, state: FSMContext, state_to_set: State = MainStates.property_edit):
    await state.set_state(state_to_set)
    await state.update_data(part_property=query.data)
    await query.message.answer('Введите/отправьте новое значение/файл:')

@main_router.callback_query(EditElectronics(), StateFilter(ElectronicsStatesGroup.in_part_info))
async def edit_electronics_option(query: types.CallbackQuery, state: FSMContext):
    await edit_option(query, state, ElectronicsStatesGroup.property_edit)

@main_router.message(StateFilter(MainStates.property_edit, ElectronicsStatesGroup.property_edit))
async def confirm_edit(message: types.Message, state: FSMContext):
    if await state.get_state() == MainStates.property_edit.state:
        part_class = Parts3d
    else:
        part_class = Electronics
    session = await get_session()
    async with session.begin() as session:
        part = await session.scalar(select(part_class).where(part_class.name == await state.get_value('part_name')))
        part_property = await state.get_value('part_property')
        if part_property == 'image':
            part.image = message.photo[0].file_id
        elif part_property == 'three_mf':
            await upload_3mf(message.document.file_id, part.name, Parts3d)
        else:
            exec(f"part.{part_property} = '{message.text}'")
        await session.commit()
    await message.answer('Успешно!')
    if await state.get_value('part_property') == "name":
        if part_class.__tablename__ == Parts3d.__tablename__:
            await open_3d_model(message, state)
        else:
            await open_electronics(message, state)
    else:
        await get_options(await state.get_value('part_query'), state)



@main_router.message(EditElectronics(), Edit3d(), StateFilter(MainStates.in_parts3d, ElectronicsStatesGroup.in_types_info), F.text == 'Добавить')
async def add_part(message: types.Message, state: FSMContext):
    inline_keyboard_builder = InlineKeyboardBuilder()
    reply_keyboard_builder = ReplyKeyboardBuilder().button(text="Подтвердить").button(text="Назад")
    if await state.get_state() == MainStates.in_parts3d.state:
        await state.set_state(MainStates.in_parts3d_creating)
        part_params = await get_part_attrs(Parts3d)
    else:
        await state.set_state(ElectronicsStatesGroup.in_electronics_creating)
        part_params = await get_part_attrs(electronics_types_classes[await state.get_value("part_type")])
    await state.update_data(part_params=part_params)
    # noinspection PyStatementEffect
    all(inline_keyboard_builder.button(text=f"{params[name]}: {value}", callback_data=name) for name, value in part_params.items())
    inline_keyboard_builder.adjust(1)
    reply_keyboard_builder.adjust(1)


    await message.answer(".", reply_markup=reply_keyboard_builder.as_markup(resize_keyboard=True))
    await message.answer('Настройте параметры:', reply_markup=inline_keyboard_builder.as_markup(resize_keyboard=True))


@main_router.callback_query(StateFilter(MainStates.in_parts3d_creating, ElectronicsStatesGroup.in_electronics_creating))
async def edit_creation_param(query: types.CallbackQuery, state: FSMContext):
    await query.answer("Введите новое значение!!!")
    if await state.get_state() == MainStates.in_parts3d_creating.state:
        await state.set_state(MainStates.edit_param_in_creating)
    else:
        await state.set_state(ElectronicsStatesGroup.edit_param_in_creating)
    await state.update_data(query=query)

@main_router.message(StateFilter(MainStates.edit_param_in_creating, ElectronicsStatesGroup.edit_param_in_creating))
async def edit_creation_param_confirm(message: types.Message, state: FSMContext):
    query: CallbackQuery = await state.get_value('query')
    part_params = await state.get_value('part_params')
    inline_keyboard_builder = InlineKeyboardBuilder()
    reply_keyboard_builder = ReplyKeyboardBuilder().button(text="Подтвердить").button(text="Назад")

    if query.data in ['image', 'three_mf']:

        if query.data == 'image':
            part_params[query.data] = message.photo[0].file_id
        else:
            part_params[query.data] = message.document.file_id
    else:
        part_params[query.data] = message.text
        await message.delete()
    if await state.get_state() == MainStates.edit_param_in_creating:
        await state.set_state(MainStates.in_parts3d_creating)
    else:
        await state.set_state(ElectronicsStatesGroup.in_electronics_creating)
    # noinspection PyStatementEffect
    all(inline_keyboard_builder.button(text=f"{params[name]}: {value}", callback_data=name) for name,value in part_params.items())
    inline_keyboard_builder.adjust(1)
    reply_keyboard_builder.adjust(1)
    await state.update_data(part_params=part_params)
    if query.data in ['image', 'three_mf']:
        await message.answer('.', reply_markup=reply_keyboard_builder.as_markup(resize_keyboard=True))
        await message.answer('Добавление детали', reply_markup=inline_keyboard_builder.as_markup(resize_keyboard=True))
    else:
        await query.message.edit_reply_markup(reply_markup=inline_keyboard_builder.as_markup(resize_keyboard=True))


@main_router.message(StateFilter(MainStates.in_parts3d_creating,ElectronicsStatesGroup.in_electronics_creating), F.text == "Подтвердить")
async def confirm_adding(message: types.Message, state: FSMContext):
    part_params: dict = await state.get_value('part_params')
    part_type = await state.get_value('part_type')
    if "Нет" in params.values():
        await message.answer("Не все поля заполнены!")
    else:
        session = await get_session()
        async with session.begin() as session:
            part_class = electronics_types_classes[part_type]
            part = part_class(**part_params)
            session.add(part)
            await session.commit()
        await message.answer('Успешно!')
        if await state.get_state() == MainStates.in_parts3d_creating:
            await open_3d_model(message, state)
        else:
            await open_electronics(message, state)


# ТОЖЕ ПЕРЕДЕЛАТЬ ПОД ЭЛЕКТРОНИКУ!!!!!!!!!!!
@main_router.message(StateFilter(MainStates.in_part3d_info, ElectronicsStatesGroup.in_part_info), F.text == "Удалить")
async def delete_part(message: types.Message, state: FSMContext):
    part_type = await state.get_value('part_type')
    async with (await get_session()).begin() as session:
        part_class = electronics_types_classes[part_type]
        part = await session.scalar(select(part_class).where(part_class.name == await state.get_value('part_name')))
        await session.delete(part)
        await session.commit()
    await message.answer("Удаление детали прошло успешно!")
    if await state.get_state() == MainStates.in_part3d_info.state:
        await open_3d_model(message, state)
    else:
        await open_electronics(message, state)


@main_router.message(StateFilter(MainStates, ElectronicsStatesGroup), F.text == 'Назад')
async def back_handler(message: types.Message, state: FSMContext):
    match await state.get_state():
        case MainStates.in_part3d_info.state:
            await open_3d_model(message, state)
        case MainStates.in_parts3d.state |\
             MainStates.in_parts3d_creating.state |\
             ElectronicsStatesGroup.in_electronics_creating |\
             ElectronicsStatesGroup.in_types:
            await send_main_menu(message, state)
        case ElectronicsStatesGroup.in_types_info | ElectronicsStatesGroup.in_part_info:
            await open_electronics(message, state)


# -------- ЭЛЕКТРОНИКА !!!!!!!!
@main_router.message(ReviewElectronics(), StateFilter(MainStates.in_main_menu), F.text == MainMenuMarkUp.electronics.value)
async def open_electronics(message: types.Message, state: FSMContext):
    await message.answer("Электроника:", reply_markup=ElectronicsTypeMarkUp.as_markup())
    await state.set_state(ElectronicsStatesGroup.in_types)

@main_router.message(StateFilter(ElectronicsStatesGroup.in_types)) # ФИЛЬТР, ЧТО ЭТО ТИП!!!!!
async def open_type(message: types.Message, state: FSMContext):
    part_type = ElectronicsTypeMarkUp(message.text).name
    text, text_keyboard, inline_keyboard = await parts_keyboard_constructor(Electronics, parts_type=part_type)
    await state.set_state(ElectronicsStatesGroup.in_types_info)
    await state.update_data(part_type=part_type)
    await message.answer(".", reply_markup=text_keyboard)
    await message.answer(text, reply_markup=inline_keyboard)



if __name__ == '__main__':
    asyncio.run(start())
