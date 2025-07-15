import tkinter as tk
from tkinter import *
from tkinter import messagebox
import json
from tkinter.ttk import Combobox
import jsonpath
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

import requests

def loginButton():
    uid = entryAccount.get()
    password = entryPass.get()
    url = "http://127.0.0.1:5000/login"
    params = {
        "uid": uid,
        "password": password
    }
    response = requests.get(url, params)
    print(response.text)
    respCode = jsonpath.jsonpath(json.loads(response.text), "$..respCode")
    print(respCode)
    respCode = int(respCode[0])
    if respCode == -1:
        s = messagebox.showerror("登录错误", "账号或密码错误")
    else:
        s = messagebox.showinfo("登录成功", "服务器连接成功")
        root.destroy()
        openAppPage(respCode)

def openAppPage(statecode):
    def usualFunc(url, params): #初始检验身份有没有过期，过期就返回-1
        label.config(text="正在请求服务器数据...")
        root.update()
        response = requests.get(url, params)
        label.config(text="请求数据成功！")
        respCode = jsonpath.jsonpath(json.loads(response.text), "$..respCode")
        if respCode != False:
            label.config(text="登录身份信息失效,请重新登录!")
            return -1
        else:
            return response

    def drawLowAndHigh(response, a1):
        maxValue = jsonpath.jsonpath(json.loads(response.text), "$..maxValue")[0]
        maxValueIndex = jsonpath.jsonpath(json.loads(response.text), "$..maxValueIndex")[0]
        minValue = jsonpath.jsonpath(json.loads(response.text), "$..minValue")[0]
        minValueIndex = jsonpath.jsonpath(json.loads(response.text), "$..minValueIndex")[0]

        downValueHigh = jsonpath.jsonpath(json.loads(response.text), "$..downValueHigh")[0]
        downValueLow = jsonpath.jsonpath(json.loads(response.text), "$..downValueLow")[0]
        downValueHighIndex = jsonpath.jsonpath(json.loads(response.text), "$..downValueHighIndex")[0]
        downValueLowIndex = jsonpath.jsonpath(json.loads(response.text), "$..downValueLowIndex")[0]
        downDif = jsonpath.jsonpath(json.loads(response.text), "$..downDif")[0]
        upValueHigh = jsonpath.jsonpath(json.loads(response.text), "$..upValueHigh")[0]
        upValueLow = jsonpath.jsonpath(json.loads(response.text), "$..upValueLow")[0]
        upValueHighIndex = jsonpath.jsonpath(json.loads(response.text), "$..upValueHighIndex")[0]
        upValueLowIndex = jsonpath.jsonpath(json.loads(response.text), "$..upValueLowIndex")[0]
        upDif = jsonpath.jsonpath(json.loads(response.text), "$..upDif")[0]

        a1.plot(downValueHighIndex, downValueHigh, marker='o', markersize=8, label='Point 1', color='blue')
        a1.plot(downValueLowIndex, downValueLow, marker='o', markersize=8, label='Point 1', color='blue')
        a1.plot([downValueHighIndex, downValueLowIndex], [downValueHigh, downValueLow], linestyle='-', linewidth=2,
                color='green', label='Line')
        a1.plot(upValueHighIndex, upValueHigh, marker='o', markersize=8, label='Point 1', color='blue')
        a1.plot(upValueLowIndex, upValueLow, marker='o', markersize=8, label='Point 1', color='blue')
        a1.plot([upValueHighIndex, upValueLowIndex], [upValueHigh, upValueLow], linestyle='-', linewidth=2,
                color='red', label='Line')

        a1.annotate(f'Max: {maxValue}', xy=(maxValueIndex, maxValue), arrowprops=dict(facecolor='red'))
        a1.annotate(f'Min: {minValue}', xy=(minValueIndex, minValue), arrowprops=dict(facecolor='blue'))
        # 显示落差
        arrow_x = (downValueHighIndex + downValueLowIndex) / 2
        arrow_y = (downValueHigh + downValueLow) / 2
        a1.annotate(f'downDiff: {downDif}', xy=(arrow_x, arrow_y), fontsize=8, ha='center')

        arrow_x = (upValueHighIndex + upValueLowIndex) / 2
        arrow_y = (upValueHigh + upValueLow) / 2
        a1.annotate(f'upDiff: {upDif}', xy=(arrow_x, arrow_y), fontsize=8, ha='center')
    def quit():
        url = baseUrl + "/quit"
        label.config(text="正在退出...")
        requests.get(url, params)
        root.destroy()
    def showSales():
        url = baseUrl + "/sales"
        thisParams = {
            "statecode": statecode,
            "timeL": codeEnetyL.get(),
            "timeR": codeEnetyR.get()
        }
        response = usualFunc(url, thisParams)
        if response == -1:
            return

        sales = jsonpath.jsonpath(json.loads(response.text), "$..sales")
        x = range(len(sales))

        f = Figure(figsize=(5, 4), dpi=100)  # 开一个画布对象
        a1 = f.add_subplot(111)
        a1.plot(x, sales)
        drawLowAndHigh(response, a1)

        canvas = FigureCanvasTkAgg(f, master=root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.25, rely=0)

    def showPool():
        url = baseUrl + "/poolmoney"
        thisParams = {
            "statecode": statecode,
            "timeL": codeEnetyL.get(),
            "timeR": codeEnetyR.get()
        }
        response = usualFunc(url, thisParams)
        if response == -1:
            return

        poolmoney = jsonpath.jsonpath(json.loads(response.text), "$..poolmoney")
        x = range(len(poolmoney))
        f = Figure(figsize=(5, 4), dpi=100)  # 开一个画布对象
        a1 = f.add_subplot(111)
        a1.plot(x, poolmoney)
        drawLowAndHigh(response, a1)

        canvas = FigureCanvasTkAgg(f, master=root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.25, rely=0)

    def showBet():
        url = baseUrl + "/bet"
        combSel = comb.current() + 1  # 获取下标
        if combSel == 0:
            s = messagebox.showerror("查询失败","请选择你要查询的奖")
            return
        thisParams = {
            "statecode":statecode,
            "timeL": codeEnetyL.get(),
            "timeR": codeEnetyR.get(),
            "betnum":combSel
        }

        response = usualFunc(url, thisParams)
        if response == -1:
            return

        type = jsonpath.jsonpath(json.loads(response.text), "$..type" + str(combSel))
        x = range(len(type))
        f = Figure(figsize=(5, 4), dpi=100)  # 开一个画布对象
        a1 = f.add_subplot(111)
        a1.plot(x, type)
        drawLowAndHigh(response, a1)

        canvas = FigureCanvasTkAgg(f, master=root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.25, rely=0)

    def showSignalPri():
        url = baseUrl + "/signalpri"
        combSel = comb.current() + 1  # 获取下标
        if combSel == 0 or combSel > 2:
            s = messagebox.showerror("查询失败", "只有一等奖和二等奖有查询意义")
            return
        thisParams = {
            "statecode": statecode,
            "betnum": combSel,
            "timeL": codeEnetyL.get(),
            "timeR": codeEnetyR.get()
        }


        response = usualFunc(url, thisParams)
        if response == -1:
            return
        type = jsonpath.jsonpath(json.loads(response.text), "$..typemoney" + str(combSel))
        x = range(len(type))
        f = Figure(figsize=(5, 4), dpi=100)  # 开一个画布对象
        a1 = f.add_subplot(111)
        a1.plot(x, type)
        drawLowAndHigh(response, a1)

        canvas = FigureCanvasTkAgg(f, master=root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.25, rely=0)


    def showHis():
        url = baseUrl + "/hisball"
        thisParams = {
            "statecode":statecode,
            "timeL":codeEnetyL.get(),
            "timeR":codeEnetyR.get()
        }
        response = usualFunc(url, thisParams)
        if response == -1:
            return

        redFreVal = list(jsonpath.jsonpath(json.loads(response.text), "$..Red")[0].values())
        blueFreVal = list(jsonpath.jsonpath(json.loads(response.text), "$..Blue")[0].values())
        redFreKey = []
        blueFreKey = []

        #原本的文字下标太长了直接用数字代替
        for i in range(33):
            redFreKey.append(str(i + 1))
        for i in range(16):
            blueFreKey.append(str(i + 1))

        # 红色球柱状图
        f = Figure(figsize=(5, 4), dpi=100)  # 开一个画布对象
        a1 = f.add_subplot(211)
        a1.bar(redFreKey, redFreVal, color="red")
        a1.set_xticks(range(1, 34))
        a1.set_xticklabels(redFreKey, fontsize=5)

        # 蓝色球柱状图
        a2 = f.add_subplot(212)
        a2.bar(blueFreKey, blueFreVal, color="blue")
        a2.set_xticks(range(1, 17))
        a2.set_xticklabels(blueFreKey, fontsize=5)

        canvas = FigureCanvasTkAgg(f, master=root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.25)

    def showOneBall():
        url = baseUrl + "/oneball"
        code = codeEnety.get()
        if code == '':
            s = messagebox.showerror("错误", "期号不能为空")
            return

        thisparams = {
            "statecode":statecode,
            "code":int(code),
        }
        response = usualFunc(url, thisparams)
        if response == -1:
            return

        if  len(json.loads(response.text)) == 0:
            label.config(text="请输入2013年后的有效期号！")
            return

        ballNum = {
            1: '①', 2: '②', 3: '③', 4: '④', 5: '⑤',
            6: '⑥', 7: '⑦', 8: '⑧', 9: '⑨', 10: '⑩',
            11: '⑪', 12: '⑫', 13: '⑬', 14: '⑭', 15: '⑮',
            16: '⑯', 17: '⑰', 18: '⑱', 19: '⑲', 20: '⑳',
            21: '㉑', 22: '㉒', 23: '㉓', 24: '㉔', 25: '㉕',
            26: '㉖', 27: '㉗', 28: '㉘', 29: '㉙', 30: '㉚',
            31: '㉛', 32: '㉜', 33: '㉝',
        }
        redList = []
        temp = json.loads(response.text)
        redList.append(ballNum[int(jsonpath.jsonpath(temp, "$..red_1")[0])])
        redList.append(ballNum[int(jsonpath.jsonpath(temp, "$..red_2")[0])])
        redList.append(ballNum[int(jsonpath.jsonpath(temp, "$..red_3")[0])])
        redList.append(ballNum[int(jsonpath.jsonpath(temp, "$..red_4")[0])])
        redList.append(ballNum[int(jsonpath.jsonpath(temp, "$..red_5")[0])])
        redList.append(ballNum[int(jsonpath.jsonpath(temp, "$..red_6")[0])])
        redres = "".join(redList)
        blueres = ballNum[int(jsonpath.jsonpath(temp, "$..blue")[0])]

        labelRedBallNum.config(text=redres)
        labelBlueBallNum.config(text=blueres)


    def haveLuckBall():
        url = baseUrl + "/luckball"
        thisParams = {
            "statecode": statecode,
            "timeL": codeEnetyL.get(),
            "timeR": codeEnetyR.get()
        }
        response = usualFunc(url, thisParams)
        if response == -1:
            return

        redBall = jsonpath.jsonpath(json.loads(response.text), "$..red")[0]
        blueBall = jsonpath.jsonpath(json.loads(response.text), "$..blue")[0]

        ballNum = {
            1: '①', 2: '②', 3: '③', 4: '④', 5: '⑤',
            6: '⑥', 7: '⑦', 8: '⑧', 9: '⑨', 10: '⑩',
            11: '⑪', 12: '⑫', 13: '⑬', 14: '⑭', 15: '⑮',
            16: '⑯', 17: '⑰', 18: '⑱', 19: '⑲', 20: '⑳',
            21: '㉑', 22: '㉒', 23: '㉓', 24: '㉔', 25: '㉕',
            26: '㉖', 27: '㉗', 28: '㉘', 29: '㉙', 30: '㉚',
            31: '㉛', 32: '㉜', 33: '㉝',
        }

        showTemp = []
        for i in redBall:
            showTemp.append(ballNum[i])

        showTemp = "".join(showTemp)
        labelRedBallNum.config(text=showTemp)
        labelBlueBallNum.config(text=ballNum[blueBall[0]])

    def arimaSales():
        url = baseUrl + "/arima"
        thisParams = {
            "statecode": statecode,
            "timeL": codeEnetyL.get(),
            "timeR": codeEnetyR.get(),
            "foredays":foreDays.get()
        }
        response = usualFunc(url, thisParams)
        if response == -1:
            return

        salesData = list(jsonpath.jsonpath(json.loads(response.text), "$..sales")[0])
        forcast = list(jsonpath.jsonpath(json.loads(response.text), "$..forcast")[0])
        lower = list(jsonpath.jsonpath(json.loads(response.text), "$..lower")[0])
        uper = list(jsonpath.jsonpath(json.loads(response.text), "$..uper")[0])
        forcast.insert(0, salesData[-1])

        f = Figure(figsize=(5, 4), dpi=100)  # 开一个画布对象
        a1 = f.add_subplot(111)
        a1.plot(range(len(salesData)), salesData, label="Real")
        a1.plot(range(len(salesData) - 1,len(forcast) + len(salesData) - 1), forcast, color="red", label="Fore")
        a1.fill_between(range(len(salesData) - 1, len(salesData) + len(lower) - 1), lower, uper, color="pink", alpha=0.5)
        a1.legend()

        canvas = FigureCanvasTkAgg(f, master=root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.25, rely=0)

        return 1

    def spem():
        combSel = comb.current() + 1  # 获取下标
        if combSel == 0:
            s = messagebox.showerror("查询失败", "请输入需要查询的奖")
            return
        url = baseUrl + "/spem"
        thisParams = {
            "statecode": statecode,
            "timeL": codeEnetyL.get(),
            "timeR": codeEnetyR.get(),
            "type": combSel
        }
        response = usualFunc(url, thisParams)
        if response == -1:
            return

        sales = jsonpath.jsonpath(json.loads(response.text), "$..sales")
        bets = jsonpath.jsonpath(json.loads(response.text), "$..bets")
        spem = jsonpath.jsonpath(json.loads(response.text), "$..spem")
        spemLabel.config(text=spem)

        f = Figure(figsize=(5, 4), dpi=100)  # 开一个画布对象
        a1 = f.add_subplot(111)
        sc = a1.scatter(sales, bets, c=bets, cmap='coolwarm', s=50)
        plt.colorbar(sc)

        canvas = FigureCanvasTkAgg(f, master=root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.25, rely=0)

        return 1

    #开新页面
    baseUrl = "http://127.0.0.1:5000"
    params = {
        "statecode": statecode
    }
    root = tk.Tk()
    root.geometry("1000x600")
    root.title("彩票分析")
    root.configure(bg="#000080")

    labelBack = Label(root, bg="#FFD700")
    labelBack.place(relx=0.2, height=440, width=600)

    labelBasic1 = Label(root, bg="#FFD700",text="数据呈现", font=("黑体", 18))
    labelBasic1.place(relx=0.05, rely=0.02)

    labelBasic2 = Label(root, bg="#FFD700", text="数据分析", font=("黑体", 18))
    labelBasic2.place(relx=0.85, rely=0.02)

    labelBasic3 = Label(root, bg="#000080", text="Version 1.0", font=("Times New Roman", 14), fg="#FFD700")
    labelBasic3.place(relx=0.85, rely=0.95)

    label = Label(root, text="--服务消息--",font=("黑体", 20, "bold"))
    label.place(relx=0.2, rely=0.74)

    showHisFreBtn = Button(root, text="历史色球频率",command=showHis,font=("黑体", 15, "bold"), bg = "#C0C0C0")
    showHisFreBtn.place(relx=0.04, rely=0.1, width=130, height=40)

    showPoolmoneyBtn = Button(root, text="历史奖池数据",command=showPool,font=("黑体", 15, "bold"), bg = "#C0C0C0")
    showPoolmoneyBtn.place(relx=0.04, rely=0.2, width=130, height=40)

    showSalesBtn = Button(root, text="历史销售额",command=showSales,font=("黑体", 15, "bold"), bg = "#C0C0C0")
    showSalesBtn.place(relx=0.04, rely=0.3, width=130, height=40)

    showBetBtn = Button(root, text="得奖注数",command=showBet,font=("黑体", 15, "bold"), bg = "#C0C0C0")
    showBetBtn.place(relx=0.04, rely=0.5, width=130, height=40)

    showSignlPri = Button(root, text="单注奖金",command=showSignalPri,font=("黑体", 15, "bold"), bg = "#C0C0C0")
    showSignlPri.place(relx=0.04, rely=0.6, width=130, height=40)

    comb = Combobox(root, values=["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖"],font=("黑体", 15, "bold"))
    comb.place(relx=0.04, rely=0.7, width=130, height=40)

    codeEnetyL = Entry(root, font=("黑体", 15, "bold"))
    codeEnetyL.place(relx=0.005, rely=0.4, width=90, height=40)
    codeEnetyL.insert(0, "2023")

    codeEnetyR = Entry(root, font=("黑体", 15, "bold"))
    codeEnetyR.place(relx=0.105, rely=0.4, width=90, height=40)
    codeEnetyR.insert(0, "2023")

    showOneBall = Button(root, text="单期号码", command=showOneBall, font=("黑体", 15, "bold"), bg="#C0C0C0")
    showOneBall.place(relx=0.09, rely=0.87, width=90, height=40)

    codeEnety = Entry(root,font=("黑体", 15, "bold"))
    codeEnety.place(relx=0.185, rely=0.87, width=90, height=40)
    codeEnety.insert(0, "000000")

    labelRedBallNum = Label(root, text="①②③㊳㊴⑩",bg="grey", fg="red", font=("黑体", 35, "bold"))
    labelRedBallNum.place(relx=0.3, rely=0.85, width="320", height="60")

    labelBlueBallNum = Label(root, text="⑩",bg="grey", fg="Blue", font=("黑体", 35, "bold"))
    labelBlueBallNum.place(relx=0.61, rely=0.85, width="70", height="60")
