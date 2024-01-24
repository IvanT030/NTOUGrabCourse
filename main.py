# -*- coding: utf-8 -*-
import logging
import os
from dotenv import load_dotenv
import selenium
from selenium import webdriver
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

from code.login import *
import sys
sys.stdout.encoding
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
api_token = os.getenv("API_TOKEN")


# Defining stages of the conversation
GET_USERNAME, GET_PASSWORD, SUBMIT_PASSWORD, LOGIN ,CONFIRM_PASSWORD,MENU= range(6)
# Callback data
START, BACK_TO_USERNAME, CONFIRM_LOGIN, BACK_TO_PASSWORD,GET_SCORE, LOGOUT = range(6)

def browsereOptions():
    option = webdriver.ChromeOptions()
    option.add_argument('headless') #無介面就被這個設定開啟
    option.add_argument('--start-maximized')
    option.add_argument('--disable-gpu')
    option.add_argument('--window-size=1920,1080')  
    return option

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("登入教學務系統", callback_data=str(START))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("尚未登入教學務系統，請登入：", reply_markup=reply_markup)
    return GET_USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="請輸入教學務系統帳號：")  # This will replace the original message and remove the buttons
    return GET_PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.text.strip()
    context.user_data['username'] = username

    keyboard = [
        [InlineKeyboardButton("上一步", callback_data=str(BACK_TO_USERNAME)),
         InlineKeyboardButton("輸入密碼", callback_data=str(SUBMIT_PASSWORD))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("若要繼續，點選輸入密碼：", reply_markup=reply_markup)
    return SUBMIT_PASSWORD

async def submit_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="請輸入教學務系統密碼：")
    return CONFIRM_PASSWORD

async def confirm_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:  
    password = update.message.text.strip()
    context.user_data['password'] = password
    keyboard = [
        [InlineKeyboardButton("上一步", callback_data=str(BACK_TO_PASSWORD)),
         InlineKeyboardButton("登入", callback_data=str(CONFIRM_LOGIN))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("若確定無誤請按登入：", reply_markup=reply_markup)

    return LOGIN

websiteGrab = None


async def login_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("username: ", context.user_data['username'])
    print("password: ", context.user_data['password'])
    # query = update.callback_query
    # await query.answer()
    global websiteGrab
    if update.callback_query:
        query = update.callback_query
        global websiteGrab
        await query.answer()
        await query.message.reply_text(text="登入資訊已接收，處理中...")
        loginWebsite = webdriver.Chrome(options= browsereOptions())
        websiteGrab, ret = login(loginWebsite,str(context.user_data['username']), str(context.user_data['password']))

        # print("return value: ",websiteGrab, ret)
        return await menu(update, context)  # 调用 menu 函数
    # else:        
    #     await update.message.reply_text("登入失敗請重新操作")
    #     return ConversationHandler.END 


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("查詢成績", callback_data=str(LOGOUT))],
        [InlineKeyboardButton("登出教學務系統", callback_data=str(LOGOUT))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="已登入教學務系統，請選擇：", reply_markup=reply_markup)
    # else:
    #     await update.message.reply_text(text="已登入教學務系統，請選擇：", reply_markup=reply_markup)
    return MENU

async def get_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("get_score")
    print("logout")
    global websiteGrab
    data,websiteGrab = downloadGrade(websiteGrab,"1121")
    print(data)
    print(data)
    keyboard = [
        [InlineKeyboardButton("回主選單", callback_data=str(LOGOUT))],
    ]
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="您已登出教學務系統。")
    return MENU

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # print("logout")
    # data = downloadGrade(websiteGrab,"1121")
    
    # filename = "./code/score.json"
    # with open(filename, 'r', encoding='utf-8') as json_file:
    #     data = json.load(json_file)
    # print(data)

    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="您已登出教學務系統。")
    return LOGIN
def main() -> None:
    application = Application.builder().token(api_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_USERNAME: [
                CallbackQueryHandler(get_username, pattern="^" + str(START) + "$")
            ],
            GET_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)
            ],
            SUBMIT_PASSWORD: [
                CallbackQueryHandler(get_username, pattern="^" + str(BACK_TO_USERNAME) + "$"),
                CallbackQueryHandler(submit_password, pattern="^" + str(SUBMIT_PASSWORD) + "$"),
            ],
            CONFIRM_PASSWORD:[
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_password),
            ],
            LOGIN: [
                CallbackQueryHandler(submit_password, pattern="^" + str(BACK_TO_PASSWORD) + "$"),
                CallbackQueryHandler(login_confirm, pattern="^" + str(CONFIRM_LOGIN) + "$"),
            ],
            MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu),
                CallbackQueryHandler(get_score, pattern="^" + str(GET_SCORE) + "$"),
                CallbackQueryHandler(logout, pattern="^" + str(LOGOUT) + "$"),
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":    
    main()



