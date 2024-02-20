# -*- coding: utf-8 -*-
import logging
import os
from dotenv import load_dotenv
import selenium
from selenium import webdriver
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from pyppeteer import launch
from code.login import *
from html_content import *
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
GET_USERNAME, GET_PASSWORD, SUBMIT_PASSWORD, LOGIN ,CONFIRM_PASSWORD,PROCESS_SEMESTER,MENU= range(7)
# Callback data
START, BACK_TO_USERNAME, CONFIRM_LOGIN, BACK_TO_PASSWORD, GET_SEMESTER,GET_SCORE,GET_SCHEDULE, LOGOUT = range(8,16)

GRAB_COURSE, INPUT_COURSE_ID, CHECK_COURSE_ID, CHECK_COURSE_ID_AND_BACK_TO_MENU, BACK_TO_MENU, LOOK_GRAB_COURSE_STATE, EDIT_COURSE_STATE ,DELETE_GRAB_COURSE = range(16,24)

def browsereOptions():
    option = webdriver.ChromeOptions()
    option.add_argument('headless') #無介面就被這個設定開啟
    option.add_argument('--start-maximized')
    option.add_argument('--disable-gpu')
    option.add_argument('--window-size=1920,1080')  
    return option

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["userID"] = update.message.from_user.id
    print("user id: ",context.user_data["userID"])
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
    print("login_confirm")
    global websiteGrab
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text(text="登入資訊已接收，處理中...")
        global websiteGrab
        try:
            loginWebsite = webdriver.Chrome(options= browsereOptions())
            websiteGrab, ret = login(loginWebsite,str(context.user_data['username']), str(context.user_data['password']))
            print("return value: ",websiteGrab, ret)
            return await menu(update, context)  # 调用 menu 函数
        except:
            await update.message.reply_text(text="登入失敗請重新操作")
            return ConversationHandler.END


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("menu")
    keyboard = [
        [InlineKeyboardButton("查詢課表", callback_data=str(GET_SCHEDULE))],
        [InlineKeyboardButton("查詢成績", callback_data=str(GET_SCORE))],
        [InlineKeyboardButton("輸入搶課課號", callback_data=str(INPUT_COURSE_ID))],
        [InlineKeyboardButton("修改搶課名單", callback_data=str(LOOK_GRAB_COURSE_STATE))],
        [InlineKeyboardButton("登出教學務系統", callback_data=str(LOGOUT))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(text="已登入教學務系統，請選擇：", reply_markup=reply_markup)
    return MENU

async def get_semester(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("get_semester")
    query = update.callback_query
    await query.answer()
    print("query.data: ",query.data)
    # 根据用户选择设置action
    action = query.data  # 假设callback_data直接传递了操作标记
    context.user_data['action'] = action
    await query.message.reply_text(text="請輸入查詢學期，格式為\"學年\"+\"學期\"，如：1121")
    return PROCESS_SEMESTER

async def process_semester(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    semester = update.message.text.strip()
    print("semester: ",semester)
    context.user_data['semester'] = semester
    action = context.user_data.get('action')
    if action == str(GET_SCORE):
        return await get_score(update, context)
    elif action == str(GET_SCHEDULE):
        return await get_schedule(update, context)
    else:
        print("error")
        return ConversationHandler.END  
    
async def get_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("get_score")
    querySem = context.user_data['semester']
    print("querySem: ",querySem)
    await update.message.reply_text(text="處理中...")
    global websiteGrab
    data,websiteGrab = await downloadGrade(websiteGrab,querySem)

    print(data)
    html_content = scoreTable_head
    html_content += f"""
        <h1>{querySem[:3]}學年度 第{querySem[3]}學期 成績單</h1>
    """
    cnt=0
    classRank="X"
    departmentRank="X"
    semesterAverageGrade="X"
    if len(data[-1]):
        departmentRank=data[-1]
    if len(data[-2]):
        classRank=data[-2]
    if len(data[-3]):
        semesterAverageGrade=data[-3]
    html_content += f"""
    <div class="info-bar">
        <span class="info-item">班排名: {classRank}</span>
        <span class="info-item">系排名: {departmentRank}</span>
        <span class="info-item">學期平均成績: {semesterAverageGrade}</span>
    </div>
    """
    html_content += scoreTable_table
    for item in data:
        if not isinstance(item, dict):
            continue  # 如果不是字典，跳过此次循环
        html_content += f"""
            <tr>
                <td>{item['課號']}</td>
                <td>{item['學分']}</td>
                <td>{item['選別']}</td>
                <td>{item['課名']}</td>
                <td>{item['教授']}</td>
                <td>{item['暫定成績']}</td>
                <td>{item['最終成績']}</td>
            </tr>
        """
    html_content += """
        </table>
        </div>
    </body>
    </html>
    """

    filename = "Myscore.html"

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    keyboard = [
        [InlineKeyboardButton("回主選單", callback_data=str(MENU))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    path_to_screenshot = './score_schreenshot.png'  # 設定截圖保存路徑
    await take_screenshot(html_content, path_to_screenshot)
    await update.message.reply_photo(photo=open(path_to_screenshot, 'rb'))
    await update.message.reply_text(text="請查看成績", reply_markup=reply_markup)
    return await menu(update, context) 

async def take_screenshot(html, path_to_save):
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.setContent(html)
    await page.screenshot({'path': path_to_save,'fullPage': True})
    await browser.close()

async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("get_schedule")
    querySem = context.user_data['semester']
    print("querySem: ",querySem)
    await update.message.reply_text(text="處理中...")
    global websiteGrab
    data,websiteGrab = downloadSchedule(websiteGrab,querySem)
    print(data)
    
    keyboard = [
        [InlineKeyboardButton("回主選單", callback_data=str(MENU))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    path_to_screenshot = './score_schreenshot.png'  # 設定截圖保存路徑
    # await take_screenshot(html_content, path_to_screenshot)
    # await update.message.reply_photo(photo=open(path_to_screenshot, 'rb'))
    await update.message.reply_text(text="請查看課表", reply_markup=reply_markup)
    return await menu(update, context) 

#需要有一個查詢db此user選了多少堂課的function
targetCourse = dict()
async def input_course_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("input_course_id")
    userID = context.user_data["userID"]
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("回主選單", callback_data=str(BACK_TO_MENU))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if userID not in targetCourse:
        targetCourse[userID] = []
    content = f"您已選擇{len(targetCourse[userID])}門課程"
    if len(targetCourse[userID]) > 4:
        content += "，可用額度已滿，若需修改搶課名單，請至\"修改搶課名單\"選項修改"
        await query.edit_message_text(text=content, reply_markup=reply_markup)
        return await menu(update, context)
    else:
        content += f"，還有{4-len(targetCourse[userID])}門課程可選，請輸入搶課課號："
        await query.edit_message_text(text=content,reply_markup=reply_markup)
        return GRAB_COURSE
        

async def confirm_target_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("confirm_target_course")
    targetCourseID = update.message.text.strip()
    context.user_data['targetCourseID'] = targetCourseID
    content = f"您已選擇 {targetCourseID}，請繼續以下操作"

    keyboard = [
        [InlineKeyboardButton("回主選單", callback_data=str(BACK_TO_MENU))]
    ]
    if len(targetCourse[update.message.from_user.id]) < 4:
        keyboard[0].append(InlineKeyboardButton("確認並繼續輸入", callback_data=str(CHECK_COURSE_ID)))
        keyboard[0].append(InlineKeyboardButton("確認並回主選單", callback_data=str(CHECK_COURSE_ID_AND_BACK_TO_MENU)))
    elif len(targetCourse[update.message.from_user.id]) == 4:
        keyboard[0].append(InlineKeyboardButton("確認並回主選單", callback_data=str(CHECK_COURSE_ID_AND_BACK_TO_MENU)))

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=content, reply_markup=reply_markup)
    return GRAB_COURSE

#需要一個檢查課號是否存在的function
async def check_course_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("check_course_id") 
    courseID = context.user_data['targetCourseID']
    # check if courseID exists
    userID = context.user_data["userID"]
    if True:
        targetCourse[userID].append(courseID)
    return await input_course_id(update, context)

async def check_course_id_and_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:  
    print("check_course_id_and_back_to_menu")
    courseID = context.user_data['targetCourseID']
    userID = context.user_data["userID"]
    # check if courseID exists
    if True:
        targetCourse[userID].append(courseID)
    return await menu(update, context)

async def look_grab_course_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("look_grab_course_state")
    query = update.callback_query
    await query.answer()
    userID = context.user_data["userID"]
    if userID not in targetCourse:
        targetCourse[userID] = []
    if len(targetCourse[userID]) == 0:
        content = "您尚未選擇任何課程"
    else:
        content = "您已選擇的課程如下："
    keyboard = []
    print("targetCourse[userID]",targetCourse[userID])
    for course in targetCourse[userID]:
        print("course",course)
        keyboard.append([InlineKeyboardButton(course, callback_data=f"EDIT_COURSE_STATE_{course}"),])
    keyboard.append([InlineKeyboardButton("回主選單", callback_data=str(BACK_TO_MENU))])

    reply_markup = InlineKeyboardMarkup(keyboard)
    print("keyboard",keyboard)

    await query.edit_message_text(text=content, reply_markup=reply_markup)
    return GRAB_COURSE



#需要一個查詢該課程有沒有搶到的function
async def edit_course_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("edit_course_state")
    query = update.callback_query
    await query.answer()
    editedCourse = query.data
    context.user_data["editedCourse"] = editedCourse[18:]
    print("editedCourse",editedCourse   )
    courseID = update.callback_query.data
    userID = context.user_data["userID"]

    #要加上課程有沒有搶到的資訊
    
    content = f"您已選擇 {editedCourse[18:]}，請選擇以下操作："
    keyboard = [
        [InlineKeyboardButton("刪除此搶課課程", callback_data=str(DELETE_GRAB_COURSE)),
        InlineKeyboardButton("回主選單", callback_data=str(BACK_TO_MENU))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text=content, reply_markup=reply_markup)
    return GRAB_COURSE

async def delete_grab_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("delete_grab_course")
    query = update.callback_query
    await query.answer()
    userID = context.user_data["userID"]
    print("context.user_data[editedCourse]",context.user_data["editedCourse"])
    targetCourse[userID].remove(context.user_data["editedCourse"])
    await query.message.reply_text(text="已刪除此搶課課程")
    return await menu(update, context)

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("logout")
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(text="您已登出教學務系統。")
    return START
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
            PROCESS_SEMESTER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_semester)
            ],
            MENU: [
                CallbackQueryHandler(menu, pattern="^" + str(MENU) + "$"),
                CallbackQueryHandler(get_semester, pattern="^" + str(GET_SEMESTER) + "$"),
                CallbackQueryHandler(input_course_id, pattern="^" + str(INPUT_COURSE_ID) + "$"),
                CallbackQueryHandler(get_semester, pattern="^" + str(GET_SCORE) + "$"),
                CallbackQueryHandler(get_semester, pattern="^" + str(GET_SCHEDULE) + "$"),
                CallbackQueryHandler(look_grab_course_state, pattern="^" + str(LOOK_GRAB_COURSE_STATE) + "$"),
                CallbackQueryHandler(logout, pattern="^" + str(LOGOUT) + "$"),
            ],
            GRAB_COURSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_target_course),
                CallbackQueryHandler(menu, pattern="^" + str(BACK_TO_MENU) + "$"),
                CallbackQueryHandler(check_course_id, pattern="^" + str(CHECK_COURSE_ID) + "$"),
                CallbackQueryHandler(check_course_id_and_back_to_menu, pattern="^" + str(CHECK_COURSE_ID_AND_BACK_TO_MENU) + "$"),
                CallbackQueryHandler(edit_course_state, pattern="^" + "EDIT_COURSE_STATE_" ),
                CallbackQueryHandler(delete_grab_course, pattern="^" + str(DELETE_GRAB_COURSE) + "$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":    
    main()