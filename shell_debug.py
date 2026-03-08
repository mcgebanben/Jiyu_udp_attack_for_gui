"""
shell_debug.py - 支持打包环境的命令行交互组件
在PyInstaller打包后，input()和print()仍能正常工作
"""

import customtkinter as ctk
import sys
import threading
import queue
import os
from datetime import datetime
from time import sleep
import hashlib as Hash #哈希加密
import Jiyu_udp_attack as Jiyu

class CommandLineWidget(ctk.CTkFrame):
    def __init__(self, master, width=800, height=450, **kwargs):
        # 传递尺寸参数给父类CTkFrame
        super().__init__(master, width=width, height=height, **kwargs)
        
        # 检测是否在打包环境中运行
        self.is_frozen = getattr(sys, 'frozen', False)
        
        # 保存尺寸信息
        self.frame_width = width
        self.frame_height = height
        global window_width
        global window_height
        window_width = width
        window_height = height
        
        # 配置网格权重
        self.grid_rowconfigure(0, weight=1)  # 输出区占大部分空间
        self.grid_rowconfigure(1, weight=0)  # 输入区固定高度
        self.grid_columnconfigure(0, weight=1)
        
        # 命令历史
        self.command_history = []
        self.history_index = -1
        
        # 输入队列和线程安全机制
        self.input_queue = queue.Queue()
        self.waiting_for_input = False
        self.current_input_prompt = ""
        
        # 输出队列
        self.output_queue = queue.Queue()
        self.is_running = True
        self.process_queue_id = None
        
        # 创建界面
        self._create_widgets()
        
        # 设置输入输出重定向（关键修复）
        self._setup_io_redirection()
        
        # 启动输出队列处理器
        self.process_queue_id = self.after(100, self._process_output_queue)
        
    def _create_widgets(self):
        """创建界面组件"""
        # 1. 输出文本框 (上半部分)
        self.output_text = ctk.CTkTextbox(
            self,
            font=("Microsoft YaHei UI", 16),
            wrap="word"
        )
        self.output_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self._show_welcome()
        
        # 2. 输入框 (下半部分)
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="输入命令，按回车执行",
            font=("Microsoft YaHei UI", 16)
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.input_entry.bind("<Return>", self._handle_input)
        self.input_entry.bind("<Up>", self._history_up)
        self.input_entry.bind("<Down>", self._history_down)
        
        # 3. 清空按钮
        clear_btn = ctk.CTkButton(
            input_frame,
            text="清空",
            width=60,
            font=("Microsoft YaHei UI", 16),
            command=self._clear_output
        )
        clear_btn.grid(row=0, column=1, padx=(0, 5), pady=5)
        
        # 关键：强制框架不根据内容调整大小
        self.grid_propagate(False)
        
    def _show_welcome(self):
        """显示欢迎信息"""
        size_info = f"尺寸: {window_width} x {window_height}"
        
        # 显示打包状态
        status = "打包环境" if self.is_frozen else "开发环境"
        
        welcome = f"{'='*50}\n命令行就绪 ({status})\n{size_info}\n{'='*50}\n本软件支持输入 单个ip: \n    如:10.0.254.14\nip范围: \n    如:10.0.254.14-18\nip地址请找开发者获取\n点击一个按钮后,只能先完成当前输入才能点击其他按钮\n想要更多帮助，请输入help\n>>> "
        self.output_text.insert("1.0", welcome)
        self.output_text.configure(state="disabled")
    
    def _setup_io_redirection(self):
        """设置输入输出重定向（修复打包版本）"""
        # 保存原始标准输出（用于备份）
        self.original_stdout = sys.stdout
        
        # 1. 设置输出重定向（捕获print）
        class OutputRedirector:
            def __init__(self, widget):
                self.widget = widget
                
            def write(self, text):
                # 将输出添加到队列中
                if text and self.widget.is_running:
                    self.widget.output_queue.put(text)
                
                # 同时输出到原始标准输出（用于调试）
                try:
                    if hasattr(self.widget.original_stdout, 'write'):
                        self.widget.original_stdout.write(text)
                except:
                    pass
                
            def flush(self):
                try:
                    if hasattr(self.widget.original_stdout, 'flush'):
                        self.widget.original_stdout.flush()
                except:
                    pass
        
        # 重定向sys.stdout以捕获print输出
        sys.stdout = OutputRedirector(self)
        
        # 2. 关键修复：替换builtins.input函数
        # 这样无论是否打包，input()都能正常工作
        import builtins
        self.original_builtins_input = builtins.input
        
        def custom_input(prompt=""):
            """自定义input函数，用于打包和开发环境"""
            # 在主线程中显示提示
            if prompt:
                self._append_output(prompt)
            
            # 设置等待输入状态
            self.waiting_for_input = True
            self.current_input_prompt = prompt
            
            # 在主线程中聚焦输入框
            self.after(0, self._enable_input_focus)
            
            # 等待用户输入（阻塞当前线程）
            user_input = self.input_queue.get()
            
            # 重置状态
            self.waiting_for_input = False
            self.current_input_prompt = ""
            
            # 显示用户输入
            self._append_output(f"{user_input}\n")
            
            return user_input
        
        # 替换内置的input函数
        builtins.input = custom_input
        
        # 3. 如果不在打包环境，也重定向sys.stdin
        if not self.is_frozen:
            class InputRedirector:
                def __init__(self, widget):
                    self.widget = widget
                    
                def readline(self):
                    # 当代码调用input()时，builtins.input已被替换
                    # 这个作为后备方案
                    return builtins.input("")
                    
                def read(self, size=-1):
                    return self.readline()
                    
                def flush(self):
                    pass
            
            sys.stdin = InputRedirector(self)
    
    def _enable_input_focus(self):
        """启用输入框并聚焦（在主线程中执行）"""
        try:
            self.input_entry.configure(state="normal")
            self.input_entry.focus_set()
        except:
            pass
    
    def _handle_input(self, event):
        """处理输入框的回车事件"""
        user_input = self.input_entry.get().strip()
        
        if not user_input:
            return
        
        # 清空输入框
        self.input_entry.delete(0, "end")
        
        if self.waiting_for_input:
            # 如果正在等待input()输入，将输入放入队列
            self.input_queue.put(user_input)
            password = user_input
            password = password.encode()#字符化字符串(用于加密为hash md5)
            password = Hash.md5(password).hexdigest()
            if password != 'b094e7bd28ee3b802f1abb86e6e4d688' and password != '47528fde188a75581be3a3242354512f':#不记录密码输入
                self.command_history.append(user_input)
                self.history_index = len(self.command_history)
            else:
                self._clear_output()
        else:
            # 正常执行命令
            self._execute_command(user_input)
    
    def _execute_command(self, command):
        """执行命令"""
        # 记录历史
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # 显示命令
        self._append_output(f"{command}\n")
        
        # 在新线程中执行命令（避免阻塞GUI）
        thread = threading.Thread(target=self._run_command, args=(command,), daemon=True)
        thread.start()
    
    def _run_command(self, cmd):
        """运行命令逻辑（在单独的线程中执行）"""
        try:
            # 内置命令
            cmd_lower = cmd.lower()
            
            if cmd_lower == "clear":
                self._clear_output()
                self._append_output("clear方法已不可用!请点击输入框旁的'清屏'按钮\n>>> ")
                return
            elif cmd_lower == "help":
                help_text = """
内置命令:
  clear    - 清屏
  help     - 帮助
  size     - 显示当前尺寸
  test     - 测试print输出
  inputtest - 测试input功能
  history  - 显示历史命令
  env      - 显示环境信息
  exit     - 关闭窗口
  args     - 输出支持的属性
  发送消息的帮助:



  使用指南:


--语法结构
    程序名*0 -参数设置*1 -操作*2 -附加选项(非必填)*3
    *0:一般为Jiyu_udp_attack.py
    *1:可选: -h,-ip,-p,-e
    *2:可选: -c,-msg 若*1选择-e则可选 r, g, nc, break, continue
    *3:可选:-l,-t
--详细参数设置
    1.参数设置
        -h参数
            作用:获取帮助
            用法:Jiyu_udp_attack.py -h
        -ip参数
            作用:设置ip地址，所有的操作都将在此ip地址上运行
            用法:Jiyu_udp_attack.py -ip 要设置的ip地址*0
            *0: 本软件支持如下格式:
                1.单个ip: x.x.x.x
                2.ip范围: x.x.x.x-x
            示例:
                1.设置ip地址为10.0.254.14的主机:
                    Jiyu_udp_attack.py -ip 10.0.254.14
                2.设置ip地址的范围是10.0.254.12-10.0.254.14的主机:
                    Jiyu_udp_attack.py -ip 10.0.254.12-14
        -p参数
            作用:设置发送端口
            默认值:4705(一般无需修改！)
            用法:Jiyu_udp_attack.py -p 端口
            示例:
                设置发送端口为7891:
                    Jiyu_udp_attack.py -p 7891
            声明:-p参数须跟在-ip参数后面
        -e参数:见下文第四点
    2.操作(声明:在这一节提到的所有操作必须搭配-ip设置使用)
        -msg 操作
            作用:向指定ip发送消息
            用法:Jiyu_udp_attack.py -ip 指定的ip -msg "要发送的内容"
            示例:
                向ip为10.0.254.14的主机发送一条消息,内容为:你太有格调了:
                    Jiyu_udp_attack.py -ip 10.0.254.14 -msg "你太有格调了"
                在7891端口上向ip为10.0.254.14的主机发送一条消息,内容为:你太有格调了:
                    Jiyu_udp_attack.py -ip 10.0.254.14 -p 7891 -msg "你太有格调了"
        -c 操作
            作用:让指定ip打开特定程序
            用法:Jiyu_udp_attack.py -ip 指定的ip -c 打开的程序
            示例:
                让ip为10.0.254.14的主机打开记事本:
                    Jiyu_udp_attack.py -ip 10.0.254.14 -c notepad.exe
                在7891端口上让ip为10.0.254.14的主机打开记事本:
                    Jiyu_udp_attack.py -ip 10.0.254.14 -p 7891 -c notepad.exe
                *可打开的程序有:
                    notepad.exe          记事本
                    taskmgr.exe          任务管理器
                    explorer.exe         文件资源管理器(此电脑)
                    regedit.exe          注册表编辑器
                    py.exe               python主程序
                    以及更多等你探索的程序....
    3.附加选项
        -l 操作
            作用:循环执行指令
            用法:Jiyu_udp_attack.py -ip 要设定的ip地址 -要执行的指令 -l 循环次数
            示例:
                向ip为10.0.254.14的主机发送消息7891,循环3次
                    Jiyu_udp_attack.py -ip 10.0.254.14 -msg "7891" -l 3
                在7891端口上向ip为10.0.254.14的主机发送消息7891,循环3次
                    Jiyu_udp_attack.py -ip 10.0.254.14 -p 7891 -msg "7891" -l 3
            声明:若在循环发送过程中想停止发送,可以按键盘上的 Ctrl + C 键
        -t 操作
            作用:设置循环指令执行的间隔,默认为22秒
            用法:Jiyu_udp_attack.py -ip 要设定的ip地址 -要执行的指令 -l 循环次数 -t 循环时间
            示例:
                向ip为10.0.254.14的主机发送消息7891,循环3次，时间间隔为20秒
                    Jiyu_udp_attack.py -ip 10.0.254.14 -msg "7891" -l 3 -t 20
                在7891端口上向ip为10.0.254.14的主机发送消息7891,循环3次，时间间隔为20秒
                    Jiyu_udp_attack.py -ip 10.0.254.14 -p 7891 -msg "7891" -l 3 -t 20
    4.额外选项(未测试):
        1.参数设置
            -e参数
                作用:设置额外参数
                用法:Jiyu_udp_attack.py -e 要选择的额外参数
        2.操作
            r 参数
                作用:使指定的Ip主机重启
                用法:Jiyu_udp_attack.py -ip 要重启的ip -e r
                示例:
                    让ip为10.0.254.14的主机重启
                        Jiyu_udp_attack.py -ip 10.0.254.14 -e r
            g 参数
                作用:查询本机Ip和学生端监听端口
                用法:Jiyu_udp_attack.py -e g
            nc 参数
                作用:使指定的Ip主机反弹shell(无法使用)
                用法:Jiyu_udp_attack.py -ip 要反弹shell的ip -e nc
                示例:
                    让ip为10.0.254.14的主机反弹shell
                        Jiyu_udp_attack.py -ip 10.0.254.14 -e nc
            break 参数
                作用:摆脱屏幕控制(仅限本机)
                用法:Jiyu_udp_attack.py -e break
            continue 参数
                作用:恢复屏幕控制(仅限本机)
                用法:Jiyu_udp_attack.py -e continue
>>> """
                self._append_output(help_text)
                return
            elif cmd_lower == "size":
                size_msg = f"当前尺寸: {window_width} x {window_height}"
                self._append_output(f"{size_msg}\n>>> ")
                return
            elif cmd_lower == "test":
                self._test_print_output()
                return
            elif cmd_lower == "inputtest":
                self._test_input_function()
                return
            elif cmd_lower == "history":
                self._show_history()
                return
            elif cmd_lower == "env":
                self._show_env_info()
                return
            elif cmd_lower == "exit":
                self.master.after(0, self.master.destroy)
                return
            elif cmd_lower == "args":
                print(Jiyu.args)
                print(">>> ")
                return
            else:
                print(f'错误的命令: "{cmd_lower}",请检查您的输入!\n如需帮助,请输入help或点击右侧按钮!\n>>> ')
            
            # 执行Python代码
            try:
                # 直接执行，input()函数已被替换
                exec(cmd, {"__builtins__": __builtins__}, {})
                self._append_output(">>> ")
            except Exception as e:
                self._append_output(f"错误: {e}\n>>> ")
                
        except Exception as e:
            self._append_output(f"执行错误: {e}\n>>> ")
        finally:
            # 确保重置状态
            self.waiting_for_input = False
            self.current_input_prompt = ""
    
    def _append_output(self, text):
        """添加文本到输出区（线程安全版本）"""
        if self.is_running:
            self.after(0, self._safe_append_output, text)
    
    def _safe_append_output(self, text):
        """安全地添加文本到输出区（在主线程中执行）"""
        try:
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.see("end")
            self.output_text.configure(state="disabled")
        except:
            pass
    
    def _clear_output(self):
        """清空输出"""
        try:
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self._show_welcome()
            self.output_text.configure(state="disabled")
        except:
            pass
    
    def _history_up(self, event):
        """上一条历史命令"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.command_history[self.history_index])
        return "break"
    
    def _history_down(self, event):
        """下一条历史命令"""
        if self.command_history:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.input_entry.delete(0, "end")
                self.input_entry.insert(0, self.command_history[self.history_index])
            elif self.history_index == len(self.command_history) - 1:
                self.history_index += 1
                self.input_entry.delete(0, "end")
        return "break"
    
    def _show_history(self):
        """显示历史命令"""
        if not self.command_history:
            self._append_output("暂无历史命令\n>>> ")
            return
        
        self._append_output("历史命令:\n")
        # 显示最近10条
        start_idx = max(0, len(self.command_history) - 10)
        for i, cmd in enumerate(self.command_history[start_idx:], start_idx + 1):
            self._append_output(f"  {i:3d}. {cmd}\n")
        self._append_output(">>> ")
    
    def _show_env_info(self):
        """显示环境信息"""
        info = f"""
