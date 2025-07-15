import random
import threading
import statsmodels.api as sm
import pandas as pd
from flask import Flask, request
import requests
import json
import datetime
import pymysql
import jsonpath
import numpy as np
from scipy.stats import spearmanr


def find_open_parenthesis(input_string):
    for index, char in enumerate(input_string):
        if char == '（':
            return index
    return -1


# sql插入语句提高复用率
def FuliSqlInsert(curse, sql_connection, i):
    khindex = find_open_parenthesis(i[16])

    # 处理加奖的情况
    if (khindex != -1):
        print(i)
        i = list(i)
        i[16] = i[16][0: khindex]
        i = tuple(i)

    test_query = "INSERT INTO fulicaipiao(code, red_1, red_2, red_3, red_4, red_5, red_6, blue, sales, poolmoney, type1, type2, type3, type4, type5, type6, typemoney1, typemoney2, typemoney3, typemoney4, typemoney5, typemoney6) " \
                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    try:
        curse.execute(test_query, i)
        sql_connection.commit()
    except Exception as e:
        sql_connection.rollback()


# 一次爬取接口
def CrawFuLiOneProcess(No):
    if No == -1: No = 999999999
    # 连接数据库
    sql_connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='stu123',
        database='fuli'
    )
    curse = sql_connection.cursor()

    # 请求接口获取数据
    url = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
    params = {
        "name": "ssq",
        "pageNo": "1",
        "pageSize": No,
        "systemType": "PC"
    }

    response = requests.get(url, params=params)
    json_response = json.loads(response.text)

    # 初步提取所需的信息变成可以存储的元组形式
    red_ball = jsonpath.jsonpath(json_response, '$..red')
    blue_ball = jsonpath.jsonpath(json_response, '$..blue')
    code = jsonpath.jsonpath(json_response, '$..code')
    sales = jsonpath.jsonpath(json_response, '$..sales')
    poolmoney = jsonpath.jsonpath(json_response, '$..poolmoney')
    typemoney = jsonpath.jsonpath(json_response, '$..typemoney')
    typenum = jsonpath.jsonpath(json_response, '$..typenum')

    typenum = [typenum[i: i + 6] for i in range(0, len(typenum), 7)]
    typemoney = [typemoney[i: i + 6] for i in range(0, len(typemoney), 7)]

    red_ball = [item.split(',') for item in red_ball]
    fin_date = [tuple(x) for x in zip(code, red_ball, blue_ball, sales, poolmoney, typenum, typemoney)]
    fin_date = [(item[0], *item[1], item[2], item[3], item[4], *item[5], *item[6]) for item in fin_date]

    for i in fin_date:
        FuliSqlInsert(curse, sql_connection, i)

    curse.close()
    sql_connection.close()


# 把爬取过程综合起来
def CrawFuli():
    print("初始化数据库。。。")
    CrawFuLiOneProcess(-1)  # 初始化一下
    print("初始化完成进入每日检测。。。")
    while True:
        time = datetime.date.today()
        time = time.strftime("%A")
        if time == "Tuesday" or time == "Thursday" or time == "Sunday":
            time = datetime.datetime.now()
            hour = time.strftime("%H")
            minute = time.strftime("%M")
            if int(hour) >= 22:
                CrawFuLiOneProcess(2)
            elif int(hour) >= 21 and int(minute) >= 20:
                CrawFuLiOneProcess(2)


def SelectSqlForJson(query, values=None): #严格来说返回的并不是真正的json格式，每组数据前面应当加个组号再组一次字典，但是没有什么意义也不影响后续读取使用就没加
    sql_connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='stu123',
        database='fuli'
    )
    curse = sql_connection.cursor()
    curse.execute(query, values)
    results = curse.fetchall()
    data_list = []
    column_names = [desc[0] for desc in curse.description]

    for result in results:
        data = dict(zip(column_names, result))
        data_list.append(data)

    curse.close()
    sql_connection.close()

    return (json.dumps(data_list, indent=4))


