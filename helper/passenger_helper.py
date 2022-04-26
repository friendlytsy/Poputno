from os import stat
from aiogram.dispatcher import FSMContext
from create_bot import bot
from aiogram import types
from database import crimgo_db
from text import passenger_text

# Удаления сообщений в списке msg_id_list
async def remove_messages(chat_id, msg_id_list):
    for msg in msg_id_list:
        await bot.delete_message(chat_id=chat_id, message_id=msg)

# Добавления сообщений в data['msg']
async def update_msg_list(msg_id_list, state: FSMContext):
    async with state.proxy() as data:
        # Пустой лист
        msg_list = []
        # Добавляем ИД в список
        msg_list.extend(msg_id_list)
        data['msg'] = msg_list

# Обновления total_amount в state
async def update_state_with_total_amount(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['pp_confirm'] = callback.data
        # Ищем цена билета и считаем итог
        if data['route'] == 'К морю':
            price = await crimgo_db.get_pickup_point_price(data['pickup_point'], data['route'])
        else:
            price = await crimgo_db.get_pickup_point_price(data['drop_point'], data['route'])
        if price is not None: 
            data['total_amount'] = int(data['seat'])*price

# Нотификация о том, что сервер не доступен
async def notify_service_unavailable(callback: types.CallbackQuery, state: FSMContext):
    msg = await callback.message.answer(passenger_text.service_temporary_unavailable)
    # Сохраняем ИД сообщения
    await update_msg_list([msg.message_id], state)
    await callback.answer()
    await state.finish()

# Получить некую дату из state
async def get_data_from_state(from_data_type, state: FSMContext):
    async with state.proxy() as data:
        return data[from_data_type]

# Сохранить некую дату в state
async def save_data_to_state(value, to_data_type, state: FSMContext):
    async with state.proxy() as data:
        data[to_data_type] = value