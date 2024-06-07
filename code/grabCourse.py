from login import login
from login import waitForSelectorOrTimeout
from login import findFrameByName
import asyncio
import aiosqlite
import time
from pyppeteer import launch
from multiprocessing import Process, Event
#有bug 加選成功換了UI 140行那裏要調整 success_type或alaram可能要重新設計
#如果主程式放棄搶某個課但是我的程式已經取資料的時候，需要寫個函式取消該搶課
#外部程式中斷我的程，browser要能成功關掉
fail_types = ('該課程已達人數上限','未找到課程','課程不可選','選取失敗','系統錯誤','年級不可加選！','衝堂不可選！','本類主領域(博雅課程)課程限選2門！')
success_types = ('成功選取','該課程已有加選過')
dialogMsnType = 1
isFirsetSnipe = True
browser = None

async def foreverSnipeCourse(account, pwd, stop_event):
    global browser
    browser, _ = await login(account, pwd)
    while not stop_event.is_set():
        courses = []
        successCourses = []
        #讀一次DB取搶課的資料
        async with aiosqlite.connect('snapCourse.db') as conn:
            await conn.execute("BEGIN")
            try:
                async with conn.execute("SELECT course, classType FROM snapCourse") as cursor:
                    courses = await cursor.fetchall()
                await conn.commit()
                time.sleep(1)
            except Exception as e:
                await conn.rollback()
                print(f"An error occurred: {e}")
        #依照取的資料搶一遍課
        for course in courses:
            browser, state = await snipeCourse(browser, course[0], which= course[1])
            if state == "搶課成功": #搶課程供已經包含以選過的狀況
                print('搶課成功')
                successCourses.append(course)
            else: 
                print('搶失敗 下一個')

        print(f'{successCourses} in exit 1')
        #成功搶到的課在原北DB刪掉，回傳的DB上新增
        async with aiosqlite.connect('snapCourse.db') as db1, aiosqlite.connect('selectedCourse.db') as db2:
            for success_course in successCourses:
                # 删除 snapCourse.db 中的记录
                await db1.execute("DELETE FROM snapCourse WHERE course = ? AND classType = ?", (success_course[0], success_course[1]))
                await db1.commit()
                print(f"Deleted course {success_course[0]} from snapCourse")
                
                # 将记录插入到 selectedCourse.db 中
                await db2.execute("INSERT INTO selectedCourse (Course, ClassType) VALUES (?, ?)", (success_course[0], success_course[1]))
                await db2.commit()
                print(f"Inserted success course {success_course[0]} into selectedCourse")
                
def run_forever_snipe(account, pwd, stop_event):
    asyncio.run(foreverSnipeCourse(account, pwd, stop_event))

async def main():
    stop_event = Event()
    p = Process(target=run_forever_snipe, args=("01157132", 'Ycsm0613', stop_event))
    p.start()
    try:
        while True:
            try:
                user_input = input("Enter 'stop' to end the process: ")
                if user_input.strip().lower() == 'stop':
                    stop_event.set()
                    p.terminate() 
                    p.join()       
                    break
                else:
                    print("Unknown command.")
            except EOFError:
                browser.close()
                break
    except KeyboardInterrupt:
        stop_event.set()
        p.terminate()
        p.join()
        browser.close()
        print("Process interrupted and terminated.")

# 运行测试
if __name__ == "__main__":
    asyncio.run(main())

async def snipeCourse(browser, course, which="A", resnipe = False): #回傳browser跟 搶課狀態
    #resnipe指的是要不要清空輸入欄位
    #which是判斷同課號但不同的課程，分AB班 
    global dialogMsnType
    global isFirsetSnipe
    all_pages = await browser.pages()
    page = all_pages[0]
    menuFrame = None; mainFrame = None
    menuFrame = await findFrameByName(page, 'menuFrame')
    mainFrame = await findFrameByName(page, 'mainFrame')

    if isFirsetSnipe: 
        selectors_and_frames = [
            (menuFrame, '#Menu_TreeViewt1'),
            (menuFrame, '#Menu_TreeViewt31'),
            (menuFrame, '#Menu_TreeViewt41')]

        for frame, selector in selectors_and_frames:
            if await waitForSelectorOrTimeout(frame, selector):
                await frame.click(selector)

    if await waitForSelectorOrTimeout(mainFrame, '#Q_COSID'): #回傳browser跟搶課狀態
        await mainFrame.evaluate(f"""() => {{
            document.getElementById('Q_COSID').value = '';
            document.getElementById('Q_COSID').value = '{course}';
        }}""")
    if await waitForSelectorOrTimeout(mainFrame, '#QUERY_COSID_BTN'):
        await mainFrame.click('#QUERY_COSID_BTN')
    await asyncio.sleep(1)#會抓到其他的

    if await waitForSelectorOrTimeout(mainFrame, '#DataGrid1 tbody tr'):
        trs = await mainFrame.querySelectorAll('#DataGrid1 tbody tr')

    if len(trs) == 2:
        if await waitForSelectorOrTimeout(mainFrame, '#DataGrid1_ctl02_edit'):
            await mainFrame.click('#DataGrid1_ctl02_edit')
    else:
        for i, tr in enumerate(trs):
            if i == 0:
                continue
            tds = await tr.querySelectorAll('td')
            whichClass = await (await tds[3].getProperty('innerText')).jsonValue()
            print(whichClass)
            
            if which: 
                if which.upper() == whichClass.upper():
                    onclick = await tds[0].querySelector('a')
                    print(f'clicked {which}')
                    await onclick.click()
    isFirsetSnipe = False
    tmpDialogMsnType = dialogMsnType; dialogMsnType = 1
    if tmpDialogMsnType == -1 or tmpDialogMsnType == 0:
        print("偵測為搶客失敗")
        return browser, "搶課失敗"
    elif tmpDialogMsnType == 1:
        print("偵測為搶課成功")
        #加選成功 TODO 需要測試
        if await waitForSelectorOrTimeout(mainFrame, '#__SuccessWindow > div > span'):
            await mainFrame.click('#__SuccessWindow > div > span')
        return browser, "搶課成功"