def noRespSql(query, values):
    sql_connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='stu123',
        database='fuli'
    )
    curse = sql_connection.cursor()

    try:
        curse.execute(query, values)
        sql_connection.commit()
    except:
        sql_connection.rollback()

    curse.close()
    sql_connection.close()


def acqMin():
    time = datetime.datetime.now()
    return int(time.year * 12 * 12 * 24 * 60 + time.month * 12 * 24 * 60 + time.day*24*60 + time.hour*60 + time.minute)

def checkTime(statecode):
    query = "select acttime from onlinestate where statecode = %s"
    selCodeRes = SelectSqlForJson(query, statecode)
    if(len(selCodeRes) == 2):return False
    nowTime = acqMin()
    time = int(jsonpath.jsonpath(json.loads(selCodeRes), "$..acttime")[0]) #这里很坑导出来是列表必须取完第一项再Int
    if(nowTime - time >= 800):return False
    else:
        query = "update onlinestate set acttime = %s where statecode = %s"
        noRespSql(query, (nowTime, statecode))
        return True

def killState(statecode):
    query = "delete from onlinestate where statecode = %s"
    noRespSql(query, statecode)

def FetchFreq(TimeL, TimeR):
    query = "SELECT * from fulicaipiao where code >= %s and code <= %s"
    selRes = SelectSqlForJson(query, (TimeL, TimeR))
    selRes = json.loads(selRes)

    red_1 = jsonpath.jsonpath(selRes, "$..red_1")  # ..是递归遍历
    red_2 = jsonpath.jsonpath(selRes, "$..red_2")
    red_3 = jsonpath.jsonpath(selRes, "$..red_3")
    red_4 = jsonpath.jsonpath(selRes, "$..red_4")
    red_5 = jsonpath.jsonpath(selRes, "$..red_5")
    red_6 = jsonpath.jsonpath(selRes, "$..red_6")
    blue = jsonpath.jsonpath(selRes, "$..blue")

    freqListRed = [0] * 33
    freqListBlue = [0] * 16
    for i in range(len(red_1)):      #记录球的出现频率
        freqListRed[red_1[i] - 1] += 1
        freqListRed[red_2[i] - 1] += 1
        freqListRed[red_3[i] - 1] += 1
        freqListRed[red_4[i] - 1] += 1
        freqListRed[red_5[i] - 1] += 1
        freqListRed[red_6[i] - 1] += 1
        freqListBlue[blue[i] - 1] += 1

    colNameR = []
    colNameB = []
    for i in range(33):
        colNameR.append("redNum" + str(i + 1))
    for i in range(16):
        colNameB.append("blueNum" + str(i + 1))

    respList = []
    respList.append(dict(zip(colNameR, freqListRed)))  # zip包成二元组， dict把二元组包成字典
    respList.append(dict(zip(colNameB, freqListBlue)))

    keys = ["Red", "Blue"]
    respList = dict(zip(keys, respList))
    return (json.dumps(respList, indent=4))

def CalRiseDown(data):
    maxValue = max(data)
    maxValueIndex = data.index(maxValue)
    minValue = min(data)
    minValueIndex = data.index(minValue)

    downValueHigh = data[0]
    downValueLow = data[0]
    downValueHighIndex = 0
    downValueLowIndex = 0
    downDif = 0

    upValueHigh = data[0]
    upValueLow = data[0]
    upValueHighIndex = 0
    upValueLowIndex = 0
    upDif = 0
    tempHigh  = 0
    tempLow = 0

    for i in range(len(data)):
        if data[i] > data[tempHigh]:
            tempHigh = i

        if data[tempHigh] - data[i] > downDif:
            downDif = data[tempHigh] - data[i]
            downValueLow = data[i]
            downValueLowIndex = i
            downValueHigh = data[tempHigh]
            downValueHighIndex = tempHigh

        if data[i] < data[tempLow]:
            tempLow = i

        if data[i] - data[tempLow] > upDif:
            upDif = data[i] - data[tempLow]
            upValueHigh = data[i]
            upValueHighIndex = i
            upValueLow = data[tempLow]
            upValueLowIndex = tempLow

    response = [maxValue, maxValueIndex, minValue, minValueIndex, upValueHigh, upValueLow, upDif, upValueHighIndex, upValueLowIndex, downValueHigh, downValueLow, downDif, downValueHighIndex, downValueLow, downValueLowIndex]
    keys = ["maxValue", "maxValueIndex", "minValue", "minValueIndex", "upValueHigh", "upValueLow", "upDif", "upValueHighIndex", "upValueLowIndex", "downValueHigh", "downValueLow", "downDif", "downValueHighIndex", "downValueLow","downValueLowIndex"]
    response = dict(zip(keys, response))
    return response

