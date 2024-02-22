#python 3.11
import asyncio
from pyppeteer import launch
from PIL import Image
import ddddocr
import re
import sqlite3
import aiosqlite

fail_types = ('未找到課程','課程不可選','選取失敗','人數已達上限','系統錯誤','年級不可加選！','衝堂不可選！')
success_types = ('本科目設有檢查人數下限。選本課程，在未達下限人數前時無法退選，確定加選?', '成功選取')
msn = -1

async def handleDialog(dialog):
    global msn
    text = dialog.message
    print(text)
    if text in fail_types:
        msn = 0      
    elif text in success_types:
        msn = 1
    elif text == '驗證碼錯誤，請再重新輸入!!':
        msn = 2
    elif text == '帳號或密碼錯誤，請查明後再登入，若您不確定密碼，請執行忘記密碼，取得新密碼後再登入!':
        msn = 3
    await dialog.dismiss()
    
#改成browser回傳，其他函式改browser接收
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
    async def relogin(loginWebsite):
        global msn
        await loginWebsite.type('#M_PW', password)
        captcha = await loginWebsite.waitForSelector('#importantImg')
        await captcha.screenshot({'path': r'C:\GitHub\NTOUGrabCourse\code\captcha.png'})
        img = Image.open('code/captcha.png')
        match = False
        while not match:
            ocr = ddddocr.DdddOcr()
            result = ocr.classification(img)
            print(result)
            match = re.match(r'^[a-zA-Z0-9]{4}$', result)
        await loginWebsite.type('#M_PW2', result.upper())
        loginButton = await loginWebsite.querySelector('#LGOIN_BTN')
        await loginButton.click()
        await asyncio.sleep(1)
        tmp = msn; msn = -1
        if tmp == -1:
            return loginWebsite, "登入成功"
        elif tmp == 2:
            return await relogin(loginWebsite)
        elif tmp == 3:
            return None, "帳密出錯"
        else:    
            return None, "未知錯誤"
        
    await loginWebsite.goto('https://ais.ntou.edu.tw/Default.aspx') 
    #輸入帳號
    await loginWebsite.type('#M_PORTAL_LOGIN_ACNT', account)
    await loginWebsite.type('#M_PW', password)
    captcha = await loginWebsite.waitForSelector('#importantImg')
    await captcha.screenshot({'path': r'C:\GitHub\NTOUGrabCourse\code\captcha.png'})
    img = Image.open('code/captcha.png')
   
    pattern = r'^[a-zA-Z0-9]{4}$'
    match = False
    result = ''

    while not match:
        ocr = ddddocr.DdddOcr()
        result = ocr.classification(img) 
        print(result)
        match = re.match(pattern, result)

    await loginWebsite.type('#M_PW2', result.upper())
    loginButton = await loginWebsite.querySelector('#LGOIN_BTN')
    await loginButton.click()
    await asyncio.sleep(1)
    tmp = msn; msn = -1
    if tmp == -1:
        return browser, "登入成功"
    elif tmp == 2:
        return await relogin(loginWebsite)
    elif tmp == 3:
        browser.close()
        return None, "帳密出錯"
    else:    
        browser.close()
        return None, "未知錯誤"

async def downloadScedule(browser, semester):
    all_pages = await browser.pages()
    page = all_pages[0]
    year = semester[:3]; sms = semester[3]  
    await asyncio.sleep(1.5)
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
    await menuFrame.waitForSelector('#Menu_TreeViewt42')
    await menuFrame.click('#Menu_TreeViewt42')
    await mainFrame.waitForSelector('#Q_AYEAR')
    await mainFrame.select('#Q_AYEAR', year)
    await mainFrame.waitForSelector('#Q_SMS')
    await mainFrame.select('#Q_SMS', sms)
    await mainFrame.waitForSelector('#QUERY_BTN3')
    await mainFrame.click('#QUERY_BTN3')
    await asyncio.sleep(3)

    table_content = await mainFrame.evaluate('''() => {
        const table = document.querySelector("#table2");
        const rows = Array.from(table.querySelectorAll("tr"));
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll("td"));
            return cells.map(cell => cell.innerText);
        });
    }''')
    #print(table_content)
    await page.reload()
    return table_content, browser

async def downloadGrade(browser, semester):
    all_pages = await browser.pages()
    page = all_pages[0]
    await asyncio.sleep(3)
    menuFrame = None; mainFrame = None; viewFrame = None
    await page.waitForSelector('#menuIFrame')
    await page.waitForSelector('#mainIFrame')
    await page.waitForSelector('#viewIFrame')
    frames = page.frames
    for frame in frames:
        print(frame.name)
        if frame.name == 'menuFrame':
            menuFrame = frame
        elif frame.name == 'mainFrame':
            mainFrame = frame 
        elif frame.name == 'viewFrame':
            viewFrame = frame
    await menuFrame.waitForSelector('#Menu_TreeViewt1')
    await menuFrame.click('#Menu_TreeViewt1')
    await menuFrame.waitForSelector('#Menu_TreeViewt32')
    await menuFrame.click('#Menu_TreeViewt32')
    await menuFrame.waitForSelector('#Menu_TreeViewt40')
    await menuFrame.click('#Menu_TreeViewt40')

    await asyncio.sleep(4)
    await mainFrame.evaluate(f"""() => {{
        document.getElementById('Q_AYEARSMS').value = '{semester}';
    }}""")
    await mainFrame.waitForSelector('#QUERY_BTN1')
    await mainFrame.click('#QUERY_BTN1')
    await asyncio.sleep(2)

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

    average_score = await viewFrame.querySelectorEval('#M_AVG_MARK', 'node => node.innerText')
    classRank = await viewFrame.querySelectorEval('#M_CLASS_RANK', 'node => node.innerText')
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
    print(data)
    await page.reload()
    return data, page

userWeb = {}
async def main():
    a, _ = await login('01157132', 'R125179001')
    await downloadGrade(a, '1112')
    await a.close()
    

asyncio.get_event_loop().run_until_complete(main())

#使用時間逾時, 系統已將您自動登出, 請再重新登入使用本系統!! <== 掛機alert
#系統同時一次僅許可一個帳號登入，你已登入過系統，請先登出原帳號再登入!
#連續輸入３次錯誤密碼，帳號已鎖定，請後續執行忘記密碼，取得新密碼後再登入!
#系統發生錯誤 ... <= F5解決