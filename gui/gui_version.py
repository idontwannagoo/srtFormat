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
def add_styles_to_subtitles(input_file, output_file, chinese_font, english_font, chinese_font_size, english_font_size, chinese_font_color, english_font_color, chinese_bold, english_bold, chinese_italic, english_italic, chinese_blur, english_blur, shadow_opacity):
    chinese_style = r"{{\fn{font}\fs{font_size}\1c&H{font_color}&{bold}{italic}{blur}\4a&H{shadow_opacity}&}}".format(
        font=chinese_font,
        font_size=chinese_font_size,
        font_color=chinese_font_color.lstrip('#'),
        bold="" if chinese_bold else r"\b0",
        italic=r"\i1" if chinese_italic else "",
        blur=r"\be1" if chinese_blur else "",
        shadow_opacity=format(int(shadow_opacity), '02X')
    )
    english_style = r"{{\fn{font}\fs{font_size}\1c&H{font_color}&{bold}{italic}{blur}\4a&H{shadow_opacity}&}}".format(
        font=english_font,
        font_size=english_font_size,
        font_color=english_font_color.lstrip('#'),
        bold="" if english_bold else r"\b0",
        italic=r"\i1" if english_italic else "",
        blur=r"\be1" if english_blur else "",
        shadow_opacity=format(int(shadow_opacity), '02X')
    )

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
                new_lines.append("")

            if english_line:
                new_lines.append(f"{english_style}{english_line}{english_line_break}")
            else:
                new_lines.append("")

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

        # 新增参数
        chinese_font_color_frame = tk.Frame(self)
        chinese_font_color_frame.pack(pady=5)
        self.chinese_font_color_label = tk.Label(chinese_font_color_frame, text="中文字体颜色：")
        self.chinese_font_color_label.pack(side=tk.LEFT)
        self.chinese_font_color_entry = tk.Entry(chinese_font_color_frame, width=50)
        self.chinese_font_color_entry.insert(0, "#C8C8C8")  # 默认值
        self.chinese_font_color_entry.pack(side=tk.LEFT)

        english_font_color_frame = tk.Frame(self)
        english_font_color_frame.pack(pady=5)
        self.english_font_color_label = tk.Label(english_font_color_frame, text="英文字体颜色：")
        self.english_font_color_label.pack(side=tk.LEFT)
        self.english_font_color_entry = tk.Entry(english_font_color_frame, width=50)
        self.english_font_color_entry.insert(0, "#H0F94CB")  # 默认值
        self.english_font_color_entry.pack(side=tk.LEFT)

        # Checkboxes frame
        checkboxes_frame = tk.Frame(self)
        checkboxes_frame.pack(pady=5)

        self.chinese_bold_var = tk.BooleanVar(value=True)
        self.chinese_bold_check = tk.Checkbutton(checkboxes_frame, text="中文字体加粗", variable=self.chinese_bold_var)
        self.chinese_bold_check.grid(row=0, column=0, padx=5, pady=5)

        self.english_bold_var = tk.BooleanVar(value=False)
        self.english_bold_check = tk.Checkbutton(checkboxes_frame, text="英文字体加粗", variable=self.english_bold_var)
        self.english_bold_check.grid(row=0, column=1, padx=5, pady=5)

        self.chinese_italic_var = tk.BooleanVar(value=False)
        self.chinese_italic_check = tk.Checkbutton(checkboxes_frame, text="中文字体斜体",
                                                   variable=self.chinese_italic_var)
        self.chinese_italic_check.grid(row=1, column=0, padx=5, pady=5)

        self.english_italic_var = tk.BooleanVar(value=False)
        self.english_italic_check = tk.Checkbutton(checkboxes_frame, text="英文字体斜体",
                                                   variable=self.english_italic_var)
        self.english_italic_check.grid(row=1, column=1, padx=5, pady=5)

        self.chinese_blur_var = tk.BooleanVar(value=False)
        self.chinese_blur_check = tk.Checkbutton(checkboxes_frame, text="中文字体柔化", variable=self.chinese_blur_var)
        self.chinese_blur_check.grid(row=2, column=0, padx=5, pady=5)

        self.english_blur_var = tk.BooleanVar(value=False)
        self.english_blur_check = tk.Checkbutton(checkboxes_frame, text="英文字体柔化", variable=self.english_blur_var)
        self.english_blur_check.grid(row=2, column=1, padx=5, pady=5)

        shadow_opacity_frame = tk.Frame(self)
        shadow_opacity_frame.pack(pady=5)
        self.shadow_opacity_label = tk.Label(shadow_opacity_frame, text="阴影透明度：")
        self.shadow_opacity_label.pack(side=tk.LEFT)
        self.shadow_opacity_entry = tk.Entry(shadow_opacity_frame, width=50)
        self.shadow_opacity_entry.insert(0, "0")  # 默认值
        self.shadow_opacity_entry.pack(side=tk.LEFT)

        # 处理按钮
        self.process_button = tk.Button(self, text="处理字幕", command=self.process_subtitles)
        self.process_button.pack(pady=20)

        # 状态栏
        self.status_label = tk.Label(self, text="请选择 SRT 文件并点击处理", fg="blue", wraplength=580, justify="left")
        self.status_label.pack(pady=10)

    def update_fields_from_template(self, *args):
        selected_template = self.template_combobox.get()
        if selected_template == "选择模板":
            return

        with open('templates.json', 'r', encoding='utf-8') as file:
            templates = json.load(file)

        if selected_template in templates:
            template_data = templates[selected_template]
            self.chinese_font_entry.delete(0, tk.END)
            self.chinese_font_entry.insert(0, template_data["chinese_font"])
            self.english_font_entry.delete(0, tk.END)
            self.english_font_entry.insert(0, template_data["english_font"])
            self.chinese_font_size_entry.delete(0, tk.END)
            self.chinese_font_size_entry.insert(0, template_data["chinese_font_size"])
            self.english_font_size_entry.delete(0, tk.END)
            self.english_font_size_entry.insert(0, template_data["english_font_size"])
            self.chinese_font_color_entry.delete(0, tk.END)
            self.chinese_font_color_entry.insert(0, template_data["chinese_font_color"])
            self.english_font_color_entry.delete(0, tk.END)
            self.english_font_color_entry.insert(0, template_data["english_font_color"])
            self.chinese_bold_var.set(template_data["chinese_bold"])
            self.english_bold_var.set(template_data["english_bold"])
            self.chinese_italic_var.set(template_data["chinese_italic"])
            self.english_italic_var.set(template_data["english_italic"])
            self.chinese_blur_var.set(template_data["chinese_blur"])
            self.english_blur_var.set(template_data["english_blur"])
            self.shadow_opacity_entry.delete(0, tk.END)
            self.shadow_opacity_entry.insert(0, template_data["shadow_opacity"])
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
        template_name = f"{self.chinese_font_entry.get()}_{self.chinese_font_size_entry.get()}_" \
                        f"{self.english_font_entry.get()}_{self.english_font_size_entry.get()}_" \
                        f"{self.shadow_opacity_entry.get()}_" \
                        f"{'加粗' if self.chinese_bold_var.get() else ''}" \
                        f"{'斜体' if self.chinese_italic_var.get() else ''}" \
                        f"{'柔化' if self.chinese_blur_var.get() else ''}"

        template_data = {
            "chinese_font": self.chinese_font_entry.get(),
            "english_font": self.english_font_entry.get(),
            "chinese_font_size": self.chinese_font_size_entry.get(),
            "english_font_size": self.english_font_size_entry.get(),
            "chinese_font_color": self.chinese_font_color_entry.get(),
            "english_font_color": self.english_font_color_entry.get(),
            "chinese_bold": self.chinese_bold_var.get(),
            "english_bold": self.english_bold_var.get(),
            "chinese_italic": self.chinese_italic_var.get(),
            "english_italic": self.english_italic_var.get(),
            "chinese_blur": self.chinese_blur_var.get(),
            "english_blur": self.english_blur_var.get(),
            "shadow_opacity": self.shadow_opacity_entry.get()
        }

        self.templates.append(template_name)
        with open('templates.json', 'w', encoding='utf-8') as file:
            json.dump({template_name: template_data}, file, ensure_ascii=False, indent=4)

        self.load_templates_refresh()

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
            messagebox.showerror("错误", "请选择有效的 SRT 文件")
            return

        self.status_label.config(text="处理中...", fg="orange")
        self.update_idletasks()

        chinese_font = self.chinese_font_entry.get().strip() or "寒蝉端黑体 Compact"
        english_font = self.english_font_entry.get().strip() or chinese_font
        chinese_font_size = self.chinese_font_size_entry.get().strip() or "18"
        english_font_size = self.english_font_size_entry.get().strip() or "12"
        chinese_font_color = self.chinese_font_color_entry.get().strip() or "#C8C8C8"
        english_font_color = self.english_font_color_entry.get().strip() or "#H0F94CB"
        chinese_bold = self.chinese_bold_var.get()
        english_bold = self.english_bold_var.get()
        chinese_italic = self.chinese_italic_var.get()
        english_italic = self.english_italic_var.get()
        chinese_blur = self.chinese_blur_var.get()
        english_blur = self.english_blur_var.get()
        shadow_opacity = self.shadow_opacity_entry.get().strip() or "255"

        output_file = os.path.join(os.path.dirname(input_file),
                                   f"{chinese_font}_{english_font}_{os.path.basename(input_file)}")

        result = add_styles_to_subtitles(input_file, output_file, chinese_font, english_font, chinese_font_size,
                                         english_font_size, chinese_font_color, english_font_color, chinese_bold,
                                         english_bold, chinese_italic, english_italic, chinese_blur, english_blur,
                                         shadow_opacity)

        if os.path.isfile(result):
            self.status_label.config(text=f"处理完成: {result}", fg="green")
        else:
            self.status_label.config(text=f"处理失败: {result}", fg="red")

        self.update_idletasks()


if __name__ == "__main__":
    app = SubtitleProcessorApp()
    app.mainloop()
