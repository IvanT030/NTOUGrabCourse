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
 
def downloadScedule(user ,myWebsite, semester, key):
    global result
    global userWeb
    userWeb[user][1] = 'working'
    year = semester[:3]; sms = semester[3]  
    menuFrame = WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.NAME, 'menuFrame')))
    myWebsite.switch_to.frame(menuFrame)
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt1'))).click()
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt30'))).click()
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'Menu_TreeViewt41'))).click()
    myWebsite.switch_to.default_content()
    mainFrame = WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.NAME, 'mainFrame')))
    myWebsite.switch_to.frame(mainFrame)
    yearSelector = Select(WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.ID, 'Q_AYEAR'))))
    yearSelector.select_by_value(f'{year}')
    smsSelector = Select(WebDriverWait(myWebsite, 10).until(EC.presence_of_element_located((by.ID, 'Q_SMS'))))
    smsSelector.select_by_value(f'{sms}')
    WebDriverWait(myWebsite, 10).until(EC.element_to_be_clickable((by.ID, 'QUERY_BTN3'))).click()
    time.sleep(0.5)
    lessons = WebDriverWait(myWebsite, 10).until(EC.presence_of_all_elements_located((by.XPATH, '//*[@id="table2"]/tbody/tr')))
    scedule = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
    for i, rowlessons in enumerate(lessons, start=-1):
        if i == -1:
            continue
        tds = rowlessons.find_elements(by.TAG_NAME, 'td')
        for td in tds:
            if td.get_attribute('innerText') == '\xa0':
                scedule[i].append('None')
            else:
                scedule[i].append(td.get_attribute('innerText'))
    myWebsite.switch_to.default_content()
    myWebsite.refresh()
    result[key] = scedule
    userWeb[user] = [myWebsite, 'none']

def monitor_variable(account, function, *args): #之後要加key
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
    keys = set()
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

#####
#    while thread.is_alive():
#        await asyncio.sleep(1)    
#    print(f'{req[0]} is dead')
#####
    
async def main():
    print('send request 1')
    await push_and_return_task(['01157132', 'a78874884', 'login'])
    #await asyncio.sleep(2)
    #print('send request 2')
    #await push_and_return_task(['01157132', 'a78874884', 'downloadScedule', '1111'])
    #await asyncio.sleep(3)
    print('send request 3')
    await push_and_return_task(['01157116','Pwken531368','login'])

if __name__ == '__main__':
    asyncio.run(main())