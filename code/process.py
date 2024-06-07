import logging
import os
import threading
import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By as by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from PIL import Image
import io
import ddddocr
import re
import time
import asyncio
import uuid

userWeb = {} #user: [webdriver, state] state=>waiting, working, none
tasks = []
result = {} #unique_key: result
fail_types = ('未找到課程','課程不可選','選取失敗','人數已達上限','系統錯誤','年級不可加選！','衝堂不可選！')
success_types = ('本科目設有檢查人數下限。選本課程，在未達下限人數前時無法退選，確定加選?', '成功選取')

def dealAlert(loginWebsite):
    alert = WebDriverWait(loginWebsite, 0.5).until(EC.alert_is_present())
    text = alert.text
    alert.accept()
    if text in fail_types:
        return 0
    elif text in success_types:
        return 1
    elif text == '驗證碼錯誤，請再重新輸入!!':
        return 2
    elif text == '帳號或密碼錯誤，請查明後再登入，若您不確定密碼，請執行忘記密碼，取得新密碼後再登入!':
        return 3
    
def browsereOptions():
    option = webdriver.ChromeOptions()
    option.add_argument('headless') #無介面就被這個設定開啟
    option.add_argument('--start-maximized')
    option.add_argument('--disable-gpu')
    option.add_argument('--window-size=1920,1080')  
    return option

def login(loginWebsite, account, password, key): 
    global result
    global userWeb
    userWeb[account][1] = 'working'
    print(account + "start login")
    def relogin(loginWebsite, key):
        WebDriverWait(loginWebsite, 10).until(EC.presence_of_element_located((by.ID, 'M_PW'))).send_keys(password)
        captchaImage = loginWebsite.find_element(by.ID, 'importantImg') #獲取驗證碼圖片
        img = Image.open(io.BytesIO(captchaImage.screenshot_as_png)) #截圖
        match = False
        while not match:
            ocr = ddddocr.DdddOcr()
            res = ocr.classification(img)
            print(res)
            match = re.match(r'^[a-zA-Z0-9]{4}$', res)
        loginWebsite.find_element(by.ID, 'M_PW2').send_keys(res.upper())
        loginWebsite.find_element(by.ID, 'LGOIN_BTN').click()
        try: #檢查瀏覽器出現的alert
            types = dealAlert(loginWebsite)
            if types == 2:
                return relogin(loginWebsite, key)
            elif types == 3:
                result[key] = "帳密出錯"
            else:    
                result[key] = "未知錯誤"
        except:
            userWeb[account] = [loginWebsite, 'none']
            result[key] = "登入成功"

    loginWebsite.get('https://ais.ntou.edu.tw/Default.aspx') 
    #輸入帳號
    WebDriverWait(loginWebsite, 10).until(EC.presence_of_element_located((by.ID, 'M_PORTAL_LOGIN_ACNT'))).send_keys(account)
    WebDriverWait(loginWebsite, 10).until(EC.presence_of_element_located((by.ID, 'M_PW'))).send_keys(password)
    captchaImage = loginWebsite.find_element(by.ID, 'importantImg') #獲取驗證碼圖片
    img = Image.open(io.BytesIO(captchaImage.screenshot_as_png)) #截圖
    match = False
    res = ''

    while not match:
        ocr = ddddocr.DdddOcr()
        res = ocr.classification(img) 
        print(res)
        match = re.match(r'^[a-zA-Z0-9]{4}$', res)

    loginWebsite.find_element(by.ID, 'M_PW2').send_keys(res.upper())
    loginWebsite.find_element(by.ID, 'LGOIN_BTN').click()
    print(account + 'login done')
    try: #檢查瀏覽器出現的alert
        types = dealAlert(loginWebsite)
        if types == 2:
            relogin(loginWebsite, key)
        elif types == 3:
            result[key] = "帳密出錯"
        else:    
            result[key] = "未知錯誤"
    except:
        userWeb[account] = [loginWebsite, 'none']
        result[key] = "登入成功"
 
