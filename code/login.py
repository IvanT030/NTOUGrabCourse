#python 3.11
import asyncio
from pyppeteer import launch
from pyppeteer import dialog
# from pyppeteer.errors import TimeoutErro
from PIL import Image
import ddddocr
import re
import time
import aiosqlite

fail_types = ('未找到課程','課程不可選','選取失敗','該課程已達人數上限','系統錯誤','年級不可加選！','衝堂不可選！')
success_types = ('本科目設有檢查人數下限。選本課程，在未達下限人數前時無法退選，確定加選?', '成功選取')
msn = -1
dialogHandled = asyncio.Event()

async def findFrameByName(page, frameName):
    def frameExists(page, name):
        return name in [frame.name for frame in page.frames]
    while not frameExists(page, frameName):
        await asyncio.sleep(0.1)  
    for frame in page.frames:
        if frame.name == frameName:
            return frame

async def waitForSelectorOrTimeout(frame, selector, timeout=30000):
    try:
        await frame.waitForSelector(selector, {'visible': True})
        return True
    except TimeoutError:
        print(f"Timeout while waiting for {selector}")
        return False

async def handleDialog(dialog):
    global msn
    text = dialog.message
    print(text)
    if text == '驗證碼錯誤，請再重新輸入!!':
        msn = 2
    elif text == '帳號或密碼錯誤，請查明後再登入，若您不確定密碼，請執行忘記密碼，取得新密碼後再登入!':
        msn = 3
    else:
        for fail_type in fail_types:
            if fail_type in text:
                msn = 0
                break
        for success_type in success_types:
            if success_type in text:
                msn = 1
                break
    await dialog.accept()

async def login(account, password): 
    global msn
    browser = await launch(headless=True,
                           dumpio=True,
                           args=[f'--window-size={1920},{1080}',
                               '--disable-features=TranslateUI', 
                               '--no-sandbox'],
                            handleSIGINT=False, #讓pyppeteer可以在thread運行
                            handleSIGTERM=False,
                            handleSIGHUP=False)
    all_pages = await browser.pages()
    loginWebsite = all_pages[0]
    loginWebsite.on('dialog', lambda dialog: asyncio.ensure_future(handleDialog(dialog)))
    await loginWebsite.setViewport({'width': 1920, 'height': 1080})
    async def relogin(browser):
        global msn
        all_pages = await browser.pages()
        loginWebsite = all_pages[0]
        #輸入密碼
        if await waitForSelectorOrTimeout(loginWebsite, '#M_PW'):
            await loginWebsite.type('#M_PW', password)
        #輸入驗證碼
        if await waitForSelectorOrTimeout(loginWebsite, '#importantImg'):
            captcha = await loginWebsite.waitForSelector('#importantImg')
            await captcha.screenshot({'path': r'C:\GitHub\NTOUGrabCourse\code\captcha.png'})
            img = Image.open('code/captcha.png')
            match = False
            while not match:
                ocr = ddddocr.DdddOcr()
                result = ocr.classification(img)
                print(result)
                match = re.match(r'^[a-zA-Z0-9]{4}$', result)
            await loginWebsite.waitForSelector('#M_PW2')
            await loginWebsite.type('#M_PW2', result.upper())
        #點擊登入
        if await waitForSelectorOrTimeout(loginWebsite, '#LGOIN_BTN'):
            loginButton = await loginWebsite.querySelector('#LGOIN_BTN')
            await loginButton.click()
        # await asyncio.sleep(2)
        tmp = msn; msn = -1
        if tmp == -1:
            return browser, "登入成功"
        elif tmp == 2:
            return await relogin(browser)
        elif tmp == 3:
            await asyncio.sleep(1)
            await browser.close()
            return None, "帳密出錯"
        else: 
            await asyncio.sleep(1)
            await browser.close()
            return None, "未知錯誤"
        
    await loginWebsite.goto('https://ais.ntou.edu.tw/Default.aspx') 
    #輸入帳號
    if await waitForSelectorOrTimeout(loginWebsite, '#M_PORTAL_LOGIN_ACNT'):
        await loginWebsite.type('#M_PORTAL_LOGIN_ACNT', account)
    #輸入密碼
    if await waitForSelectorOrTimeout(loginWebsite, '#M_PW'):
        await loginWebsite.type('#M_PW', password)
    #輸入驗證碼
    if await waitForSelectorOrTimeout(loginWebsite, '#importantImg'):
        captcha = await loginWebsite.waitForSelector('#importantImg')
        await captcha.screenshot({'path': r'C:\GitHub\NTOUGrabCourse\code\captcha.png'})
        img = Image.open('code/captcha.png')
        match = False
        while not match:
            ocr = ddddocr.DdddOcr()
            result = ocr.classification(img)
            print(result)
            match = re.match(r'^[a-zA-Z0-9]{4}$', result)
        await loginWebsite.waitForSelector('#M_PW2')
        await loginWebsite.type('#M_PW2', result.upper())

    #點擊登入
    if await waitForSelectorOrTimeout(loginWebsite, '#LGOIN_BTN'):
        loginButton = await loginWebsite.querySelector('#LGOIN_BTN')
        await loginButton.click()

    await asyncio.sleep(2)

    tmp = msn; msn = -1
    if tmp == -1:
        print('browser + ', browser)
        return browser, "登入成功"
    elif tmp == 2:
        return await relogin(browser)
    elif tmp == 3:
        await asyncio.sleep(1)
        await browser.close()
        return None, "帳密出錯"
    else:    
        await asyncio.sleep(1)
        await browser.close()
        return None, "未知錯誤"

