from dotenv import load_dotenv
load_dotenv()
import logging
import os, json, base64, asyncio
import gspread
from google.oauth2.service_account import Credentials
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO)

# ===== GOOGLE SHEETS =====
SPREADSHEET_ID = "1ZIMzYUCuYefQxNoBZVlAJiTDV3lq_Zke1CjWibsWsHM"

# Завантажуємо base64 JSON сервісного акаунта
creds_b64 = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not creds_b64:
    raise ValueError("Не знайдено GOOGLE_CREDENTIALS_JSON у змінних оточення")

creds_dict = json.loads(base64.b64decode(creds_b64))
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]
)

client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# ===== TELEGRAM BOT =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не знайдено BOT_TOKEN у змінних оточення")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ===== FSM STATES =====
class Form(StatesGroup):
    name = State()
    phone = State()
    university = State()
    course = State()
    speciality = State()
    practice_place = State()
    practice_dates = State()

# ===== HANDLERS =====
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привіт! 👋 Введи своє ПІБ:")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поділитись номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("📱 Поділися своїм номером телефону:", reply_markup=kb)
    await state.set_state(Form.phone)

@dp.message(Form.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("🏫 Вкажи свій ВНЗ:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.university)

@dp.message(Form.phone)
async def process_phone_text(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("🏫 Вкажи свій ВНЗ:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.university)

@dp.message(Form.university)
async def process_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    await message.answer("📚 На якому ти курсі?")
    await state.set_state(Form.course)

@dp.message(Form.course)
async def process_course(message: Message, state: FSMContext):
    await state.update_data(course=message.text)
    await message.answer("🔢 Вкажи свою спеціальність (номер і назва):")
    await state.set_state(Form.speciality)

@dp.message(Form.speciality)
async def process_speciality(message: Message, state: FSMContext):
    await state.update_data(speciality=message.text)
    await message.answer("🏢 Де хотів би пройти практику та на якій посаді?")
    await state.set_state(Form.practice_place)

@dp.message(Form.practice_place)
async def process_place(message: Message, state: FSMContext):
    await state.update_data(practice_place=message.text)
    await message.answer("📅 Вкажи дати проходження практики:")
    await state.set_state(Form.practice_dates)

@dp.message(Form.practice_dates)
async def process_dates(message: Message, state: FSMContext):
    await state.update_data(practice_dates=message.text)
    data = await state.get_data()
    sheet.append_row([
        data['name'],
        data['phone'],
        data['university'],
        data['course'],
        data['speciality'],
        data['practice_place'],
        data['practice_dates']
    ])
    await message.answer("✅ Дякуємо! Ваші дані збережено.")
    await state.clear()

# ===== RUN =====
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