async def snipeCourse(browser, course, which=None, resnipe = False): #回傳browser跟 搶課狀態
    #resnipe指的是要不要按旁便那一欄的按鈕，也就是選課系統，線上即時加退選 etc..
    #which是判斷同課號但不同的課程，分AB班 
    global dialogMsnType
    all_pages = await browser.pages()
    page = all_pages[0]
    menuFrame = None; mainFrame = None
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
            
            if which: 
                if which.upper() == whichClass.upper():
                    onclick = await tds[0].querySelector('a')
                    await onclick.click()

    await asyncio.sleep(2)
    tmpDialogMsnType = dialogMsnType; dialogMsnType = -1
    if tmpDialogMsnType == -1 or tmpDialogMsnType == 0:
        return browser, "搶課失敗"
    elif tmpDialogMsnType == 1:
        return browser, "搶課成功"
    elif tmpDialogMsnType == 4:
        return browser, "人滿"
    #回傳是否可以resnipe, browser
    
def monitor_variable(account, function, *args):
    while True:
        if userWeb[account][1] == 'none':
            print(account + "變數已經變為 none")
            if function == "downloadScedule":
                userWeb[account][1] = 'working'
                thread = threading.Thread(target = downloadScedule, args=(userWeb[account][0], args[0]))
                thread.start()
                break

async def check_complete(key):
    global result
    while True:
        if key in result:
            print(f'{key}完成了 reault = {result[key]}')
            break
        await asyncio.sleep(0.5)

async def do_task():
    copied_task = []
    global tasks
    while len(tasks) > 0:
        print('idol')
        if copied_task == []:
            copied_task = tasks.copy()
            tasks = []
            print('find tasks task len = '+ str(len(copied_task)))
            for task in copied_task:
                if task[2] == 'login':
                    keys.add(task[3])
                    loginWebsite = webdriver.Chrome(options= browsereOptions())
                    thread = threading.Thread(target=login, args=(loginWebsite, task[0], task[1], task[-1]), daemon=True)
                    thread.start()
                elif task[2] == 'downloadScedule':
                    if userWeb[task[0]][1] != 'none':
                        thread = threading.Thread(target=monitor_variable, args=(task[0], task[2], task[3]), daemon=True)
                        thread.start()
                    else:
                        thread = threading.Thread(target=login, args=(loginWebsite, task[0], task[1]), daemon=True)
                        thread.start()
        for key in keys.copy():
            if key in result:
                print('finish one task')
                keys.remove(key)
        if len(keys) == 0:
            print('copied tasks clear')
            copied_task = []
            break
        await asyncio.sleep(0.5)

#req = [account, password, request, data, key]
async def push_and_return_task(req):
    global userWeb
    global tasks
    global result
    unique_key = str(uuid.uuid4())
    req.append(unique_key)
    if len(tasks) == 0: #activate threads
        print('activate do_task thread')
        doing_thread = threading.Thread(target= lambda: asyncio.run(do_task()))
        doing_thread.start()
    if req[2] == 'login':
        userWeb[req[0]] = [None, 'waiting']
        tasks.append(req)
    else:
        if req[0] not in userWeb:
            pass #尚未登入
        tasks.append(req)
        userWeb[req[0]][1] = 'waiting'
    thread = threading.Thread(target= lambda: asyncio.run(check_complete(unique_key)))
    thread.start()
    while unique_key not in result:
        await asyncio.sleep(0.2)
    return result.pop(unique_key)
    
async def main():
    print('send request 1')
    await push_and_return_task(['01157132', 'a78874884', 'login'])
    await asyncio.sleep(2)
    print('send request 2')
    await push_and_return_task(['downloadScedule', '1111'])
    await asyncio.sleep(3)
    print('send request 3')
    await push_and_return_task([])

if __name__ == '__main__':
    asyncio.run(main())

#TODO
#開一個新的DB存放已經搶到的課號