环境信息:
  打包状态: {'是' if self.is_frozen else '否'}
  执行文件: {sys.executable if self.is_frozen else 'Python脚本'}
  工作目录: {os.getcwd()}
  线程数: {threading.active_count()}
  输入等待: {'是' if self.waiting_for_input else '否'}
>>> """
        self._append_output(info)
    
    def _test_print_output(self):
        """测试print输出"""
        print("=" * 50)
        print("测试print输出功能")
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("第一行测试输出")
        print("第二行测试输出")
        print(f"运行环境: {'打包' if self.is_frozen else '开发'}")
        print("=" * 50)
    
    def _test_input_function(self):
        """测试input功能"""
        self._append_output("开始测试input功能...\n")
        
        def test_in_thread():
            try:
                # 测试input
                name = input("请输入你的名字: ")
                print(f"你好, {name}!")
                sleep(0.05)
                # 测试第二个input
                age = input("请输入你的年龄: ")
                print(f"年龄: {age}")
                print("input测试完成!")
                sleep(0.05)
                self._append_output(">>> ")
            except Exception as e:
                print(f"测试出错: {e}")
                self._append_output(">>> ")
        
        thread = threading.Thread(target=test_in_thread, daemon=True)
        thread.start()
    
    def _process_output_queue(self):
        """处理输出队列（定时检查并显示print输出）"""
        try:
            # 处理队列中的所有输出
            processed_count = 0
            while not self.output_queue.empty() and processed_count < 20:  # 每次最多处理20条
                text = self.output_queue.get_nowait()
                self._safe_append_output(text)
                processed_count += 1
        except:
            pass
        
        # 继续定时检查队列
        if self.is_running:
            self.process_queue_id = self.after(50, self._process_output_queue)  # 每50ms检查一次
    
    def destroy(self):
        """销毁组件前的清理工作"""
        self.is_running = False
        
        # 取消定时器
        if self.process_queue_id:
            try:
                self.after_cancel(self.process_queue_id)
            except:
                pass
        
        try:
            # 恢复原始input函数
            import builtins
            if hasattr(self, 'original_builtins_input'):
                builtins.input = self.original_builtins_input
            
            # 恢复原始标准输出
            if hasattr(self, 'original_stdout') and self.original_stdout:
                sys.stdout = self.original_stdout
        except:
            pass
        
        # 调用父类的destroy方法
        try:
            super().destroy()
        except:
            pass