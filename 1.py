import telebot
from telebot import types

API_TOKEN = '#################################################'
bot = telebot.TeleBot(API_TOKEN)

admin_id = ################################

import json
import os
import sys

def save_data():
    with open('data.json', 'w') as f:
        json.dump({
            "dates": dates,  # Assuming 'dates' is defined somewhere in your code
            "slots_status": slots_status,  # Assuming 'slots_status' is defined somewhere in your code
            "registrations": registrations
        }, f, ensure_ascii=False, indent=4)


DATA_FILE = "data.json"  # Файл для хранения данных

# Переменные для хранения данных
dates = []
time_slots = []
registrations = {}
slots_status = {}


def load_data():
    """Загружает данные из JSON-файла."""
    global dates, slots_status, registrations
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            dates = data.get('dates', [])
            slots_status = data.get('slots_status', {})
            registrations = {str(k): v for k, v in data.get('registrations', {}).items()}
    print("Data loaded successfully.")
    print(f"Loaded registrations: {registrations}")

# Загружаем данные при старте
load_data()


def restart_bot():
    print("Перезапуск бота...")
    os.execv(sys.executable, ['python'] + sys.argv)

def get_display_name(user):
    """Функция для получения тега пользователя или его имени, если тег отсутствует."""
    return f"@{user.username}" if user.username else user.first_name

def create_confirmation_keyboard(user_id, date, slots):
    """Создает клавиатуру для подтверждения записи на конкретную дату и время."""
    keyboard = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton(text="Принять", callback_data=f"accept_{user_id}_{date}")
    reject_button = types.InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}_{date}")
    keyboard.add(accept_button, reject_button)
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Используй команду /record, чтобы записаться! \n\n\n\n Команда /help поможет тебе разобраться со всем!\n\n\n Контакт для связи со мной - ")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Записаться довольно легко! \n\nКоманда /record позволит тебе выбрать дату и время. \n\nВыбрал дату и время? Молодец! \n\nТеперь подожди чуть-чуть, пока администратор примет твою запись! \n\n\n\n\nИ не забудь прийти вовремя! \n\nКонтакт для связи со мной - ")


@bot.message_handler(commands=['i_am_cyborg'])
def send_cyborg(message):
    bot.send_message(message.chat.id, "/check_record - посмотреть запись  \n/add_date - добавляет новую дату.\n/add_time - добавляет новое время.\n/delete_date - удалить дату\n/delete_record - удалить запись")

@bot.message_handler(commands=['record'])
def send_date_picker(message):
    keyboard = types.InlineKeyboardMarkup()
    for date in dates:
        keyboard.add(types.InlineKeyboardButton(text=date, callback_data=f"date_{date}"))
    bot.send_message(message.chat.id, "Выбери дату:", reply_markup=keyboard)

@bot.message_handler(commands=['add_date'])
def add_date(message):
    if message.from_user.id == admin_id:
        msg = bot.send_message(message.chat.id, "Введите новую дату:")
        bot.register_next_step_handler(msg, process_add_date)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

def process_add_date(message):
    new_date = message.text.strip()
    
    if new_date in dates:
        bot.send_message(message.chat.id, f"Дата '{new_date}' уже существует.")
    else:
        dates.append(new_date)
        slots_status[new_date] = {time: True for time in time_slots}  # Создаем слоты для новой даты
        save_data()
        bot.send_message(message.chat.id, f"Дата '{new_date}' успешно добавлена!")

