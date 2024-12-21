import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import json


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


# 处理字幕并添加样式
def add_styles_to_subtitles(input_file, output_file, chinese_font, english_font, chinese_font_size, english_font_size):
    chinese_style = r"{{\fn{font}\fs{font_size}\1c&HC8C8C8&}}".format(font=chinese_font, font_size=chinese_font_size)
    english_style = r"{{\fn{font}\fs{font_size}\1c&H0F94CB&\b0}}".format(font=english_font, font_size=english_font_size)

    chinese_line_break = r"{\r}"
    english_line_break = ""

    try:
        with open(input_file, 'r', encoding='UTF-8-sig') as file:
            lines = file.readlines()

        subtitle_groups = []
        i = 0
        while i < len(lines):
            subtitle_num = lines[i].strip()
            if not subtitle_num.isdigit():
                i += 1
                continue
            i += 1
            timestamp = lines[i].strip()
            i += 1
            chinese_line = lines[i].strip() if i < len(lines) else ""
            i += 1
            english_line = lines[i].strip() if i < len(lines) else ""
            i += 1

            subtitle_groups.append([subtitle_num, timestamp, chinese_line, english_line])

        new_lines = []
        for group in subtitle_groups:
            subtitle_num, timestamp, chinese_line, english_line = group

            new_lines.append(f"{subtitle_num}")
            new_lines.append(f"{timestamp}")

            if chinese_line:
                new_lines.append(f"{chinese_style}{chinese_line}{chinese_line_break}")
            else:
                new_lines.append(f"{chinese_line_break}")

            if english_line:
                new_lines.append(f"{english_style}{english_line}{english_line_break}")
            else:
                new_lines.append(f"{english_line_break}")

            new_lines.append('')

        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines('\n'.join(new_lines) + '\n')

        return output_file

    except Exception as e:
        return str(e)


class SubtitleProcessorApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("字幕处理工具")
        self.geometry("500x600")

        # 禁止窗口自动调整大小
        self.pack_propagate(False)

        # 初始化模板数据
        self.templates = []  # 确保初始化
        self.load_templates()  # 加载模板

        # 创建UI组件
        self.create_widgets()

        # 强制更新布局
        self.update_idletasks()

    def create_widgets(self):
        # SRT文件路径输入框和拖拽区域
        self.srt_file_label = tk.Label(self, text="拖入 SRT 文件：")
        self.srt_file_label.pack(pady=5)

        srt_file_frame = tk.Frame(self)
        srt_file_frame.pack(pady=5)

        self.srt_file_entry = tk.Entry(srt_file_frame, width=50)
        self.srt_file_entry.pack(side=tk.LEFT, padx=5)

        self.browse_button = tk.Button(srt_file_frame, text="浏览", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        self.srt_file_entry.drop_target_register(DND_FILES)
        self.srt_file_entry.dnd_bind('<<Drop>>', self.on_file_drop)

        # 选择模板
        self.template_label = tk.Label(self, text="选择模板：")
        self.template_label.pack(pady=5)

        self.template_combobox = tk.StringVar()
        self.template_combobox.set("选择模板")  # 设置默认值
        self.template_menu = tk.OptionMenu(self, self.template_combobox, *self.templates)
        self.template_menu.pack(pady=5)
        self.template_combobox.trace("w", self.update_fields_from_template)

        # 添加模板和删除模板按钮放在同一排
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        self.save_template_button = tk.Button(button_frame, text="添加当前数据为模板", command=self.save_template)
        self.save_template_button.pack(side=tk.LEFT, padx=5)

        self.delete_template_button = tk.Button(button_frame, text="删除当前模板", command=self.delete_template)
        self.delete_template_button.pack(side=tk.LEFT, padx=5)

        # 字体和大小设置
        chinese_font_frame = tk.Frame(self)
        chinese_font_frame.pack(pady=5)
        self.chinese_font_label = tk.Label(chinese_font_frame, text="中文字体：")
        self.chinese_font_label.pack(side=tk.LEFT)
        self.chinese_font_entry = tk.Entry(chinese_font_frame, width=50)
        self.chinese_font_entry.insert(0, "寒蝉端黑体 Compact")  # 默认值
        self.chinese_font_entry.pack(side=tk.LEFT)

        english_font_frame = tk.Frame(self)
        english_font_frame.pack(pady=5)
        self.english_font_label = tk.Label(english_font_frame, text="英文字体：")
        self.english_font_label.pack(side=tk.LEFT)
        self.english_font_entry = tk.Entry(english_font_frame, width=50)
        self.english_font_entry.insert(0, "寒蝉端黑体 Compact")  # 默认值
        self.english_font_entry.pack(side=tk.LEFT)

        chinese_font_size_frame = tk.Frame(self)
        chinese_font_size_frame.pack(pady=5)
        self.chinese_font_size_label = tk.Label(chinese_font_size_frame, text="中文字体大小：")
        self.chinese_font_size_label.pack(side=tk.LEFT)
        self.chinese_font_size_entry = tk.Entry(chinese_font_size_frame, width=50)
        self.chinese_font_size_entry.insert(0, "18")  # 默认值
        self.chinese_font_size_entry.pack(side=tk.LEFT)

        english_font_size_frame = tk.Frame(self)
        english_font_size_frame.pack(pady=5)
        self.english_font_size_label = tk.Label(english_font_size_frame, text="英文字体大小：")
        self.english_font_size_label.pack(side=tk.LEFT)
        self.english_font_size_entry = tk.Entry(english_font_size_frame, width=50)
        self.english_font_size_entry.insert(0, "12")  # 默认值
        self.english_font_size_entry.pack(side=tk.LEFT)

        # 处理按钮
        self.process_button = tk.Button(self, text="处理字幕", command=self.process_subtitles)
        self.process_button.pack(pady=20)

        # 状态栏
        self.status_label = tk.Label(self, text="请选择 SRT 文件并点击处理", fg="blue", wraplength=580, justify="left")
        self.status_label.pack(pady=10)

    def update_fields_from_template(self, *args):
        template_name = self.template_combobox.get()
        if template_name == "选择模板" or template_name == "默认模板":
            return

        if os.path.exists("template.json"):
            with open("template.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for template in data.get("templates", []):
                        if template["name"] == template_name:
                            self.chinese_font_entry.delete(0, tk.END)
                            self.chinese_font_entry.insert(0, template["chinese_font"])
                            self.english_font_entry.delete(0, tk.END)
                            self.english_font_entry.insert(0, template["english_font"])
                            self.chinese_font_size_entry.delete(0, tk.END)
                            self.chinese_font_size_entry.insert(0, template["chinese_font_size"])
                            self.english_font_size_entry.delete(0, tk.END)
                            self.english_font_size_entry.insert(0, template["english_font_size"])
                            break
                except json.JSONDecodeError:
                    pass

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if file_path:
            self.srt_file_entry.delete(0, tk.END)
            self.srt_file_entry.insert(0, file_path)
    def load_templates(self):
        """加载模板配置"""
        self.templates = ["默认模板"]
        if os.path.exists("template.json"):
            with open("template.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for template in data.get("templates", []):
                        self.templates.append(template["name"])
                except json.JSONDecodeError:
                    pass
    def load_templates_refresh(self):
        """加载模板配置"""
        self.templates = ["默认模板"]
        if os.path.exists("template.json"):
            with open("template.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for template in data.get("templates", []):
                        self.templates.append(template["name"])
                except json.JSONDecodeError:
                    pass

        # 更新下拉框选项
        menu = self.template_menu["menu"]
        menu.delete(0, "end")
        for template in self.templates:
            menu.add_command(label=template, command=lambda value=template: self.template_combobox.set(value))

        self.template_combobox.set("选择模板")
    def save_template(self):
        """保存当前设置为模板"""
        current_template = {
            "name": f"{self.chinese_font_entry.get()}_{self.english_font_entry.get()}",
            "chinese_font": self.chinese_font_entry.get(),
            "english_font": self.english_font_entry.get(),
            "chinese_font_size": self.chinese_font_size_entry.get(),
            "english_font_size": self.english_font_size_entry.get()
        }

        # 读取现有模板
        if os.path.exists("template.json"):
            with open("template.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {"templates": []}
        else:
            data = {"templates": []}

        # 将当前模板添加到模板列表
        data["templates"].append(current_template)

        # 保存模板到文件
        with open("template.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # 更新模板选择框
        self.load_templates_refresh()
        self.template_combobox.set(current_template["name"])

    def delete_template(self):
        """删除当前选中的模板"""
        template_name = self.template_combobox.get()
        if template_name == "选择模板" or template_name == "默认模板":
            messagebox.showwarning("警告", "请选择一个有效的模板进行删除。")
            return

        # 读取现有模板
        if os.path.exists("template.json"):
            with open("template.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {"templates": []}
        else:
            data = {"templates": []}

        # 删除选中的模板
        data["templates"] = [template for template in data["templates"] if template["name"] != template_name]

        # 保存修改后的模板数据
        with open("template.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # 更新模板列表
        self.load_templates_refresh()
        self.template_combobox.set("选择模板")

    def on_file_drop(self, event):
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
        self.update_idletasks()

        chinese_font = self.chinese_font_entry.get().strip() or "寒蝉端黑体 Compact"
        english_font = self.english_font_entry.get().strip() or chinese_font
        chinese_font_size = self.chinese_font_size_entry.get().strip() or "18"
        english_font_size = self.english_font_size_entry.get().strip() or "12"

        output_file = os.path.join(os.path.dirname(input_file),
                                   f"{chinese_font}_{english_font}_{os.path.basename(input_file)}")

        result = add_styles_to_subtitles(input_file, output_file, chinese_font, english_font, chinese_font_size,
                                         english_font_size)

        if os.path.isfile(result):
            self.status_label.config(text=f"处理完成，输出文件保存在：{result}", fg="green")
        else:
            self.status_label.config(text=f"处理过程中发生错误：{result}", fg="red")

        self.update_idletasks()


if __name__ == "__main__":
    app = SubtitleProcessorApp()
    app.mainloop()
