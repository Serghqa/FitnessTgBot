import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import ManagedTextInput
from functools import wraps
from string import ascii_lowercase, digits
from typing import Callable

from timezones import get_time_zones
from config import load_config, Config
from db import (
    add_client,
    add_trainer,
    get_trainers,
    get_workouts,
    Trainer,
    Workout,
)
from notification import send_notification
from schemas import ClientSchema, TrainerSchema
from states import ClientState, StartSG, TrainerState


logger = logging.getLogger(__name__)

ID = 'id'
NAME = 'name'
SIMBOLS = ascii_lowercase + digits
RADIO_GROUP = 'radio_group'
RADIO_TZ = 'radio_tz'
TIME_ZONE = 'time_zone'
TRAINERS = 'trainers'
TRAINER_ID = 'trainer_id'
WORKOUTS = 'workouts'


def set_user(
    dialog_manager: DialogManager,
    schema: ClientSchema | TrainerSchema,
    time_zone: str | None = None
) -> ClientSchema | TrainerSchema:

    id = dialog_manager.event.from_user.id
    name = dialog_manager.event.from_user.full_name or 'no_name'

    schema: ClientSchema | TrainerSchema = schema(
        id=id,
        name=name,
        time_zone=time_zone,
    )

    return schema


async def to_trainer_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    trainer_schema: TrainerSchema = TrainerSchema(
        **dialog_manager.start_data
    )

    await dialog_manager.start(
        data=trainer_schema.model_dump(),
        state=TrainerState.main,
        mode=StartMode.RESET_STACK,
    )


async def to_client_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    trainers: list[Trainer] | None = await get_trainers(dialog_manager)

    if trainers is None:
        await callback.answer(
            text='Не получилось получить ваши данные. '
                 'Обратитесь в службу поддержки.',
            show_alert=True,
        )

    elif not trainers:
        await callback.answer(
            text='У вас нет ни одной группы. Обратитесь в службу поддержки.',
            show_alert=True,
        )

    else:
        dialog_manager.dialog_data[TRAINERS] = \
            [trainer.get_data() for trainer in trainers]

        await dialog_manager.switch_to(
            state=StartSG.group,
            show_mode=ShowMode.EDIT,
        )


async def on_trainer(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()

    radio_checked: str = context.widget_data.get(RADIO_GROUP)

    trainer_db: dict = \
        dialog_manager.dialog_data[TRAINERS][int(radio_checked)]
    trainer: TrainerSchema = TrainerSchema(**trainer_db)

    workout: Workout = await get_workouts(
        dialog_manager=dialog_manager,
        trainer_id=trainer.id,
        client_id=dialog_manager.event.from_user.id,
    )

    client: ClientSchema = ClientSchema(
        id=dialog_manager.start_data[ID],
        name=dialog_manager.start_data[NAME],
        workouts=workout.workouts,
    )

    dialog_manager.start_data.clear()
    dialog_manager.start_data[TRAINER_ID] = trainer.id
    dialog_manager.start_data[TIME_ZONE] = trainer.time_zone
    dialog_manager.start_data.update(client.model_dump())

    await dialog_manager.start(
        data=dialog_manager.start_data,
        state=ClientState.main,
        mode=StartMode.RESET_STACK,
    )


def trainer_validate(type_factory: Callable):

    config: Config = load_config()

    @wraps(type_factory)
    def wrapper(code: str):

        if code != config.tg_bot.IS_TRAINER:
            raise ValueError
        result = type_factory(code)
        return result

    return wrapper


@trainer_validate
def is_trainer(code: str) -> str:

    return code


def is_client(code: str) -> str:

    if code.isdigit():
        return code

    raise ValueError


async def trainer_is_valid(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str
):

    await message.delete()

    await dialog_manager.switch_to(
        state=StartSG.set_tz,
        show_mode=ShowMode.EDIT,
    )


async def error_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError
):

    await message.answer(text='Неверный код')


async def client_is_valid(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str
):

    await message.delete()

    client: ClientSchema = set_user(
        dialog_manager=dialog_manager,
        schema=ClientSchema,
    )
    trainer_id = int(text)

    try:
        await add_client(
            dialog_manager=dialog_manager,
            trainer_id=trainer_id,
            client_id=client.id,
            name=client.name,
        )

        text = f'Клиент {client.name} присоединился к группе'

        await send_notification(
            bot=dialog_manager.event.bot,
            user_id=trainer_id,
            text=text,
        )

        user_data: dict = client.model_dump()
        user_data[TRAINER_ID] = trainer_id
        user_data[WORKOUTS] = 0
        user_data[TIME_ZONE] = dialog_manager.dialog_data.get(TIME_ZONE)

        await dialog_manager.start(
            data=user_data,
            state=ClientState.main,
            mode=StartMode.RESET_STACK,
        )
    except ValueError:
        await message.answer(
            text='Неверный номер группы, попробуйте еще раз, пожалуйста!',
        )


async def apply_tz(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()
    item_radio: str = context.widget_data.get(RADIO_TZ)

    timezones: list[str] = get_time_zones()
    local_zone: str = timezones[int(item_radio)]

    trainer: TrainerSchema = set_user(
        dialog_manager=dialog_manager,
        schema=TrainerSchema,
        time_zone=local_zone,
    )

    await add_trainer(
        id=trainer.id,
        name=trainer.name,
        dialog_manager=dialog_manager,
        time_zone=local_zone,
    )

    await dialog_manager.start(
        data=trainer.model_dump(),
        state=TrainerState.main,
        mode=StartMode.RESET_STACK,
    )
