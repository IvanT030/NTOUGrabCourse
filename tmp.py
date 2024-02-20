import time
def get_s(req):
    return "haha" + str(req)

def user1():
    time.sleep(3)
    print(get_s(1))

def user2():
    time.sleep(1)
    print(get_s(2))
# def main() -> None:
user1()
user2()

# # if __name__ == "tmp.py":    
# #     main()   
# task: use1 , user2

def get_score():
    retData = await sendTask(cmd)

######你的部分
aysnc def sendTask(cmd):
    result = await waitResult(id)
    return result

async def waitResult(id):
    