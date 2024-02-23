from login import login
from login import waitForSelectorOrTimeout
from login import findFrameByName
from login import snipeCourse
import asyncio
import aiosqlite
import sqlite3
import threading
from pyppeteer import launch
#courses字串:'哪節:狀態,哪節:狀態' 狀態分成0(還沒搶)，1(正在搶)(防止同時讀檔案的race condition)，2(搶玩了)，3(錯誤)

maxBrowser = 5 #not using yet
task_queue = asyncio.Queue(maxsize=30)
userWeb = {} #{user: [web, resnipe]}
getTaskSleepTime = 2
doTaskSleepTask = 2


async def getTask():#太久沒有接任務可以做成怠速模式
    global task_queue
    while True:
        print('拿任務')
        conn = sqlite3.connect('snapCourse.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM snapCourse LIMIT 1")
        first_row = cursor.fetchone()
        if first_row == None:
            await asyncio.sleep(getTaskSleepTime)
            continue
        await task_queue.put(first_row)
        cursor.execute("DELETE FROM snapCourse WHERE rowid = (SELECT MIN(rowid) FROM snapCourse)")
        conn.commit()
        cursor.close()
        conn.close()
        await asyncio.sleep(getTaskSleepTime)

async def doTask(): 
    conn = sqlite3.connect('userCourse.db')
    cursor = conn.cursor()
    global task_queue
    while True:
        try:
            print('做任務')
            task = task_queue.get_nowait() #task = [account, password, course]
            account = task[0]; password = task[1]; course = task[2]; which = task[3]
            result = ''
            print(account + '開始搶' + course)
            if account not in userWeb:
                browser, _ = await login(task[0], password)
                if browser == None:
                    print(account + 'login error')
                    cursor.execute('SELECT courses FROM userData WHERE account = ?', (account,))
                    totalCourses = cursor.fetchone()  # 檢索第一條符合條件的記錄
                    totalCourses = totalCourses[0].split(',')
                    for i, item in enumerate(totalCourses):
                        key = item.split(':')  # 將字串按照冒號分割成鍵和值 [課號:課名:班別:狀態,]
                        if key[0] == course:
                            totalCourses[i] = f'{key[0]}:{key[1]}:{key[2]}:1'
                            break
                    coureTxt = ','.join(totalCourses)
                    cursor.execute('UPDATE `userData` SET `courses` = ? WHERE `account` IS ?', (coureTxt ,account))
                    conn.commit()
                    continue
                _, _, result = await snipeCourse(False, browser, course, which)
                userWeb[account] = browser
            else:
                _, _, result = await snipeCourse(True, userWeb[account], course, which)
            if result == '人滿':
                await task_queue.put(task)
            cursor.execute('SELECT courses FROM userData WHERE account = ?', (account,))
            totalCourses = cursor.fetchone()  # 檢索第一條符合條件的記錄
            totalCourses = totalCourses[0].split(',')
            for i, item in enumerate(totalCourses):
                key = item.split(':')  # 將字串按照冒號分割成鍵和值
                if key[0] == course:
                    if result == '搶課失敗':
                        totalCourses[i] = f'{key[0]}:{key[1]}:{key[2]}:3'
                    elif result == '搶課成功':
                        totalCourses[i] = f'{key[0]}:{key[1]}:{key[2]}:2'
                    break
            coureTxt = ','.join(totalCourses)
            cursor.execute('UPDATE `userData` SET `courses` = ? WHERE `account` IS ?', (coureTxt ,account))
            conn.commit()

        except asyncio.QueueEmpty:
            #print('task queue is empty! :)))')
            pass
        await asyncio.sleep(doTaskSleepTask)

if __name__ == '__main__':
    getTaskThread = threading.Thread(target= lambda: asyncio.run(getTask()))
    doTaskThread = threading.Thread(target= lambda: asyncio.run(doTask()))
    getTaskThread.start()
    doTaskThread.start()