async def downloadSchedule(browser, semester):
    all_pages = await browser.pages()
    page = all_pages[0]
    year = semester[:3]; sms = semester[3]  
    menuFrame = None; mainFrame = None
    menuFrame = await findFrameByName(page, 'menuFrame')
    mainFrame = await findFrameByName(page, 'mainFrame')

    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt1'):
        await menuFrame.click('#Menu_TreeViewt1')
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt31'):
        await menuFrame.click('#Menu_TreeViewt31')
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt42'):
        await menuFrame.click('#Menu_TreeViewt42')
    if await waitForSelectorOrTimeout(mainFrame, '#Q_AYEAR'):
        await mainFrame.select('#Q_AYEAR', year)
    if await waitForSelectorOrTimeout(mainFrame, '#Q_SMS'):
        await mainFrame.select('#Q_SMS', sms)
    if await waitForSelectorOrTimeout(mainFrame, '#QUERY_BTN3'):
        await mainFrame.click('#QUERY_BTN3')
    if await waitForSelectorOrTimeout(mainFrame, '#table2'):
        table_content = await mainFrame.evaluate('''() => {
            const table = document.querySelector("#table2");
            const rows = Array.from(table.querySelectorAll("tr"));
            return rows.map(row => {
                const cells = Array.from(row.querySelectorAll("td"));
                return cells.map(cell => cell.innerText);
            });
        }''')
    print(table_content)
    await page.reload()
    return table_content, browser

async def downloadGrade(browser, semester):
    all_pages = await browser.pages()
    page = all_pages[0]
    menuFrame = None; mainFrame = None; viewFrame = None
    menuFrame = await findFrameByName(page, 'menuFrame')
    mainFrame = await findFrameByName(page, 'mainFrame')
    viewFrame = await findFrameByName(page, 'viewFrame')
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt1'):
        await menuFrame.click('#Menu_TreeViewt1')
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt32'):
        await menuFrame.click('#Menu_TreeViewt32')
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt40'):
        await menuFrame.click('#Menu_TreeViewt40')
    if await waitForSelectorOrTimeout(mainFrame, '#Q_AYEARSMS'):
        await mainFrame.evaluate(f"""() => {{
            document.getElementById('Q_AYEARSMS').value = '{semester}';
        }}""")
    if await waitForSelectorOrTimeout(mainFrame, '#QUERY_BTN1'):
        await mainFrame.click('#QUERY_BTN1')
    if await waitForSelectorOrTimeout(viewFrame, '#DataGrid tbody tr'):
        trs = await viewFrame.querySelectorAll('#DataGrid tbody tr')
    data = []
    # 現在trs應該包含所有的<tr>元素
    for i, tr in enumerate(trs):
        if i == 0:
            continue
        tds = await tr.querySelectorAll('td')
        score_data = {
            "課號": await (await tds[1].getProperty('innerText')).jsonValue(),
            "學分": await (await tds[3].getProperty('innerText')).jsonValue(),
            "選別": await (await tds[4].getProperty('innerText')).jsonValue(),
            "課名": await (await tds[5].getProperty('innerText')).jsonValue(),
            "教授": await (await tds[6].getProperty('innerText')).jsonValue(),
            "暫定成績": await (await tds[7].getProperty('innerText')).jsonValue(),
            "最終成績": await (await tds[8].getProperty('innerText')).jsonValue()
        }
        data.append(score_data)
    print("data: ", data)   

    if await waitForSelectorOrTimeout(viewFrame, '#M_AVG_MARK'):
        average_score = await viewFrame.querySelectorEval('#M_AVG_MARK', 'node => node.innerText')
    if await waitForSelectorOrTimeout(viewFrame, '#M_CLASS_RANK'):
        classRank = await viewFrame.querySelectorEval('#M_CLASS_RANK', 'node => node.innerText')
    if await waitForSelectorOrTimeout(viewFrame, '#M_FACULTY_RANK'):
        faculityRank = await viewFrame.querySelectorEval('#M_FACULTY_RANK', 'node => node.innerText')

    data.append(average_score)
    data.append(classRank)
    data.append(faculityRank)

    await page.reload()
    return data, browser