@bot.message_handler(commands=['add_time'])
def add_time(message):
    if message.from_user.id == admin_id:
        keyboard = types.InlineKeyboardMarkup()
        for date in dates:
            keyboard.add(types.InlineKeyboardButton(text=date, callback_data=f"addtime_{date}"))
        bot.send_message(message.chat.id, "Выберите дату для добавления времени:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('addtime_'))
def handle_add_time_date_selection(call):
    selected_date = call.data.split('_')[1]
    msg = bot.send_message(call.message.chat.id, f"Введите время для даты '{selected_date}':")
    bot.register_next_step_handler(msg, lambda m: process_add_time(m, selected_date))
    bot.answer_callback_query(call.id)

def process_add_time(message, selected_date):
    new_time = message.text.strip()
    
    if new_time in slots_status[selected_date]:
        bot.send_message(message.chat.id, f"Время '{new_time}' уже существует для даты '{selected_date}'.")
    else:
        slots_status[selected_date][new_time] = True
        save_data()
        bot.send_message(message.chat.id, f"Время '{new_time}' успешно добавлено для даты '{selected_date}'.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
def handle_date_selection(call):
    user_id = call.from_user.id
    selected_date = call.data.split('_')[1]

# Создаем клавиатуру для выбора времени
    available_slots = [slot for slot, status in slots_status[selected_date].items() if status]
    if available_slots:
        keyboard = types.InlineKeyboardMarkup()
        for slot in available_slots:
            keyboard.add(types.InlineKeyboardButton(text=slot, callback_data=f"time_{selected_date}_{slot}"))
        bot.send_message(call.message.chat.id, "Выбери время:", reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, "К сожалению, все временные слоты для этой даты уже заняты.")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_slot_selection(call):
    user_id = call.from_user.id
    _, selected_date, selected_slot = call.data.split('_')

    if slots_status[selected_date][selected_slot]:
        slots_status[selected_date][selected_slot] = False  # Занять слот

        # Инициализируем список записей пользователя, если его нет
        if str(user_id) not in registrations:
            registrations[str(user_id)] = []  # Приводим user_id к строке

        # Проверяем, есть ли запись на выбранную дату
        user_date_record = next((record for record in registrations[str(user_id)] if record['date'] == selected_date), None)

        if user_date_record:
            user_date_record['slots'].append(selected_slot)  # Добавляем слот к существующей записи
        else:
            registrations[str(user_id)].append({'date': selected_date, 'slots': [selected_slot]})  # Создаем новую запись

        # Уведомление администратору
        bot.send_message(
            admin_id,
            f"Пользователь {get_display_name(call.from_user)} выбрал {selected_date} {selected_slot}.",
            reply_markup=create_confirmation_keyboard(user_id, selected_date, selected_slot)
        )
        bot.answer_callback_query(call.id, text="Ваш выбор принят, ожидайте подтверждения администратора.")
    else:
        bot.answer_callback_query(call.id, text="Этот слот уже занят.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_'))
def handle_acceptance(call):
    user_id, selected_date = call.data.split('_')[1:]
    user_id = str(user_id)  # Преобразуем в строку
    user_record = next((record for record in registrations.get(user_id, []) if record['date'] == selected_date), None)

    if user_record:
        for slot in user_record['slots']:
            bot.send_message(user_id, f"Ваша запись на {selected_date} {slot} подтверждена!")
        # Сохраняем данные один раз после обработки всех слотов
        save_data()
        bot.answer_callback_query(call.id, text="Записи подтверждены.")
    else:
        bot.answer_callback_query(call.id, text="Ошибка при подтверждении записи.")
    restart_bot()

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def handle_rejection(call):
    user_id, selected_date = call.data.split('_')[1:]
    user_id = int(user_id)

    user_record = next((record for record in registrations.get(user_id, []) if record['date'] == selected_date), None)
    if user_record:
        for slot in user_record['slots']:
            slots_status[selected_date][slot] = True  # Освобождаем все выбранные слоты
        registrations[user_id].remove(user_record)  # Удаляем запись о пользователе на эту дату
        bot.send_message(user_id, "Ваши записи отклонены.")
        bot.answer_callback_query(call.id, text="Записи отклонены.")
    else:
        bot.answer_callback_query(call.id, text="Ошибка при отклонении записи.")

@bot.message_handler(commands=['check_record'])
@bot.message_handler(commands=['check_record'])
def check_record(message):
    if message.from_user.id == admin_id:
        if registrations:
            all_records = []  # Список для хранения всех записей
            for user_id, records in registrations.items():
                user_records = f"Пользователь {get_display_name(bot.get_chat(user_id))}:\n"
                user_records += "\n".join([f"  - Дата {record['date']}: слоты {', '.join(record['slots'])}" for record in records])
                all_records.append(user_records)
                
            records_output = "\n\n".join(all_records)  # Объединяем все записи в одну строку
            bot.send_message(admin_id, f"Записи:\n{records_output}")
        else:
            bot.send_message(admin_id, "Нет записей пользователей.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

@bot.message_handler(commands=['delete_record'])
def delete_record(message):
    if message.from_user.id == admin_id:
        if registrations:
            # Генерация списка записей для удаления
            keyboard = types.InlineKeyboardMarkup()
            for user_id, records in registrations.items():
                for record in records:
                    date = record['date']
                    slots = ", ".join(record['slots'])
                    callback_data = f"delete_{user_id}_{date}"
                    # Используем get_display_name вместо bot.get_chat
                    keyboard.add(types.InlineKeyboardButton(
                        text=f"Пользователь {get_display_name(message.from_user)}: {date} ({slots})", 
                        callback_data=callback_data
                    ))
            bot.send_message(admin_id, "Выберите запись для удаления:", reply_markup=keyboard)
        else:
            bot.send_message(admin_id, "Нет записей для удаления.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")







@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_deletion(call):
    print(f"Callback data received: {call.data}")
    _, user_id, selected_date = call.data.split('_')
    user_id = str(user_id)

    print(f"Trying to delete user with ID: {user_id}")
    print(f"Current registrations: {registrations}")

    if user_id in registrations:
        user_records = [record for record in registrations[user_id] if record['date'] == selected_date]
        print(f"User records found: {user_records}")
        if user_records:
            # Create a new list excluding the records to delete
            registrations[user_id] = [
                record for record in registrations[user_id] if record['date'] != selected_date
            ]

            # Free up the occupied slots
            for user_record in user_records:
                for slot in user_record['slots']:
                    slots_status[selected_date][slot] = True

            # If the user has no more records, remove them from the registrations
            if not registrations[user_id]:
                del registrations[user_id]

            save_data()  # Save updated data
            print(f"Records successfully deleted for user {user_id}.")
            bot.answer_callback_query(call.id, text="Записи успешно удалены.")
        else:
            bot.answer_callback_query(call.id, text="Ошибка: записи на указанную дату не найдены.")
    else:
        bot.answer_callback_query(call.id, text=f"Ошибка: пользователь {user_id} не найден в списке записей.")




@bot.message_handler(commands=['my_records'])
def my_records(message):
    user_id = message.from_user.id
    if user_id in registrations and registrations[user_id]:
        # Создаем клавиатуру с записями пользователя
        keyboard = types.InlineKeyboardMarkup()
        for record in registrations[user_id]:
            date = record['date']
            slots = ", ".join(record['slots'])
            callback_data = f"user_delete_{date}"
            keyboard.add(types.InlineKeyboardButton(text=f"{date}: {slots}", callback_data=callback_data))
        bot.send_message(user_id, "Ваши записи:", reply_markup=keyboard)
    else:
        bot.send_message(user_id, "У вас нет активных записей.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_delete_'))
def handle_user_deletion(call):
    user_id = call.from_user.id
    selected_date = call.data.split('_')[2]

    user_record = next((record for record in registrations.get(user_id, []) if record['date'] == selected_date), None)
    if user_record:
        # Освобождаем занятые слоты
        for slot in user_record['slots']:
            slots_status[selected_date][slot] = True
        # Удаляем запись
        registrations[user_id].remove(user_record)
        if not registrations[user_id]:
            del registrations[user_id]  # Удаляем пользователя, если у него нет записей

        bot.answer_callback_query(call.id, text="Запись успешно удалена.")
        bot.send_message(user_id, f"Ваша запись на {selected_date} удалена.")
        bot.send_message(admin_id, f"Пользователь {get_display_name(bot.get_chat(user_id))} удалил свою запись на {selected_date}.")  # Уведомление администратору
    else:
        bot.answer_callback_query(call.id, text="Ошибка: запись не найдена.")



@bot.message_handler(commands=['delete_date'])
def delete_date(message):
    if message.from_user.id == admin_id:
        if dates:
            # Создаем клавиатуру с доступными датами
            keyboard = types.InlineKeyboardMarkup()
            for date in dates:
                keyboard.add(types.InlineKeyboardButton(text=date, callback_data=f"deldate_{date}"))
            bot.send_message(admin_id, "Выберите дату для удаления:", reply_markup=keyboard)
        else:
            bot.send_message(admin_id, "Список дат пуст.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('deldate_'))
def handle_delete_date(call):
    selected_date = call.data.split('_')[1]

    if selected_date in dates:
        # Удаляем дату и её слоты
        dates.remove(selected_date)
        del slots_status[selected_date]
        
        # Удаляем записи пользователей на эту дату
        for user_id in list(registrations.keys()):
            registrations[user_id] = [r for r in registrations[user_id] if r['date'] != selected_date]
            if not registrations[user_id]:
                del registrations[user_id]
        save_data()

        bot.answer_callback_query(call.id, text="Дата успешно удалена.")
        bot.send_message(admin_id, f"Дата '{selected_date}' и все связанные записи удалены.")
    else:
        bot.answer_callback_query(call.id, text="Ошибка: дата не найдена.")





bot.polling()
