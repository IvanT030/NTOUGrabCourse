from login import login
from login import waitForSelectorOrTimeout
from login import findFrameByName
from login import snipeCourse
import asyncio
import aiosqlite
import sqlite3
import threading
from pyppeteer import launch
#courses字串:'哪節:狀態,哪節:狀態' 狀態分成0(還沒搶)，1(正在搶)(防止同時讀檔案的race condition)，2(搶玩了)


maxThread = 5
currentThread = 0

maxBrowser = 5
task_queue = asyncio.Queue(maxsize=10)
userWeb = {} #{user: [web, resnipe]}

async def getTask():#太久沒有接任務可以做成怠速模式
    global currentThread
    global task_queue
    while True:
        print('get Task')
        if currentThread < maxThread:
            conn = sqlite3.connect('snapCourse.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapCourse LIMIT 1")
            first_row = cursor.fetchone()
            print('get value',first_row)
            if first_row == None:
                await asyncio.sleep(2)
                continue
            await task_queue.put(first_row)
            currentThread += 1
            cursor.execute("DELETE FROM snapCourse WHERE rowid = (SELECT MIN(rowid) FROM snapCourse)")
            conn.commit()
            cursor.close()
            conn.close()
        await asyncio.sleep(2)

async def doTask(): 
    global currentThread
    global task_queue
    endLoginTasks = asyncio.Queue()
    endSnipeTasks = asyncio.Queue()
    while True:
        print('the end:', endLoginTasks)
        try:
            #snipeCourseValue = (browser,"...",account,course,(which)不一定)<=tuple
            snipeCourseValue = endLoginTasks.get_nowait() 
            if snipeCourseValue[0] == None:
                currentThread -= 1
                continue
            print('start : ', snipeCourseValue)
            # if snipeCourseValue[2] not in userWeb:
            snipeThread = threading.Thread(target= 
                    lambda: asyncio.run(snipeCourse(False, snipeCourseValue[0], snipeCourseValue[3])))#, snipeCourseValue[4])
            # else:
            #     snipeThread = threading.Thread(target= 
            #         lambda: asyncio.run(snipeCourse(True, snipeCourseValue[0], snipeCourseValue[3])))#, snipeCourseValue[4])
            snipeThread.start()
        except asyncio.QueueEmpty:
            print('end login task is empty! :))')
            pass
        try:
            task = task_queue.get_nowait()
            account = task[0]
            if account not in userWeb:
                logThread = threading.Thread(target= 
                    lambda: asyncio.run(endLoginTasks.put(asyncio.run(login(task[0], task[1])) + (account, task[2]))))
                logThread.start()
                print(account + 'start login')
        except asyncio.QueueEmpty:
            #print('task queue is empty! :)))')
            pass
        await asyncio.sleep(2)

if __name__ == '__main__':
    getTaskThread = threading.Thread(target= lambda: asyncio.run(getTask()))
    doTaskThread = threading.Thread(target= lambda: asyncio.run(doTask()))
    getTaskThread.start()
    doTaskThread.start()

# 提交更改
# conn.commit()
# 關閉連接
# conn.close()