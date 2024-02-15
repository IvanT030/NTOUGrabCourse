import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By as by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import json
from PIL import Image
import numpy as np
import io
import ddddocr
import re
import time


fail_types = ('未找到課程','課程不可選','選取失敗','人數已達上限','系統錯誤','年級不可加選！','衝堂不可選！')
success_types = ('本科目設有檢查人數下限。選本課程，在未達下限人數前時無法退選，確定加選?', '成功選取')

def browsereOptions():
    option = webdriver.ChromeOptions()
    #option.add_argument('headless') #無介面就被這個設定開啟
    option.add_argument('--start-maximized')
    option.add_argument('--disable-gpu')
    option.add_argument('--window-size=1920,1080')  
    return option

def dealAlert(loginWebsite):
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

def login(loginWebsite, account, password): 
    def relogin(loginWebsite):
        WebDriverWait(loginWebsite, 10).until(EC.presence_of_element_located((by.ID, 'M_PW'))).send_keys(password)
        captchaImage = loginWebsite.find_element(by.ID, 'importantImg') #獲取驗證碼圖片
        img = Image.open(io.BytesIO(captchaImage.screenshot_as_png)) #截圖
        pattern = r'^[a-zA-Z0-9]{4}$'
        match = False
        while not match:
            ocr = ddddocr.DdddOcr()
            result = ocr.classification(img)
            print(result)
            match = re.match(pattern, result)
        loginWebsite.find_element(by.ID, 'M_PW2').send_keys(result.upper())
        loginWebsite.find_element(by.ID, 'LGOIN_BTN').click()
        try: #檢查瀏覽器出現的alert
            types = dealAlert(loginWebsite)
            if types == 2:
                relogin(loginWebsite)
            elif types == 3:
                return None, "帳密出錯"
            else:    
                return None, "未知錯誤"
        except:
            pass

    loginWebsite.get('https://ais.ntou.edu.tw/Default.aspx') 
    #輸入帳號
    WebDriverWait(loginWebsite, 10).until(EC.presence_of_element_located((by.ID, 'M_PORTAL_LOGIN_ACNT'))).send_keys(account)
    WebDriverWait(loginWebsite, 10).until(EC.presence_of_element_located((by.ID, 'M_PW'))).send_keys(password)
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

    try: #檢查瀏覽器出現的alert
        types = dealAlert(loginWebsite)
        if types == 2:
            return relogin(loginWebsite)
        elif types == 3:
            return None, "帳密出錯"
        else:    
            return None, "未知錯誤"
    except:
        return loginWebsite, "登入成功"

def downloadSchedule(myWebsite, semester):
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
    return scedule ,myWebsite

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

#if __name__ == '__main__':
    #loginWebsite = webdriver.Chrome(options= browsereOptions())
    #a, b = login(loginWebsite, '01157132', 'a78874884')
    #print(b)
    #downloadSchedule(a,'1111')
    #--pick course
    #Courses = []
    #grabCourse(loginWebsite, Courses)


#使用時間逾時, 系統已將您自動登出, 請再重新登入使用本系統!! <== 掛機alert
#系統同時一次僅許可一個帳號登入，你已登入過系統，請先登出原帳號再登入!