import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES

import ctypes



# 判断文件名中是否包含指定的标识符
def get_file_priority(file_name):
    file_name = file_name.lower()  # 转小写方便判断
    # 定义优先级，越靠前优先级越高
    if 'chseng' in file_name:
        return 3
    elif 'chs' in file_name:
        return 2
    elif 'ch' in file_name:
        return 1
    else:
        return 0


def add_styles_to_subtitles(input_file, output_file, chinese_font, english_font, chinese_font_size, english_font_size):
    # 定义中文和英文的样式前缀
    chinese_style = r"{{\fn{font}\fs{font_size}\1c&HC8C8C8&}}".format(font=chinese_font, font_size=chinese_font_size)
    english_style = r"{{\fn{font}\fs{font_size}\1c&H0F94CB&\b0}}".format(font=english_font, font_size=english_font_size)

    # 定义换行符，中文使用这个，英文行不加换行符
    chinese_line_break = r"{\r}"
    english_line_break = ""

    try:
        with open(input_file, 'r', encoding='UTF-8-sig') as file:
            lines = file.readlines()

        # 处理字幕并按编号分组
        subtitle_groups = []
        i = 0
        while i < len(lines):
            subtitle_num = lines[i].strip()  # 获取字幕编号
            if not subtitle_num.isdigit():
                i += 1
                continue
            i += 1
            timestamp = lines[i].strip()  # 获取时间戳
            i += 1
            chinese_line = lines[i].strip() if i < len(lines) else ""  # 获取中文行
            i += 1
            english_line = lines[i].strip() if i < len(lines) else ""  # 获取英文行
            i += 1

            # 将每个字幕项分成四部分
            subtitle_groups.append([subtitle_num, timestamp, chinese_line, english_line])

        # 处理每个字幕项，添加样式
        new_lines = []
        for group in subtitle_groups:
            subtitle_num, timestamp, chinese_line, english_line = group

            # 添加字幕编号和时间戳
            new_lines.append(f"{subtitle_num}")
            new_lines.append(f"{timestamp}")

            # 如果有中文行，添加中文样式
            if chinese_line:
                new_lines.append(f"{chinese_style}{chinese_line}{chinese_line_break}")
            else:
                new_lines.append(f"{chinese_line_break}")  # 如果没有中文行，添加换行符

            # 如果有英文行，添加英文样式，并且不加换行符
            if english_line:
                new_lines.append(f"{english_style}{english_line}{english_line_break}")
            else:
                new_lines.append(f"{english_line_break}")  # 如果没有英文行，添加换行符

            # 每个字幕项之间要添加一个空行
            new_lines.append('')  # 添加空行作为分隔

        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines('\n'.join(new_lines) + '\n')

        return output_file

    except Exception as e:
        return str(e)


class SubtitleProcessorApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("字幕处理工具")
        self.geometry("500x500")

        # 禁止窗口自动调整大小，防止它自动根据内容调整
        self.pack_propagate(False)

        # 创建UI组件
        self.create_widgets()

        # 强制更新布局以确保状态栏立即可见
        self.update_idletasks()

    def create_widgets(self):
        # SRT文件路径输入框和拖拽区域
        self.srt_file_label = tk.Label(self, text="拖入 SRT 文件：")
        self.srt_file_label.pack(pady=5)

        self.srt_file_entry = tk.Entry(self, width=50)
        self.srt_file_entry.pack(pady=5)

        self.srt_file_entry.drop_target_register(DND_FILES)
        self.srt_file_entry.dnd_bind('<<Drop>>', self.on_file_drop)

        # 字体和大小设置
        self.chinese_font_label = tk.Label(self, text="中文字体：")
        self.chinese_font_label.pack(pady=5)
        self.chinese_font_entry = tk.Entry(self, width=50)
        self.chinese_font_entry.insert(0, "寒蝉端黑体 Compact")  # 默认值
        self.chinese_font_entry.pack(pady=5)

        self.english_font_label = tk.Label(self, text="英文字体：")
        self.english_font_label.pack(pady=5)
        self.english_font_entry = tk.Entry(self, width=50)
        self.english_font_entry.insert(0, "寒蝉端黑体 Compact")  # 默认值
        self.english_font_entry.pack(pady=5)

        self.chinese_font_size_label = tk.Label(self, text="中文字体大小：")
        self.chinese_font_size_label.pack(pady=5)
        self.chinese_font_size_entry = tk.Entry(self, width=50)
        self.chinese_font_size_entry.insert(0, "18")  # 默认值
        self.chinese_font_size_entry.pack(pady=5)

        self.english_font_size_label = tk.Label(self, text="英文字体大小：")
        self.english_font_size_label.pack(pady=5)
        self.english_font_size_entry = tk.Entry(self, width=50)
        self.english_font_size_entry.insert(0, "12")  # 默认值
        self.english_font_size_entry.pack(pady=5)

        # 处理按钮
        self.process_button = tk.Button(self, text="处理字幕", command=self.process_subtitles)
        self.process_button.pack(pady=20)

        # 状态栏
        self.status_label = tk.Label(self, text="请选择 SRT 文件并点击处理", fg="blue", wraplength=580, justify="left")
        self.status_label.pack(pady=10)

    def on_file_drop(self, event):
        # 当文件被拖放到SRT文件输入框时，自动填写路径
        file_path = event.data
        if file_path.endswith(".srt"):
            self.srt_file_entry.delete(0, tk.END)
            self.srt_file_entry.insert(0, file_path)
        else:
            messagebox.showerror("错误", "请拖入有效的 .srt 文件。")

    def process_subtitles(self):
        input_file = self.srt_file_entry.get().strip()

        if not os.path.isfile(input_file):
            messagebox.showerror("错误", "请输入有效的 .srt 文件路径。")
            return

        # 更新状态为处理中
        self.status_label.config(text="处理中...", fg="orange")

        # 强制更新界面以刷新显示
        self.update_idletasks()

        # 获取字体和大小设置
        chinese_font = self.chinese_font_entry.get().strip() or "寒蝉端黑体 Compact"
        english_font = self.english_font_entry.get().strip() or chinese_font
        chinese_font_size = self.chinese_font_size_entry.get().strip() or "18"
        english_font_size = self.english_font_size_entry.get().strip() or "12"

        # 设置输出文件路径（在同一目录下）
        output_file = os.path.join(os.path.dirname(input_file), f"{chinese_font}_{english_font}_{os.path.basename(input_file)}" if chinese_font != english_font else f"{chinese_font}_{os.path.basename(input_file)}")

        # 调用处理函数
        result = add_styles_to_subtitles(input_file, output_file, chinese_font, english_font, chinese_font_size, english_font_size)

        # 更新状态显示
        if os.path.isfile(result):
            self.status_label.config(text=f"处理完成，输出文件保存在：{result}", fg="green")
        else:
            self.status_label.config(text=f"处理过程中发生错误：{result}", fg="red")

        # 强制更新界面以刷新显示
        self.update_idletasks()


if __name__ == "__main__":
    app = SubtitleProcessorApp()
    app.mainloop()
