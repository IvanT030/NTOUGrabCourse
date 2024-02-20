#python 3.11
import asyncio
from pyppeteer import launch
from pyppeteer import dialog
from PIL import Image
import io
import ddddocr
import re
import time

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
        return loginWebsite, "登入成功"
    elif tmp == 2:
        return await relogin(loginWebsite)
    elif tmp == 3:
        browser.close()
        return None, "帳密出錯"
    else:    
        browser.close()
        return None, "未知錯誤"

async def downloadScedule(page, semester):
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
    await asyncio.sleep(10)

    table_content = await mainFrame.evaluate('''() => {
        const table = document.querySelector("#table2");
        const rows = Array.from(table.querySelectorAll("tr"));
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll("td"));
            return cells.map(cell => cell.innerText);
        });
    }''')
    #print(table_content)
    await page.refresh()
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

def downloadGrade(myWebsite, semester):
    menuFrame = WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.NAME, 'menuFrame')))
    myWebsite.switch_to.frame(menuFrame)
    #教務系統
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt1'))).click()
    #成績系統
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt31'))).click()
    #查詢各式成績#
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt39'))).click()
    myWebsite.switch_to.default_content()
    mainFrame = WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.NAME, 'mainFrame')))
    myWebsite.switch_to.frame(mainFrame)
    #學年期
    semester_input = WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.ID, 'Q_AYEARSMS')))
    semester_input.clear()
    semester_input.send_keys(semester)
    #查詢button
    myWebsite.find_element(by.ID, 'QUERY_BTN1').click()
    #成績表
    myWebsite.switch_to.default_content()
    viewFrame = WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.NAME, 'viewFrame')))
    myWebsite.switch_to.frame(viewFrame)
    trs = WebDriverWait(myWebsite, 20).until(
        EC.presence_of_all_elements_located((by.XPATH, '//*[@id="DataGrid"]/tbody/tr'))
    )
    data = []
    # 現在gradeTable應該包含所有的<tr>元素
    for i, tr in enumerate(trs):
        if i == 0 :
            continue
        tds = tr.find_elements(by.TAG_NAME, 'td')
        score_data = {
            "課號": tds[1].get_attribute('innerText'),
            "學分": tds[3].get_attribute('innerText'),
            "選別": tds[4].get_attribute('innerText'),
            "課名": tds[5].get_attribute('innerText'),
            "教授": tds[6].get_attribute('innerText'),
            "暫定成績": tds[7].get_attribute('innerText'),
            "最終成績": tds[8].get_attribute('innerText')
        }
        data.append(score_data)

    average_score = myWebsite.find_element(by.ID, 'M_AVG_MARK').get_attribute('innerText')
    classRank = myWebsite.find_element(by.ID, 'M_CLASS_RANK').get_attribute('innerText')
    faculityRank = myWebsite.find_element(by.ID, 'M_FACULTY_RANK').get_attribute('innerText')

    data.append(average_score)
    data.append(classRank)
    data.append(faculityRank)

    myWebsite.switch_to.default_content()
    myWebsite.refresh()
    return data, myWebsite

async def main():
    a, b = await login('01157132','R125179001')
    await downloadScedule(a, '1112')

asyncio.get_event_loop().run_until_complete(main())

#使用時間逾時, 系統已將您自動登出, 請再重新登入使用本系統!! <== 掛機alert
#系統同時一次僅許可一個帳號登入，你已登入過系統，請先登出原帳號再登入!
#連續輸入３次錯誤密碼，帳號已鎖定，請後續執行忘記密碼，取得新密碼後再登入!
#系統發生錯誤 ... <= F5解決