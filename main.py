# import logging
# from dotenv import load_dotenv
# import os
# from telegram import Update,InlineQueryResultArticle, InputTextMessageContent
# from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler,InlineQueryHandler

# load_dotenv()

# api_token = os.getenv("API_TOKEN")
# print(api_token)

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="你好，我是機器人")

# async def echosss(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text_caps = ' '.join(context.args).upper()
#     await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)
# async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.inline_query.query
#     if not query:
#         return
#     results = []
#     results.append(
#         InlineQueryResultArticle(
#             id=query.upper(),
#             title='Caps',
#             input_message_content=InputTextMessageContent(query.upper())
#         )
#     )
#     await context.bot.answer_inline_query(update.inline_query.id, results)
# if __name__ == '__main__':
#     application = ApplicationBuilder().token(api_token).build()
    
#     echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echosss)

#     start_handler = CommandHandler('start', start)
#     caps_handler = CommandHandler('caps', caps)
#     inline_caps_handler = InlineQueryHandler(inline_caps)
#     application.add_handler(start_handler)
#     application.add_handler(echo_handler)
#     application.add_handler(caps_handler)
#     application.add_handler(inline_caps_handler)
#     application.run_polling()

#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.
#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.
import logging
import os
from dotenv import load_dotenv
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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
api_token = os.getenv("API_TOKEN")
print(api_token)
# Defining stages of the conversation
GET_USERNAME, GET_PASSWORD, CHECK_LOGIN, LOGGED_IN ,CONFIRM_PASSWORD= range(5)
# Callback data
START, BACK_TO_USERNAME, SUBMIT_PASSWORD, CONFIRM_LOGIN, BACK_TO_PASSWORD, LOGOUT = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    keyboard = [
        [InlineKeyboardButton("登入教學務系統", callback_data=str(START))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("尚未登入教學務系統，請登入：", reply_markup=reply_markup)
    return GET_USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for username."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="請輸入教學務系統帳號：")  # This will replace the original message and remove the buttons
    return GET_PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the username and ask for the password."""
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
    """Ask for the password."""
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
    return LOGGED_IN

async def logged_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the conversation after getting the password."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("登出教學務系統", callback_data=str(LOGOUT))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # 使用 edit_message_text 来更新消息内容
        await query.edit_message_text(text="登入資訊已接收，處理中...")
        # await asyncio.sleep(3)  # 模拟登录处理的延迟
        await query.edit_message_text(text="已登入教學務系統，請選擇：", reply_markup=reply_markup)
    elif update.message:
        # 如果是常规消息，则直接回复
        await update.message.reply_text("登入資訊已接收，處理中...")
        # 这里可能需要根据逻辑添加更多的处理代码

    return LOGGED_IN

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the BACK action."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="請輸入教學務系統帳號：")
    return GET_PASSWORD

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle logout."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="您已登出教學務系統。")
    return ConversationHandler.END
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
            CHECK_LOGIN: [
                CallbackQueryHandler(back, pattern="^" + str(BACK_TO_USERNAME) + "$"),
                CallbackQueryHandler(submit_password, pattern="^" + str(SUBMIT_PASSWORD) + "$"),
                CallbackQueryHandler(confirm_password, pattern="^" + str(LOGGED_IN) + "$"),
            ],
            CONFIRM_PASSWORD:[
                CallbackQueryHandler(submit_password, pattern="^" + str(SUBMIT_PASSWORD) + "$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_password),
                CallbackQueryHandler(get_password, pattern="^" + str(BACK_TO_PASSWORD) + "$"),
                CallbackQueryHandler(logged_in, pattern="^" + str(CONFIRM_LOGIN) + "$")

            ],
            LOGGED_IN: [
                CallbackQueryHandler(submit_password, pattern="^" + str(BACK_TO_PASSWORD) + "$"),
                CallbackQueryHandler(logged_in, pattern="^" + str(CONFIRM_LOGIN) + "$"),
                CallbackQueryHandler(logout, pattern="^" + str(LOGOUT) + "$")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