def FetchPoolmoney(timeL, timeR):
    query = "select poolmoney from fulicaipiao where code >= %s and code <= %s"
    selRes = SelectSqlForJson(query, (timeL, timeR))
    response = CalRiseDown(jsonpath.jsonpath(json.loads(selRes), "$..poolmoney"))
    selRes = list(json.loads(selRes))
    selRes.append(response)
    selRes = json.dumps(selRes, indent=4)
    return selRes

def FetchSales(timeL, timeR):
    query = "select sales from fulicaipiao where code >= %s and code <= %s"
    selSales = SelectSqlForJson(query, (timeL, timeR))

    response = CalRiseDown(jsonpath.jsonpath(json.loads(selSales), "$..sales"))
    selSales = list(json.loads(selSales))
    selSales.append(response)
    selSales = json.dumps(selSales, indent=4)
    return selSales

def FetchBet(betnum, timeL, timeR):
    query = "select type1,type2,type3,type4,type5,type6 from fulicaipiao where code >= %s and code <= %s"
    selBet = SelectSqlForJson(query, (timeL,timeR))

    response = CalRiseDown(jsonpath.jsonpath(json.loads(selBet), "$..type" + str(betnum)))
    selBet = list(json.loads(selBet))
    selBet.append(response)
    selBet = json.dumps(selBet, indent=4)
    return selBet

def FetchSignalpri(betnum, timeL, timeR):
    query = "select typemoney1,typemoney2 from fulicaipiao where code >= %s and code <=%s"
    selBet = SelectSqlForJson(query, (timeL, timeR))

    response = CalRiseDown(jsonpath.jsonpath(json.loads(selBet), "$..typemoney" + str(betnum)))
    selBet = list(json.loads(selBet))
    selBet.append(response)
    selBet = json.dumps(selBet, indent=4)
    return selBet

def FetchOneBall(code):
    if int(code) != 0:
        query = "select red_1,red_2,red_3,red_4,red_5,red_6,blue from fulicaipiao where code = %s"
        selOneBall = SelectSqlForJson(query, code)
    else:
        query = "SELECT red_1, red_2, red_3, red_4, red_5, red_6, blue FROM fulicaipiao ORDER BY code DESC LIMIT 1"
        selOneBall = SelectSqlForJson(query)

    return selOneBall


def FetchLuckBall(timeL, timeR):
    ans = FetchFreq(timeL, timeR)
    redBall = list(jsonpath.jsonpath(json.loads(ans), "$..Red")[0].values())
    blueBall = list(jsonpath.jsonpath(json.loads(ans), "$..Blue")[0].values())

    redBall = [1/i for i in redBall]
    blueBall = [i/i for i in blueBall]
    redBall = np.array(redBall)
    blueBall = np.array(blueBall)

    redSum = redBall.sum()
    blueSum = blueBall.sum()

    redBall = redBall / redSum
    blueBall = blueBall / blueSum

    funnyRed = []
    funnyBlue = []

    i = 0
    while i < 6:
        temp = random.random()
        tempSum = 0
        for j in range(33):
            tempSum += redBall[j]
            if tempSum >= temp:
                try:
                    funnyRed.index(j + 1)
                except ValueError:
                    i += 1
                    funnyRed.append(j + 1)
                    break
                break

    temp = random.random()
    tempSum = 0
    for j in range(16):
        tempSum += blueBall[j]
        if tempSum >= temp:
            funnyBlue.append(j + 1)
            break

    return json.dumps(dict(zip(["red", "blue"],[funnyRed, funnyBlue])))


