import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button
from sqlalchemy.exc import SQLAlchemyError

from db import get_workouts, update_workouts, Workout
from schemas import ClientSchema
from states import ClientEditState
from notification import send_notification


logger = logging.getLogger(__name__)

ID = 'id'
WORKOUT = 'workout'
WORKOUTS = 'workouts'


async def workout_add(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Увеличивает счётчик тренировок клиента на 1.
    """

    workout_db: Workout | None = await _update_workouts(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager
    )

    if workout_db is not None:
        dialog_manager.start_data[WORKOUT] += 1

    else:
        await callback.answer(
            text='Произошла неожиданная ошибка. Попробуйте ещё '
                 'раз или обратитесь в поддержку.',
            show_alert=True,
        )


async def workout_sub(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Уменьшает счётчик тренировок клиента на 1, если текущее количество
    тренировок (включая промежуточное изменение) не опустится ниже нуля.
    """

    workout_db: Workout | None = await _update_workouts(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager
    )

    if workout_db is not None:
        workouts = dialog_manager.start_data[WORKOUTS]

        if workouts + (dialog_manager.start_data[WORKOUT] - 1) > -1:
            dialog_manager.start_data[WORKOUT] -= 1

    else:
        await callback.answer(
            text='Произошла неожиданная ошибка. Попробуйте ещё '
                 'раз или обратитесь в поддержку.',
            show_alert=True,
        )


async def workout_apply(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Применяет изменения к счётчику тренировок клиента.
    Если изменения были успешно сохранены, отправляет уведомление клиенту.
    Если данные изменились во время операции, выводит предупреждение.
    """

    client_id: int = dialog_manager.start_data.get(ID)

    workout_db: Workout | None = await _update_workouts(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )
    if workout_db is None:
        await callback.answer(
            text='Не удалось получить ваши данные о количестве тренировок. '
                 'Обратитесь в службу поддержки.',
            show_alert=True,
        )
        return

    workouts: int = dialog_manager.start_data[WORKOUTS]
    workout: int = dialog_manager.start_data[WORKOUT]

    if workout_db.workouts == workouts:
        try:
            workout_db_new: Workout | None = await update_workouts(
                workout=workout_db,
                workouts=workout+workouts,
                dialog_manager=dialog_manager,
            )
        except SQLAlchemyError as error:
            logger.error(
                'Ошибка при обновлении количества '
                'тренировок клиента client_id=%s, '
                'trainer_id=%s, path=%s',
                dialog_manager.start_data.get(ID),
                dialog_manager.event.from_user.id,
                __name__,
                exc_info=error,
            )
            await callback.answer(
                text='Неудалось обновить ваши данные, попробуйте еще '
                     'раз, пожалуйста.',
                show_alert=True,
            )
            return

        dialog_manager.start_data[WORKOUTS] = workout_db_new.workouts

        text = (
            f'Количество тренировок было изменено, '
            f'теперь у вас {workout_db_new.workouts} тренировок.'
        )
        await send_notification(
            bot=dialog_manager.event.bot,
            user_id=client_id,
            text=text,
        )

    else:
        await callback.answer(
            text=(
                'Во время редактирования, клиент '
                'производил операции связанные с записью, '
                'данные были изменены. '
                'Повторите вашу операцию еще раз, пожалуйста!'
            ),
            show_alert=True,
        )
        dialog_manager.start_data[WORKOUTS] = workout_db.workouts
    dialog_manager.start_data[WORKOUT] = 0


def is_valid_type(code: str):

    sign = ''

    if code.startswith('-'):
        sign = '-'
        code = code[1:]

    if code.isdigit() and int(code) < 100:
        return sign + code

    raise ValueError


async def successful_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str
):

    if text.startswith('-'):
        workout = dialog_manager.start_data[WORKOUT] - int(text[1:])
        if (dialog_manager.start_data[WORKOUTS] + workout) < 0:
            workout = abs(
                dialog_manager.start_data[WORKOUTS] + workout
            ) + workout

    else:
        workout = dialog_manager.start_data[WORKOUT] + int(text)

    dialog_manager.start_data[WORKOUT] = workout


async def error_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError
):

    await message.answer(text='Error code')


async def back_group(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    workout_db: Workout | None = \
        await _update_workouts(callback, widget, dialog_manager)

    if workout_db is None:
        await callback.answer(
            text='Произошла неожиданная ошибка при обновлении ваших '
                 'данных, обратитесь в поддержку или попробуйте '
                 'еще раз.',
            show_alert=True,
        )
        return

    await dialog_manager.done(
        result=dialog_manager.start_data,
        show_mode=ShowMode.EDIT,
    )


async def _update_workouts(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> Workout | None:
    """
    Загружает и обновляет данные о количестве тренировок клиента.
    """

    data_user: dict = dialog_manager.start_data
    client: ClientSchema = ClientSchema.model_validate(data_user)

    try:
        workout_db: Workout | None = await get_workouts(
            dialog_manager=dialog_manager,
            trainer_id=dialog_manager.event.from_user.id,
            client_id=client.id,
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка призагрузке данных о количестве тренировок '
            'клиента client_id=%s, trainer_id=%s, path=%s',
            dialog_manager.start_data.get(ID),
            dialog_manager.event.from_user.id,
            __name__,
            exc_info=error,
        )
        return None

    if workout_db is not None and workout_db.workouts != client.workouts:
        await callback.answer(
            text='Количество тренировок клиента было изменено',
            show_alert=True,
        )
        data_user[WORKOUTS] = workout_db.workouts

    return workout_db


async def to_edit_client(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Переходит в состояние редактирования тренировок клиента,
    предварительно обновив данные о тренировках.
    Если обновление не удалось, выводит сообщение об ошибке.
    """

    workout_db: Workout | None = await _update_workouts(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager
    )

    if workout_db is not None:
        await dialog_manager.switch_to(
            state=ClientEditState.workout_edit,
            show_mode=ShowMode.EDIT,
        )

    else:
        await callback.answer(
            text='Произошла ошибка. Попробуйте ещё '
                 'раз или обратитесь в поддержку.',
            show_alert=True,
        )


async def to_main_client(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:

    workout_db: Workout | None = await _update_workouts(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager
    )

    if workout_db is None:
        await callback.answer(
            text='Возникла неожиданная ошибка, попробуйте еще раз.',
            show_alert=True,
        )
        return

    await dialog_manager.switch_to(
        state=ClientEditState.main,
        show_mode=ShowMode.EDIT,
    )
