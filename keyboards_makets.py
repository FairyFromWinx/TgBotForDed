from enum import Enum
from typing import Union

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy.sql.base import elements


class KeyboardBase(Enum):
    __inline__: bool
    __adjust__: list
    __add_back_button__: bool

    @classmethod
    def as_markup(cls, return_builder=False) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup,
                                                    ReplyKeyboardBuilder, InlineKeyboardBuilder]:
        keyboard = (ReplyKeyboardBuilder() if not cls.__inline__ else InlineKeyboardBuilder())
        class_values = [element.value for element in list(cls) if element.name != "__adjust__"]
        if bool(class_values):
            if cls.__inline__: all(keyboard.button(text=button["text"],
                                      callback_data=button["callback_data"]) for button in class_values)
            else: all(keyboard.button(text=button) for button in class_values)
        keyboard.adjust(*cls.__adjust__)
        if cls.__add_back_button__:
            keyboard.row(KeyboardButton(text="Назад"))
        return keyboard if return_builder else keyboard.as_markup(resize_keyboard=True)

    @classmethod
    def get_values(cls):
        return [element.value for element in list(cls) if element.name not in ["__inline__",
                                                                              "__adjust__"]]

class MainMenuMarkUp(KeyboardBase):
    __inline__ = False
    __adjust__ = [1]
    __add_back_button__ = False

    modules3d = "3Д модули"
    electronics = "Электроника"
    ded = "Дед"