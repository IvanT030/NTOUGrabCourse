#python 3.11
import asyncio
from pyppeteer import launch
from pyppeteer import dialog
# from pyppeteer.errors import TimeoutErro
from PIL import Image
import io
import ddddocr
import re
import time

fail_types = ('未找到課程','課程不可選','選取失敗','人數已達上限','系統錯誤','年級不可加選！','衝堂不可選！')
success_types = ('本科目設有檢查人數下限。選本課程，在未達下限人數前時無法退選，確定加選?', '成功選取')
msn = -1

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
    if text in fail_types:
        msn = 0      
    elif text in success_types:
        msn = 1
    elif text == '驗證碼錯誤，請再重新輸入!!':
        msn = 2
    elif text == '帳號或密碼錯誤，請查明後再登入，若您不確定密碼，請執行忘記密碼，取得新密碼後再登入!':
        msn = 3
    await dialog.dismiss()

async def login(account, password): 
    global msn
    browser = await launch(headless=False,
                           dumpio=True,
                           args=[f'--window-size={1920},{1080}'])
    loginWebsite = await browser.newPage()
    loginWebsite.on('dialog', lambda dialog: asyncio.ensure_future(handleDialog(dialog)))
    await loginWebsite.setViewport({'width': 1920, 'height': 1080})
    async def relogin(loginWebsite):
        global msn
        await loginWebsite.waitForSelector('#M_PW')
        await loginWebsite.type('#M_PW', password)
        await loginWebsite.waitForSelector('#importantImg')
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
        await loginWebsite.waitForSelector('#LGOIN_BTN')
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
    await loginWebsite.waitForSelector('#M_PORTAL_LOGIN_ACNT')
    await loginWebsite.type('#M_PORTAL_LOGIN_ACNT', account)
    await loginWebsite.waitForSelector('#M_PW')
    await loginWebsite.type('#M_PW', password)
    await loginWebsite.waitForSelector('#importantImg')
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

    await loginWebsite.waitForSelector('#M_PW2')
    await loginWebsite.type('#M_PW2', result.upper())
    await loginWebsite.waitForSelector('#LGOIN_BTN')
    loginButton = await loginWebsite.querySelector('#LGOIN_BTN')
    await loginButton.click()
    await asyncio.sleep(1)
    tmp = msn; msn = -1
    if tmp == -1:
        return loginWebsite, "登入成功"
    elif tmp == 2:
        return await relogin(loginWebsite)
    elif tmp == 3:
        browser.close()
        return None, "帳密出錯"
    else:    
        browser.close()
        return None, "未知錯誤"
     

async def downloadSchedule(page, semester):
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
    return table_content, page

def grabCourse(myWebsite, courseNumbers): #couseNumber多個課號 先當list用
    #菜單按鈕
    #myWebsite.find_element(by.XPATH, '//*[@id="header"]/div[1]/div[1]').click()
    #換框架
    myWebsite.switch_to.frame(myWebsite.find_element(by.NAME, 'menuFrame'))
    #教務系統
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt1'))).click()
    #選課系統按鈕
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt30'))).click()
    #線上即時加退選按鈕
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt40'))).click()
    #以下尚未測試 尋找課號input
    course_input = WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.ID, 'Q_COSID')))
    submit_btn = myWebsite.find_element(by.ID, 'QUERY_COSID_BTN')
    
    for course in courseNumbers:
        course_input.clear()
        course_input.send_keys(course)
        submit_btn.click()
        types = dealAlert(myWebsite)
        if types == 0:
            print("選課程出了問題")

    myWebsite.switch_to.default_content()
    myWebsite.refresh()


async def downloadGrade(page, semester):
    await asyncio.sleep(2)
    menuFrame = None; mainFrame = None; viewFrame = None
    frames = page.frames
    for frame in frames:
        if frame.name == 'menuFrame':
            menuFrame = frame
        elif frame.name == 'mainFrame':
            mainFrame = frame 
        elif frame.name == 'viewFrame':
            viewFrame = frame
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt1'):
        await menuFrame.click('#Menu_TreeViewt1')
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt32'):
        await menuFrame.click('#Menu_TreeViewt32')
    if await waitForSelectorOrTimeout(menuFrame, '#Menu_TreeViewt40'):
        await menuFrame.click('#Menu_TreeViewt40')
    # await menuFrame.waitForSelector('#Menu_TreeViewt1')
    # await menuFrame.click('#Menu_TreeViewt1')
    # await menuFrame.waitForSelector('#Menu_TreeViewt32')
    # await menuFrame.click('#Menu_TreeViewt32')
    # await menuFrame.waitForSelector('#Menu_TreeViewt40')
    # await menuFrame.click('#Menu_TreeViewt40')

    print('click')  
    print("menuFrame: ", menuFrame)
    # await asyncio.sleep(4)
    # if await waitForSelectorOrTimeout(menuFrame, '#pageFrame'):
    # frames = page.frames
    # for frame in frames:
    #     if frame.name == 'menuFrame':
    #         menuFrame = frame
    #     elif frame.name == 'mainFrame':
    #         mainFrame = frame 
    #     elif frame.name == 'viewFrame':
    #         viewFrame = frame
    #     print(frame.name)
    if await waitForSelectorOrTimeout(mainFrame, '#Q_AYEARSMS'):
        # await menuFrame.click('#MainIFrame')
    # await menuFrame.click('#Menu_TreeViewt40')
        await mainFrame.evaluate(f"""() => {{
            document.getElementById('Q_AYEARSMS').value = '{semester}';
        }}""")
    print("sfsdsff")
    if await waitForSelectorOrTimeout(mainFrame, '#QUERY_BTN1'):
        await mainFrame.click('#QUERY_BTN1')
    # print('click')
    # await mainFrame.waitForSelector('#QUERY_BTN1')
    # await mainFrame.click('#QUERY_BTN1')
    # await asyncio.sleep(2)
    # frames = page.frames
    # for frame in frames:
    #     if frame.name == 'menuFrame':
    #         menuFrame = frame
    #     elif frame.name == 'mainFrame':
    #         mainFrame = frame 
    #     elif frame.name == 'viewFrame':
    #         viewFrame = frame
    #     print(frame.name)
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
    # classRank = await viewFrame.querySelectorEval('#M_CLASS_RANK', 'node => node.innerText')
    # faculityRank = await viewFrame.querySelectorEval('#M_FACULTY_RANK', 'node => node.innerText')

    data.append(average_score)
    data.append(classRank)
    data.append(faculityRank)
    print("data: ", data)
    await page.reload()
    return data, page

async def main():
    a, b = await login('01157132','R125179001')
    await downloadGrade(a, '1112')

asyncio.get_event_loop().run_until_complete(main())

#使用時間逾時, 系統已將您自動登出, 請再重新登入使用本系統!! <== 掛機alert
#系統同時一次僅許可一個帳號登入，你已登入過系統，請先登出原帳號再登入!
#連續輸入３次錯誤密碼，帳號已鎖定，請後續執行忘記密碼，取得新密碼後再登入!
#系統發生錯誤 ... <= F5解決