def FetchArima(timeL, timeR, foredays):
    query = "select sales from fulicaipiao where code >= %s and code <=%s"
    selSales = SelectSqlForJson(query, (timeL, timeR))
    selSales = jsonpath.jsonpath(json.loads(selSales), "$..sales")

    index = range(len(selSales))
    ts = pd.Series(selSales, index=index)

    sarima_model = sm.tsa.SARIMAX(ts, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    sarima_results = sarima_model.fit()

    # 预测未来值
    forecast_steps = foredays  # 预测未来
    forecast = sarima_results.get_forecast(steps=forecast_steps)

    # 获取预测值和置信区间
    forecast_mean = forecast.predicted_mean
    forecast_conf_int = forecast.conf_int()

    forecast = list(forecast_mean)
    lower = list(forecast_conf_int.iloc[:, 0])
    uper = list(forecast_conf_int.iloc[:, 1])

    responce = json.dumps(dict(zip(["sales", "forcast", "lower", "uper"], [selSales, forecast, lower, uper])))
    return responce


def FetchSpem(timeL, timeR, type):
    sales = FetchSales(timeL, timeR)
    bets = FetchBet(1, timeL, timeR)

    typeString = "$..type" + str(type)
    sales = jsonpath.jsonpath(json.loads(sales), "$..sales")
    bets = jsonpath.jsonpath(json.loads(bets), typeString)

    x = np.array(sales)
    y = np.array(bets)

    # 使用spearmanr函数计算斯皮尔曼相关系数
    spem, _ = spearmanr(x, y)

    return json.dumps(dict(zip(["sales", "bets", "spem"], [sales, bets, spem])))


def test():
    app = Flask(__name__)

    @app.route('/hisball')
    def FuncFetchFreq():
        statecode = int(request.values.get("statecode"))
        timeL = int(request.values.get("timeL")) * 1000
        timeR = (int(request.values.get("timeR")) + 1) * 1000
        if(checkTime(statecode)):
            return FetchFreq(timeL, timeR)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)#请求错误

    @app.route('/poolmoney')
    def FuncFetchPoolmoney():
        statecode = int(request.values.get("statecode"))
        if(checkTime(statecode)):
            timeL = int(request.values.get("timeL")) * 1000
            timeR = (int(request.values.get("timeR")) + 1) * 1000
            return FetchPoolmoney(timeL, timeR)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  #请求错误

    @app.route('/sales')
    def FuncFetchSales():
        statecode = int(request.values.get("statecode"))
        timeL = int(request.values.get("timeL")) * 1000
        timeR = (int(request.values.get("timeR")) + 1) * 1000
        if (checkTime(statecode)):
            return FetchSales(timeL, timeR)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  # 请求错误

    @app.route('/bet')
    def FuncFetchBet():
        statecode = int(request.values.get("statecode"))
        betnum = int(request.values.get("betnum"))
        timeL = int(request.values.get("timeL")) * 1000
        timeR = (int(request.values.get("timeR")) + 1) * 1000
        if (checkTime(statecode)):
            return FetchBet(betnum, timeL, timeR)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  # 请求错误

    @app.route('/signalpri')
    def FuncFetchSignalPri():
        statecode = int(request.values.get("statecode"))
        betnum = int(request.values.get("betnum"))
        timeL = int(request.values.get("timeL")) * 1000
        timeR = (int(request.values.get("timeR")) + 1) * 1000
        if (checkTime(statecode)):
            return FetchSignalpri(betnum, timeL, timeR)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  # 请求错误

    @app.route('/oneball')
    def FuncFetchOneBall():
        statecode = int(request.values.get("statecode"))
        code = int(request.values.get("code"))
        if (checkTime(statecode)):
            return FetchOneBall(code)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  # 请求错误

    @app.route('/arima')
    def FuncArima():
        statecode = int(request.values.get("statecode"))
        foredays = int(request.values.get("foredays"))
        timeL = int(request.values.get("timeL")) * 1000
        timeR = (int(request.values.get("timeR")) + 1) * 1000
        if (checkTime(statecode)):
            return FetchArima(timeL, timeR, foredays)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  # 请求错误


    @app.route('/luckball')
    def FuncLuckBall():
        statecode = int(request.values.get("statecode"))
        timeL = int(request.values.get("timeL")) * 1000
        timeR = (int(request.values.get("timeR")) + 1) * 1000
        if (checkTime(statecode)):
            return FetchLuckBall(timeL, timeR)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  # 请求错误

    @app.route('/spem')
    def FunctionSpem():
        statecode = int(request.values.get("statecode"))
        timeL = int(request.values.get("timeL")) * 1000
        timeR = (int(request.values.get("timeR")) + 1) * 1000
        type = request.values.get("type")
        if (checkTime(statecode)):
            return FetchSpem(timeL, timeR, type)
        else:
            killState(statecode)
            return json.dumps(dict(zip(["respCode"], [-1])), indent=4)  # 请求错误


    @app.route('/login')
    def FuncLogin():
        uid = request.values.get("uid")
        password = request.values.get("password")

        query = "select * from client where uid = %s"
        selIdRes = SelectSqlForJson(query, uid)
        if len(selIdRes) == 2:
            respCode = -1# 不知道为什么打包回来的空文件大小是2 那么就设置为2了
        else:
            checkPass = jsonpath.jsonpath(json.loads(selIdRes), "$..password")
            checkPass = checkPass[0] #这里要注意，checkPass和password都是字符串类型的
            if checkPass == password:
                query = "select * from onlinestate where uid = %s"  #去在线数据库看看有没有，有就直接返回并且刷新时间没就重新生成插入数据
                time = acqMin()
                respCode = abs(uid.__hash__() + random.randint(0, 999999999))

                if(len(SelectSqlForJson(query, uid)) == 2):
                    query = "insert into onlinestate(uid, statecode, acttime) values (%s, %s, %s)"
                    noRespSql(query, (uid, respCode, time))
                else:
                    query = "update onlinestate set acttime = %s where uid = %s"
                    noRespSql(query, (time, uid))
                    query = "update onlinestate set statecode = %s where uid = %s"
                    noRespSql(query, (respCode, uid))

            else:
                respCode = -1

        respJson = json.dumps(dict(zip(["respCode"], [respCode])), indent=4)
        return respJson

    @app.route('/regist')
    def FuncRegist():
        uid = request.values.get("uid")
        password = request.values.get("password")

        query = "select * from client where uid = %s" #检查这个账号有没有注册过注册过就不能注册
        selIdRes = SelectSqlForJson(query, uid)
        if len(selIdRes) != 2:
            respCode = -1  # 不知道为什么打包回来的空文件大小是2 那么就设置为2了
        else:
            respCode = 1
            query = "insert into client(uid, password) values (%s, %s)"
            noRespSql(query, (uid, password,))

        respJson = json.dumps(dict(zip(["respCode"], [respCode])), indent=4)
        return respJson


    @app.route('/quit')
    def FuncQuit():
        statecode = request.values.get("statecode")
        query = "delete from onlinestate where statecode = %s"
        noRespSql(query, statecode)
        respJson = json.dumps(dict(zip(["respCode"], [1])), indent=4)
        return respJson
    app.run(host="0.0.0.0",port=5000)



if __name__ == '__main__':
    thread_1 = threading.Thread(target=CrawFuli).start()
    thread_2 = threading.Thread(target=test).start()