async def userCourses(account):
    courses = []
    async with aiosqlite.connect('userCourse.db') as conn:
        async with conn.execute('SELECT courses FROM userData WHERE account = ?', (account,)) as cursor:
            result = cursor.fetchone()
            if result:
                courses_data = result[0]
                courses = courses_data.split(',')
                print(f"Courses for account '{account}': {courses_data}")
            else:
                print(f"Account '{account}' not found.")

    return courses

async def searchCourse(browser, course):
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
    await menuFrame.waitForSelector('#Menu_TreeViewt40')
    await menuFrame.click('#Menu_TreeViewt40')
    await asyncio.sleep(1.5)
    await mainFrame.waitForSelector('#Q_CH_LESSON')
    await mainFrame.evaluate(f"""() => {{document.getElementById('Q_CH_LESSON').value = '{course}';}}""")
    await mainFrame.waitForSelector('#QUERY_BTN7')
    await mainFrame.click('#QUERY_BTN7')

    await mainFrame.waitForSelector('#DataGrid tbody tr')
    trs = await mainFrame.querySelectorAll('#DataGrid tbody tr')
    data = []
    # 現在trs應該包含所有的<tr>元素
    for i, tr in enumerate(trs):
        if i == 0:
            continue
        tds = await tr.querySelectorAll('td')
        td_innerText = {
            "課號": await (await tds[2].getProperty('innerText')).jsonValue(),
            "課名": await (await tds[3].getProperty('innerText')).jsonValue(),
            "開課單位": await (await tds[4].getProperty('innerText')).jsonValue(),
            "年級班別": await (await tds[5].getProperty('innerText')).jsonValue(),
            "教授": await (await tds[6].getProperty('innerText')).jsonValue(),
            "是否英文": await (await tds[8].getProperty('innerText')).jsonValue(),
            "學分": await (await tds[9].getProperty('innerText')).jsonValue(),
            "選別": await (await tds[10].getProperty('innerText')).jsonValue(),
            "人數上下限": await (await tds[12].getProperty('innerText')).jsonValue(),
            "實習": await (await tds[13].getProperty('innerText')).jsonValue(),
            "期限": await (await tds[16].getProperty('innerText')).jsonValue()
        }
        data.append(td_innerText)
    await page.reload()
    return data, browser

async def snipeCourse(resnipe, browser, course, which=None):
    global msn
    all_pages = await browser.pages()
    page = all_pages[0]
    menuFrame = None; mainFrame = None
    print('here')
    menuFrame = await findFrameByName(page, 'menuFrame')
    mainFrame = await findFrameByName(page, 'mainFrame')

    if not resnipe: 
        selectors_and_frames = [
            (menuFrame, '#Menu_TreeViewt1'),
            (menuFrame, '#Menu_TreeViewt31'),
            (menuFrame, '#Menu_TreeViewt41')]

        for frame, selector in selectors_and_frames:
            if await waitForSelectorOrTimeout(frame, selector):
                await frame.click(selector)

    if await waitForSelectorOrTimeout(mainFrame, '#Q_COSID'):
        await mainFrame.evaluate(f"""() => {{
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
            if which.upper() == whichClass.upper():
                onclick = await tds[0].querySelector('a')
                await onclick.click()

    await asyncio.sleep(2)
    tmp = msn; msn = -1
    if tmp == -1:
        return False, browser, "未知錯誤"
    elif tmp == 0:
        return True, browser, "搶課失敗"
    elif tmp == 1:
        return True, browser, "搶課成功"
    #回傳是否可以resnipe, browser
    
async def main():
    a, b = await login('01157132', 'R125179001')
    print(b)
    a,b,c = await snipeCourse(False , a, 'B57020A6')
    print(c)
    a,b,c = await snipeCourse(a , b, 'B5701M3J', 'B')
    print(c)
    a,b,c = await snipeCourse(a , b, 'B570258M')
    print(c)
    b.close()
    #await snipeCourse(a, 'B5701M3J', 'A')

# asyncio.get_event_loop().run_until_complete(main())

#使用時間逾時, 系統已將您自動登出, 請再重新登入使用本系統!! <== 掛機alert
#系統同時一次僅許可一個帳號登入，你已登入過系統，請先登出原帳號再登入!
#連續輸入３次錯誤密碼，帳號已鎖定，請後續執行忘記密碼，取得新密碼後再登入!
#系統發生錯誤 ... <= F5解決
#本帳號已重複登入，請登出!