#------------------------------------------------------------------------------------------------------#

    luckBtn = Button(root, text="轮盘赌号码", command=haveLuckBall, font=("黑体", 15, "bold"), bg="#C0C0C0")
    luckBtn.place(relx=0.835, rely=0.1, width=130, height=40)

    arimaBtn = Button(root, text="SARIMA预测销售", command=arimaSales, font=("黑体", 12, "bold"), bg="#C0C0C0")
    arimaBtn.place(relx=0.835, rely=0.2, width=130, height=40)

    foreDays = Entry(root, font=("黑体", 15, "bold"))
    foreDays.place(relx=0.835, rely=0.3, width=130, height=40)
    foreDays.insert(0, "12")

    spemBtn = Button(root, text="注数与销售额相关性", command=spem, font=("黑体", 9, "bold"), bg="#C0C0C0")
    spemBtn.place(relx=0.835, rely=0.4, width=130, height=40)

    spemLabel = Label(root, bg="lightgrey", text="斯皮尔曼相关系数", font=("黑体", 12))
    spemLabel.place(relx=0.81, rely=0.5, width=180, height=40)

    quitBtn = Button(root, text="退出登录",command=quit)
    quitBtn.place(relx=0.74, rely=0.74)

    root.mainloop()
def openRegisterPage():
    def registButton():
        uid = entryAccount.get()
        password = entryPass.get()
        rePassword = reEntryPass.get()
        url = "http://127.0.0.1:5000/regist"
        params = {
            "uid": uid,
            "password": password
        }

        if(password != rePassword):
            s = messagebox.showerror("注册失败", "两次密码输入不一致")
        else:
            response = requests.get(url, params)
            respCode = jsonpath.jsonpath(json.loads(response.text), "$..respCode")
            respCode = int(respCode[0])
            if respCode == -1:
                s = messagebox.showerror("注册失败", "账号已存在")
            else:
                s = messagebox.showinfo("注册成功", "恭喜!账号注册成功")
                register_window.destroy()

    # 创建注册页面窗口
    register_window = tk.Toplevel(root)
    register_window.geometry("500x400")
    register_window.configure(bg="lightblue")
    register_window.attributes("-topmost", True)
    register_window.title("注册界面")

    labelOpen = Label(register_window, text="账户注册", fg="blue", bg="lightblue", font=("楷体", 40,"bold"))
    labelOpen.place(relx=0.28, rely=0.1)

    entryAccount = Entry(register_window, font=("楷体", 20), bd=3)
    entryAccount.place(relx=0.25, rely=0.3, height=40, width=250)
    labelAccount = Label(register_window, font=("楷体", 16), bg="lightblue", text="账号：", bd=3)
    labelAccount.place(relx=0.1, rely=0.31)

    entryPass = Entry(register_window, font=("楷体", 20), show="*", bd=3)
    entryPass.place(relx=0.25, rely=0.45, height=40, width=250)
    labelPass = Label(register_window, font=("楷体", 16), bg="lightblue", text="密码：", bd=3)
    labelPass.place(relx=0.1, rely=0.46)

    reEntryPass = Entry(register_window, font=("楷体", 20), show="*", bd=3)
    reEntryPass.place(relx=0.25, rely=0.60, height=40, width=250)
    relabelPass = Label(register_window, font=("楷体", 16), bg="lightblue", text="确认密码：", bd=3)
    relabelPass.place(relx=0.015, rely=0.61)

    loginButton = Button(register_window, text="提交注册信息", font=("楷体", 20), bg="blue", fg="white", bd=3, command=registButton)
    loginButton.place(relx=0.25, rely=0.76, height=40, width=250)

    nameLabel = Label(register_window, text="design-By-21211357314唐登", fg="blue", bg="lightblue", font=("楷体", 12))
    nameLabel.place(relx=0.55, rely=0.9)


