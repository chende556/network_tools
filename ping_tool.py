# ping_tool.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import socket
from datetime import datetime

class PingTester:
    def __init__(self, root):
        self.root = root
        self.root.title("网络连通性测试工具 - 网络组·郭诚")
        self.root.geometry("800x600")
        self.center_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.is_testing = False
        self.processes = []
        self.progress_dict = {}

        self.setup_ui()

    def center_window(self):
        self.root.update_idletasks()
        w, h = 800, 600
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def get_gateway(self):
        try:
            if os.name == 'nt':
                result = subprocess.run(['route', 'print', '0.0.0.0'],
                                        capture_output=True, text=True, encoding='gbk', errors='ignore')
                for line in result.stdout.splitlines():
                    if '0.0.0.0' in line and '在链路上' not in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            ip = parts[2]
                            try:
                                socket.inet_aton(ip)
                                return ip
                            except:
                                pass
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 0))
                local = s.getsockname()[0]
                return '.'.join(local.split('.')[:3]) + '.1'
        except:
            pass
        return "192.168.1.1"

    def setup_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="网络连通性测试工具", font=("微软雅黑", 16, "bold")).pack(pady=(0, 15))

        info = ttk.LabelFrame(main, text="网络信息", padding=10)
        info.pack(fill=tk.X, pady=(0, 10))
        gateway = self.get_gateway()
        tk.Label(info, text=f"计算机名: {socket.gethostname()}", font=("微软雅黑", 10)).pack(anchor=tk.W)
        tk.Label(info, text=f"检测到网关: {gateway}", font=("微软雅黑", 10)).pack(anchor=tk.W)

        targets = [
            ("网关", gateway),
            ("公司DNS", "192.168.1.45"),
            ("百度网站", "www.baidu.com"),
            ("外网IP", "121.37.46.65")
        ]
        self.check_vars = []
        target_frame = ttk.LabelFrame(main, text="测试目标", padding=10)
        target_frame.pack(fill=tk.X, pady=(0, 10))
        for i, (name, host) in enumerate(targets):
            var = tk.BooleanVar(value=True)
            self.check_vars.append((var, name, host))
            cb = tk.Checkbutton(target_frame, text=f"{name} ({host})",
                                variable=var, font=("微软雅黑", 10))
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=5)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        self.start_btn = ttk.Button(btn_frame, text="开始测试", command=self.start_test)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.stop_btn = ttk.Button(btn_frame, text="停止测试", state=tk.DISABLED, command=self.stop_test)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="打开结果文件", command=self.open_result).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关于", command=self.show_about).pack(side=tk.RIGHT)

        self.progress = ttk.Progressbar(main, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 5))
        self.progress_text = tk.StringVar(value="等待开始...")
        tk.Label(main, textvariable=self.progress_text, font=("微软雅黑", 10)).pack(anchor=tk.W)

        self.status = tk.StringVar(value="就绪 - 请选择测试目标并点击开始测试")
        tk.Label(main, textvariable=self.status, font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(5, 0))

        log_frame = ttk.LabelFrame(main, text="实时结果", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9))
        self.log.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="© 网络组 - 郭诚", font=("微软雅黑", 8), fg="gray").pack(side=tk.BOTTOM, pady=(5, 0))

    def show_about(self):
        messagebox.showinfo("关于", "网络连通性测试工具\n\n开发维护：网络组 - 郭诚\n版本：1.0\n\n内部工具，请勿外传。")

    def update_log(self, msg):
        self.log.insert(tk.END, msg)
        self.log.see(tk.END)

    def update_progress(self):
        if not self.progress_dict:
            return
        total = sum(self.progress_dict.values()) / len(self.progress_dict)
        self.progress['value'] = total
        text = "进度: " + " ".join(f"{k}({v}%) " for k, v in self.progress_dict.items())
        self.progress_text.set(text)

    def ping_target(self, name, host, result_file):
        self.progress_dict[name] = 0
        self.root.after(0, self.update_progress)
        output_lines = []

        try:
            if os.name == 'nt':
                cmd = ['ping', '-n', '100', host]
            else:
                cmd = ['ping', '-c', '100', host]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding='gbk' if os.name == 'nt' else 'utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(proc)

            sent = 0
            while self.is_testing:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.rstrip('\n\r')
                output_lines.append(line)

                if '来自' in line or 'Reply from' in line or 'bytes from' in line:
                    sent += 1
                    self.progress_dict[name] = min(100, sent)
                    self.root.after(0, self.update_progress)
                    ts = datetime.now().strftime("%H:%M:%S")
                    self.root.after(0, self.update_log, f"[{ts}] {name}: {line}\n")

            try:
                proc.wait(timeout=5)
            except:
                pass

            try:
                with open(result_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n【{name} - {host}】\n" + "-"*50 + "\n")
                    f.write('\n'.join(output_lines))
                    f.write("\n" + "="*50 + "\n")
            except Exception as e:
                self.root.after(0, self.update_log, f"写入文件失败: {e}\n")

            self.progress_dict[name] = 100
            self.root.after(0, self.update_progress)
            self.root.after(0, self.update_log, f"\n{name}({host}): 测试完成 ✓\n\n")

        except Exception as e:
            err_msg = f"{name}({host}): 错误 - {e}"
            self.root.after(0, self.update_log, err_msg + "\n")

    def start_test(self):
        selected = [(name, host) for var, name, host in self.check_vars if var.get()]
        if not selected:
            messagebox.showwarning("警告", "请至少选择一个测试目标")
            return

        self.is_testing = True
        self.processes.clear()
        self.progress_dict = {}
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.log.delete(1.0, tk.END)
        self.status.set("测试进行中...")

        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.expanduser("~")
        except:
            desktop = os.getcwd()
        result_file = os.path.join(desktop, "ping_result.txt")

        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("网络连通性测试报告\n")
                f.write("工具提供：网络组 - 郭诚\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"计算机名: {socket.gethostname()}\n")
                f.write("="*60 + "\n\n目标:\n")
                for _, host in selected:
                    f.write(f"  - {host}\n")
                f.write("\n" + "="*60 + "\n\n")
        except Exception as e:
            messagebox.showerror("错误", f"无法创建结果文件: {e}\n将尝试保存到程序目录。")
            result_file = os.path.join(os.getcwd(), "ping_result.txt")
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write("...（略）...\n")

        self.update_log("开始并发测试...\n\n")

        def run_all():
            threads = []
            for name, host in selected:
                if not self.is_testing:
                    break
                t = threading.Thread(target=self.ping_target, args=(name, host, result_file), daemon=True)
                t.start()
                threads.append(t)
                self.update_log(f"已启动: {name}({host})\n")
                threading.Event().wait(0.3)

            for t in threads:
                t.join(timeout=120)

            if self.is_testing:
                self.root.after(0, self.finish_test, result_file)

        threading.Thread(target=run_all, daemon=True).start()

    def stop_test(self):
        self.is_testing = False
        for p in self.processes:
            try:
                p.terminate()
            except:
                pass
        self.processes.clear()
        self.status.set("测试已停止")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_log("\n" + "="*50 + "\n测试已被用户停止\n")

    def finish_test(self, result_file):
        self.is_testing = False
        self.progress['value'] = 100
        self.status.set("测试完成")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_log("\n" + "="*50 + f"\n所有测试完成！结果已保存至:\n{result_file}\n")

        if messagebox.askyesno("完成", "测试已完成！是否打开结果文件？"):
            self.open_result()

    def open_result(self):
        path = os.path.join(os.path.expanduser("~"), "Desktop", "ping_result.txt")
        if not os.path.exists(path):
            path = os.path.join(os.getcwd(), "ping_result.txt")
        if os.path.exists(path):
            try:
                os.startfile(path) if os.name == 'nt' else subprocess.run(['xdg-open', path])
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {e}")
        else:
            messagebox.showwarning("提示", "结果文件不存在，请先运行测试")

    def on_closing(self):
        if self.is_testing:
            if messagebox.askokcancel("退出", "测试正在进行，确定退出？"):
                self.stop_test()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    PingTester(root)
    root.mainloop()