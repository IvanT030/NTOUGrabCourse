import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By as by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from PIL import Image
import numpy as np
import io
import ddddocr
import re

option = webdriver.ChromeOptions()
#option.add_argument('headless') #無介面就被這個設定開啟
option.add_argument('--start-maximized')
option.add_argument('--disable-gpu')

fail_types = ('未找到課程','課程不可選','選取失敗','人數已達上限','系統錯誤','年級不可加選！','衝堂不可選！')
success_types = ('本科目設有檢查人數下限。選本課程，在未達下限人數前時無法退選，確定加選?', '成功選取')

def dealAlert():
    alert = WebDriverWait(loginWebsite, 1).until(EC.alert_is_present())
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

def login(loginWebsite):
    with open('account_data.json', encoding='UTF-8') as f: #不用utf-8會出事
        data = json.load(f) #獲取登入的帳號資料

    loginWebsite.get('https://ais.ntou.edu.tw/Default.aspx') 
    #輸入帳號
    WebDriverWait(loginWebsite, 10).until(EC.presence_of_element_located((by.ID, 'M_PORTAL_LOGIN_ACNT'))).send_keys(data['account'])
    loginWebsite.find_element(by.ID, 'M_PW').send_keys(data['password']) #輸入密碼
    captchaImage = loginWebsite.find_element(by.ID, 'importantImg') #獲取驗證碼圖片
    img = Image.open(io.BytesIO(captchaImage.screenshot_as_png)) #截圖

    pattern = r'^[a-zA-Z0-9]{4}$'
    match = False
    result = ''

    while not match:
        ocr = ddddocr.DdddOcr()
        result = ocr.classification(img)
        print(result)
        match = re.match(pattern, result)
        
    loginWebsite.find_element(by.ID, 'M_PW2').send_keys(result.upper())
    loginWebsite.find_element(by.ID, 'LGOIN_BTN').click()

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
        types = dealAlert()
        if types == 0:
            print("選課程出了問題")

    myWebsite.switch_to.default_content()


if __name__ == '__main__':
    loginWebsite = webdriver.Chrome(options= option)
    #------login
    retryTime = 0
    while retryTime < 5:
        login(loginWebsite)
        try: #檢查瀏覽器出現的alert
            types = dealAlert()
            if types == 2:
                #print(types)
                retryTime += 1
            elif types == 3:
                raise Exception("帳密出錯")     
        except:
            #print("no alert")
            break
    if retryTime == 5:
        raise Exception("帳密出錯")
    
    Courses = []
    grabCourse(loginWebsite, Courses)
#使用時間逾時, 系統已將您自動登出, 請再重新登入使用本系統!! <== 掛機alert