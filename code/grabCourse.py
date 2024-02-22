from login import login
import asyncio
import aiosqlite
import sqlite3
import threading
from pyppeteer import launch
import queue
#courses字串:'哪節:狀態,哪節:狀態' 狀態分成0(還沒搶)，1(正在搶)(防止同時讀檔案的race condition)，2(搶玩了)


maxThread = 2
currentThread = 0

maxBrowser = 5
task_queue = asyncio.Queue(maxsize=10)
userWeb = {}

async def getTask():
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
                await asyncio.sleep(4)
                continue
            await task_queue.put(first_row)
            currentThread += 1
            cursor.execute("DELETE FROM snapCourse WHERE rowid = (SELECT MIN(rowid) FROM snapCourse)")
            conn.commit()
            cursor.close()
            conn.close()
        await asyncio.sleep(4)

async def doTask():
    global currentThread
    global task_queue
    endLoginTasks = asyncio.Queue()
    while True:
        try:
            #(browser,"...",account)
            snipeCourseValue = endLoginTasks.get_nowait() 
            print('find : ', snipeCourseValue)
            logThread = threading.Thread(target= 
                    lambda: asyncio.run(endLoginTasks.put(asyncio.run(login(task[0], task[1])) + (account,))))
            currentThread -= 1
            #await snapCourse()
        except asyncio.QueueEmpty:
            #print('end login task is empty! :))')
            pass
        try:
            task = task_queue.get_nowait()
            account = task[0]
            if account not in userWeb:
                logThread = threading.Thread(target= 
                    lambda: asyncio.run(endLoginTasks.put(asyncio.run(login(task[0], task[1])) + (account,))))
                logThread.start()
                print(account + 'start login')
        except asyncio.QueueEmpty:
            #print('task queue is empty! :)))')
            pass
        await asyncio.sleep(2)

#which處理多個相同課號的
async def snipeCourse(browser, course, which):
    global currentThread
    all_pages = await browser.pages()
    page = all_pages[0]
    await asyncio.sleep(2.5)
    await page.waitForSelector('#menuIFrame')
    await page.waitForSelector('#mainIFrame')
    menuFrame = None; mainFrame = None
    frames = page.frames
    for frame in frames:
        if frame.name == 'menuFrame':
            menuFrame = frame
        elif frame.name == 'mainFrame':
            mainFrame = frame 
    await menuFrame.waitForSelector('#Menu_TreeViewt1')
    await menuFrame.click('#Menu_TreeViewt1')
    await menuFrame.waitForSelector('#Menu_TreeViewt31')
    await menuFrame.click('#Menu_TreeViewt31')
    await menuFrame.waitForSelector('#Menu_TreeViewt41')
    await menuFrame.click('#Menu_TreeViewt41')

    await asyncio.sleep(3)
    await mainFrame.evaluate(f"""() => {{document.getElementById('Q_COSID').value = '{course}';}}""")
    await mainFrame.waitForSelector('#QUERY_COSID_BTN')
    await mainFrame.click('#QUERY_COSID_BTN')

    currentThread -= 1
    



if __name__ == '__main__':
    getTaskThread = threading.Thread(target= lambda: asyncio.run(getTask()))
    doTaskThread = threading.Thread(target= lambda: asyncio.run(doTask()))
    getTaskThread.start()
    doTaskThread.start()

# 提交更改
# conn.commit()
# 關閉連接
# conn.close()