if __name__ == '__main__':
    root = Tk()
    root.geometry("500x400")
    root.title("登录界面")
    root.configure(bg="lightblue")

    labelOpen = Label(root, text="账户登录", fg="blue", bg="lightblue", font=("楷体", 40, "bold"))
    labelOpen.place(relx=0.28, rely=0.1)

    entryAccount = Entry(root, font=("楷体", 20), bd=3)
    entryAccount.place(relx=0.25, rely=0.35, height=40, width=250)
    labelAccount = Label(root, font=("楷体", 16), bg="lightblue", text="账号：", bd=3)
    labelAccount.place(relx=0.1, rely=0.36)

    entryPass = Entry(root, font=("楷体", 20), show="*", bd=3)
    entryPass.place(relx=0.25, rely=0.5, height=40, width=250)
    labelPass = Label(root, font=("楷体", 16), bg="lightblue", text="密码：", bd=3)
    labelPass.place(relx=0.1, rely=0.51)

    loginButton = Button(root, text="登录", font=("楷体", 20), bg="blue", fg="white", bd=3, command=loginButton)
    loginButton.place(relx=0.15, rely=0.68, height=40, width=120)

    regButton = Button(root, text="注册", font=("楷体", 20), bg="blue", fg="white", bd=3, command=openRegisterPage)
    regButton.place(relx=0.6, rely=0.68, height=40, width=120)

    nameLabel = Label(root, text="design-By-21211357314唐登", fg="blue", bg="lightblue", font=("楷体", 12))
    nameLabel.place(relx=0.55, rely=0.9)

    root.mainloop()



