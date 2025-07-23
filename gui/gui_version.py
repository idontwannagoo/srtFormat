import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import json
import chardet
import tempfile
import re
import subprocess
import sys

# 尝试导入 pysubs2 ，如果没有安装则提供安装指南
try:
    import pysubs2
except ImportError:
    pysubs2 = None

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
        # 检查文件扩展名
        file_ext = os.path.splitext(input_file)[1].lower()
        temp_srt_file = None
        
        if file_ext == '.ass':
            # 如果是 ASS 文件，先转换为 SRT
            if pysubs2 is None:
                return " 请安装 pysubs2 库以支持 ASS 文件 : pip install pysubs2"
                
            temp_srt_path, error = convert_ass_to_srt(input_file)
            if error:
                return error
                
            temp_srt_file = temp_srt_path
            input_file = temp_srt_path

        # 检测文件编码
        try:
            with open(input_file, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
    
            # 定义多种可能的编码
            encodings_to_try = [encoding, 'utf-8', 'utf-8-sig', 'gbk', 'big5', 'shift-jis', 'cp1252', 'latin-1', 'UTF-16']
            
            lines = None
            for enc in encodings_to_try:
                if enc is None:
                    continue
                try:
                    with open(input_file, 'r', encoding=enc) as file:
                        lines = file.readlines()
                        break
                except UnicodeDecodeError:
                    continue
                
            if lines is None:
                return f" 无法解码文件，尝试了以下编码 : {', '.join([e for e in encodings_to_try if e])}"
        except Exception as e:
            return f" 读取文件时出错 : {str(e)}"

        # 检测字幕格式类型
        subtitle_format = detect_subtitle_format(lines)
        
        if subtitle_format == "standard":
            # 标准格式：一个时间戳后跟中英文
            subtitle_groups = process_standard_format(lines)
        elif subtitle_format == "ass":
            # ASS 格式已经转换为 SRT，使用标准格式处理
            subtitle_groups = process_standard_format(lines)
        else:
            # 分离格式：相同时间戳的两个连续字幕块
            subtitle_groups = process_separated_format(lines)

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

        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.writelines('\n'.join(new_lines) + '\n')
        except Exception as write_error:
            return f" 写入输出文件时出错 : {str(write_error)}"

        # 如果创建了临时文件，删除它
        if temp_srt_file and os.path.exists(temp_srt_file):
            try:
                os.unlink(temp_srt_file)
            except:
                pass

        return output_file

    except Exception as e:
        # 确保清理临时文件
        if 'temp_srt_file' in locals() and temp_srt_file and os.path.exists(temp_srt_file):
            try:
                os.unlink(temp_srt_file)
            except:
                pass
        return str(e)

def detect_subtitle_format(lines):
    """ 检测字幕格式类型 """
    # 检查是否是 ASS 格式
    for line in lines[:20]:  # 只检查前 20 行
        if line.strip().startswith('[Script Info]') or '[V4+ Styles]' in line or '[Events]' in line:
            return "ass"
            
    i = 0
    timestamps = []
    
    while i < len(lines):
        line = lines[i].strip()
        if line.isdigit():  # 字幕序号
            i += 1
            if i < len(lines):
                timestamp = lines[i].strip()
                if " --> " in timestamp:  # 时间戳
                    timestamps.append(timestamp)
        i += 1
    
    # 检查是否有重复的时间戳
    timestamp_count = {}
    for ts in timestamps:
        timestamp_count[ts] = timestamp_count.get(ts, 0) + 1
    
    # 如果有大量重复时间戳，认为是分离格式
    duplicate_count = sum(1 for count in timestamp_count.values() if count > 1)
    if duplicate_count > len(timestamps) * 0.3:  # 如果超过 30% 的时间戳有重复
        return "separated"
    else:
        return "standard"

def process_standard_format(lines):
    """ 处理标准格式：一个时间戳后跟中英文 """
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
    
    return subtitle_groups

def process_separated_format(lines):
    """ 处理分离格式：相同时间戳的两个连续字幕块 """
    # 先收集所有字幕块
    blocks = []
    current_block = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    
    if current_block:
        blocks.append(current_block)
    
    # 合并相同时间戳的字幕块
    subtitle_groups = []
    i = 0
    while i < len(blocks) - 1:
        block1 = blocks[i]
        block2 = blocks[i + 1]
        
        # 检查两个块是否有相同的时间戳
        if len(block1) >= 2 and len(block2) >= 2 and block1[1] == block2[1]:
            # 假设第一个块是中文，第二个块是英文
            subtitle_num = block1[0]
            timestamp = block1[1]
            chinese_line = block1[2] if len(block1) > 2 else ""
            english_line = block2[2] if len(block2) > 2 else ""
            
            # 检查是否英文在引号中，这通常表示英文
            if chinese_line and chinese_line.startswith('"') and chinese_line.endswith('"'):
                chinese_line, english_line = english_line, chinese_line
            
            subtitle_groups.append([subtitle_num, timestamp, chinese_line, english_line])
            i += 2
        else:
            # 如果时间戳不同，则按标准格式处理当前块
            if len(block1) >= 3:
                subtitle_num = block1[0]
                timestamp = block1[1]
                text_line = block1[2]
                
                # 尝试分割中英文
                if "\n" in text_line:
                    chinese_line, english_line = text_line.split("\n", 1)
                else:
                    chinese_line = text_line
                    english_line = ""
                
                subtitle_groups.append([subtitle_num, timestamp, chinese_line, english_line])
            i += 1
    
    # 处理最后一个块（如果有）
    if i < len(blocks):
        block = blocks[i]
        if len(block) >= 3:
            subtitle_num = block[0]
            timestamp = block[1]
            text_line = block[2]
            
            # 尝试分割中英文
            if "\n" in text_line:
                chinese_line, english_line = text_line.split("\n", 1)
            else:
                chinese_line = text_line
                english_line = ""
            
            subtitle_groups.append([subtitle_num, timestamp, chinese_line, english_line])
    
    return subtitle_groups

# 添加处理 ASS 字幕的新函数
def convert_ass_to_srt(ass_file_path):
    """
    将 ASS 字幕文件转换为 SRT 格式
    :param ass_file_path: ASS 文件路径
    :return: 转换后的 SRT 文件路径
    """
    if pysubs2 is None:
        return None, " 请安装 pysubs2 库以支持 ASS 文件 : pip install pysubs2"
    
    try:
        # 创建临时文件来保存 SRT 输出
        fd, temp_srt_path = tempfile.mkstemp(suffix='.srt')
        os.close(fd)
        
        # 检测文件编码
        with open(ass_file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
        
        # 尝试多种编码方式加载 ASS 文件
        encodings_to_try = [encoding, 'utf-8', 'utf-8-sig', 'gbk', 'big5', 'shift-jis', 'cp1252', 'latin-1']
        success = False
        error_msg = ""
        
        for enc in encodings_to_try:
            if enc is None:
                continue
                
            try:
                # 使用 pysubs2 加载 ASS 文件并保存为 SRT
                subs = pysubs2.load(ass_file_path, encoding=enc)
                subs.save(temp_srt_path, format_='srt', encoding='utf-8')
                success = True
                break
            except Exception as e:
                error_msg = str(e)
                continue
        
        if not success:
            return None, f" 无法加载字幕文件，尝试了多种编码但都失败了。最后的错误 : {error_msg}"
        
        return temp_srt_path, None
    except Exception as e:
        if 'temp_srt_path' in locals() and os.path.exists(temp_srt_path):
            try:
                os.unlink(temp_srt_path)
            except:
                pass
        return None, str(e)

class SubtitleProcessorApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title(" 字幕处理工具 ")
        self.geometry("500x750")  # 增加窗口高度以容纳更多内容

        # 禁止窗口自动调整大小
        self.pack_propagate(False)

        # 初始化模板数据
        self.templates = []  # 确保初始化
        self.load_templates()  # 加载模板

        # 创建 UI 组件
        self.create_widgets()
        
        # 检查 pysubs2 是否已安装
        if pysubs2 is None:
            self.status_label.config(text=" 提示 : 未安装 pysubs2 库，无法处理 ASS 字幕文件。请运行 : pip install pysubs2", fg="orange")

        # 强制更新布局
        self.update_idletasks()

    def create_widgets(self):
        # SRT 文件路径输入框和拖拽区域
        self.srt_file_label = tk.Label(self, text=" 拖入字幕文件 (SRT 或 ASS)：")
        self.srt_file_label.pack(pady=5)

        srt_file_frame = tk.Frame(self)
        srt_file_frame.pack(pady=5)

        self.srt_file_entry = tk.Entry(srt_file_frame, width=50)
        self.srt_file_entry.pack(side=tk.LEFT, padx=5)

        self.browse_button = tk.Button(srt_file_frame, text=" 浏览 ", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        self.srt_file_entry.drop_target_register(DND_FILES)
        self.srt_file_entry.dnd_bind('<<Drop>>', self.on_file_drop)

        # 选择模板
        self.template_label = tk.Label(self, text=" 选择模板：")
        self.template_label.pack(pady=5)

        self.template_combobox = tk.StringVar()
        self.template_combobox.set(" 选择模板 ")  # 设置默认值
        self.template_menu = tk.OptionMenu(self, self.template_combobox, *self.templates)
        self.template_menu.pack(pady=5)
        self.template_combobox.trace("w", self.update_fields_from_template)

        # 添加模板和删除模板按钮放在同一排
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        self.save_template_button = tk.Button(button_frame, text=" 添加当前数据为模板 ", command=self.save_template)
        self.save_template_button.pack(side=tk.LEFT, padx=5)

        self.delete_template_button = tk.Button(button_frame, text=" 删除当前模板 ", command=self.delete_template)
        self.delete_template_button.pack(side=tk.LEFT, padx=5)

        # 字体和大小设置
        chinese_font_frame = tk.Frame(self)
        chinese_font_frame.pack(pady=5)
        self.chinese_font_label = tk.Label(chinese_font_frame, text=" 中文字体：")
        self.chinese_font_label.pack(side=tk.LEFT)
        self.chinese_font_entry = tk.Entry(chinese_font_frame, width=50)
        self.chinese_font_entry.insert(0, " 寒蝉端黑体 Compact")  # 默认值
        self.chinese_font_entry.pack(side=tk.LEFT)

        english_font_frame = tk.Frame(self)
        english_font_frame.pack(pady=5)
        self.english_font_label = tk.Label(english_font_frame, text=" 英文字体：")
        self.english_font_label.pack(side=tk.LEFT)
        self.english_font_entry = tk.Entry(english_font_frame, width=50)
        self.english_font_entry.insert(0, " 寒蝉端黑体 Compact")  # 默认值
        self.english_font_entry.pack(side=tk.LEFT)

        chinese_font_size_frame = tk.Frame(self)
        chinese_font_size_frame.pack(pady=5)
        self.chinese_font_size_label = tk.Label(chinese_font_size_frame, text=" 中文字体大小：")
        self.chinese_font_size_label.pack(side=tk.LEFT)
        self.chinese_font_size_entry = tk.Entry(chinese_font_size_frame, width=50)
        self.chinese_font_size_entry.insert(0, "18")  # 默认值
        self.chinese_font_size_entry.pack(side=tk.LEFT)

        english_font_size_frame = tk.Frame(self)
        english_font_size_frame.pack(pady=5)
        self.english_font_size_label = tk.Label(english_font_size_frame, text=" 英文字体大小：")
        self.english_font_size_label.pack(side=tk.LEFT)
        self.english_font_size_entry = tk.Entry(english_font_size_frame, width=50)
        self.english_font_size_entry.insert(0, "12")  # 默认值
        self.english_font_size_entry.pack(side=tk.LEFT)

        # 新增参数
        chinese_font_color_frame = tk.Frame(self)
        chinese_font_color_frame.pack(pady=5)
        self.chinese_font_color_label = tk.Label(chinese_font_color_frame, text=" 中文字体颜色：")
        self.chinese_font_color_label.pack(side=tk.LEFT)
        self.chinese_font_color_entry = tk.Entry(chinese_font_color_frame, width=50)
        self.chinese_font_color_entry.insert(0, "#C8C8C8")  # 默认值
        self.chinese_font_color_entry.pack(side=tk.LEFT)

        english_font_color_frame = tk.Frame(self)
        english_font_color_frame.pack(pady=5)
        self.english_font_color_label = tk.Label(english_font_color_frame, text=" 英文字体颜色：")
        self.english_font_color_label.pack(side=tk.LEFT)
        self.english_font_color_entry = tk.Entry(english_font_color_frame, width=50)
        self.english_font_color_entry.insert(0, "#0F94CB")  # 默认值
        self.english_font_color_entry.pack(side=tk.LEFT)

        # Checkboxes frame
        checkboxes_frame = tk.Frame(self)
        checkboxes_frame.pack(pady=5)

        self.chinese_bold_var = tk.BooleanVar(value=True)
        self.chinese_bold_check = tk.Checkbutton(checkboxes_frame, text=" 中文字体加粗 ", variable=self.chinese_bold_var)
        self.chinese_bold_check.grid(row=0, column=0, padx=5, pady=5)

        self.english_bold_var = tk.BooleanVar(value=False)
        self.english_bold_check = tk.Checkbutton(checkboxes_frame, text=" 英文字体加粗 ", variable=self.english_bold_var)
        self.english_bold_check.grid(row=0, column=1, padx=5, pady=5)

        self.chinese_italic_var = tk.BooleanVar(value=False)
        self.chinese_italic_check = tk.Checkbutton(checkboxes_frame, text=" 中文字体斜体 ",
                                                   variable=self.chinese_italic_var)
        self.chinese_italic_check.grid(row=1, column=0, padx=5, pady=5)

        self.english_italic_var = tk.BooleanVar(value=False)
        self.english_italic_check = tk.Checkbutton(checkboxes_frame, text=" 英文字体斜体 ",
                                                   variable=self.english_italic_var)
        self.english_italic_check.grid(row=1, column=1, padx=5, pady=5)

        self.chinese_blur_var = tk.BooleanVar(value=False)
        self.chinese_blur_check = tk.Checkbutton(checkboxes_frame, text=" 中文字体柔化 ", variable=self.chinese_blur_var)
        self.chinese_blur_check.grid(row=2, column=0, padx=5, pady=5)

        self.english_blur_var = tk.BooleanVar(value=False)
        self.english_blur_check = tk.Checkbutton(checkboxes_frame, text=" 英文字体柔化 ", variable=self.english_blur_var)
        self.english_blur_check.grid(row=2, column=1, padx=5, pady=5)

        shadow_opacity_frame = tk.Frame(self)
        shadow_opacity_frame.pack(pady=5)
        self.shadow_opacity_label = tk.Label(shadow_opacity_frame, text=" 阴影透明度：")
        self.shadow_opacity_label.pack(side=tk.LEFT)
        self.shadow_opacity_entry = tk.Entry(shadow_opacity_frame, width=50)
        self.shadow_opacity_entry.insert(0, "0")  # 默认值
        self.shadow_opacity_entry.pack(side=tk.LEFT)

        # 处理按钮
        self.process_button = tk.Button(self, text=" 处理字幕 ", command=self.process_subtitles)
        self.process_button.pack(pady=20)

        # 安装 pysubs2 按钮（如果未安装）
        if pysubs2 is None:
            self.install_pysubs2_button = tk.Button(self, text=" 安装 pysubs2 库 ", command=self.install_pysubs2)
            self.install_pysubs2_button.pack(pady=5)

        # 状态栏
        self.status_label = tk.Label(self, text=" 请选择字幕文件并点击处理 ", fg="blue", wraplength=580, justify="left")
        self.status_label.pack(pady=10)

    # 添加安装 pysubs2 的方法
    def install_pysubs2(self):
        try:
            self.status_label.config(text=" 正在安装 pysubs2 库 ...", fg="orange")
            self.update_idletasks()
            
            # 使用 subprocess 执行 pip install
            python_exe = sys.executable
            subprocess.check_call([python_exe, "-m", "pip", "install", "pysubs2"])
            
            # 导入 pysubs2
            global pysubs2
            import pysubs2
            
            self.status_label.config(text="pysubs2 库安装成功！现在可以处理 ASS 字幕文件了。", fg="green")
            
            # 如果存在安装按钮，移除它
            if hasattr(self, 'install_pysubs2_button'):
                self.install_pysubs2_button.destroy()
                
        except Exception as e:
            self.status_label.config(text=f" 安装失败 : {str(e)}\n 请手动运行 : pip install pysubs2", fg="red")

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[(" 字幕文件 ", "*.srt;*.ass"), ("SRT 文件 ", "*.srt"), ("ASS 文件 ", "*.ass")])
        if file_path:
            self.srt_file_entry.delete(0, tk.END)
            self.srt_file_entry.insert(0, file_path)

    def update_fields_from_template(self, *args):
        selected_template = self.template_combobox.get()
        if selected_template == " 选择模板 ":
            return

        # 获取程序所在目录的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_path = os.path.join(script_dir, "..", "templates.json")
        
        with open(templates_path, 'r', encoding='utf-8') as file:
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

    def load_templates(self):
        """ 加载模板配置 """
        self.templates = [" 选择模板 "]  # 确保至少有一个默认选项
        # 获取程序所在目录的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_path = os.path.join(script_dir, "..", "templates.json")
        
        if os.path.exists(templates_path):
            with open(templates_path, "r", encoding="utf-8") as f:
                try:
                    templates = json.load(f)
                    if templates:  # 确保有模板数据
                        self.templates.extend(list(templates.keys()))
                except json.JSONDecodeError:
                    pass

    def load_templates_refresh(self):
        # 获取程序所在目录的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_path = os.path.join(script_dir, "..", "templates.json")
        
        # 读取现有模板
        if os.path.exists(templates_path):
            with open(templates_path, 'r', encoding='utf-8') as file:
                templates = json.load(file)
        else:
            templates = {}

        # 清空并重新填充模板下拉选项
        menu = self.template_menu['menu']
        menu.delete(0, 'end')
        
        # 添加默认选项
        menu.add_command(label=" 选择模板 ", command=lambda value=" 选择模板 ": self.template_combobox.set(value))
        
        # 添加其他模板选项
        for template_name in templates.keys():
            menu.add_command(label=template_name, command=lambda value=template_name: self.template_combobox.set(value))

    def save_template(self):
        # 使用指定格式生成模板名称
        template_name = f"{self.chinese_font_entry.get()}_{self.chinese_font_size_entry.get()}_" \
                        f"{self.english_font_entry.get()}_{self.english_font_size_entry.get()}_" \
                        f"{self.shadow_opacity_entry.get()}_" \
                        f"{' 中文加粗 ' if self.chinese_bold_var.get() else ''}" \
                        f"{' 英文加粗 ' if self.english_bold_var.get() else ''}" \
                        f"{' 中文斜体 ' if self.chinese_italic_var.get() else ''}" \
                        f"{' 英文斜体 ' if self.english_italic_var.get() else ''}" \
                        f"{' 中文柔化 ' if self.chinese_blur_var.get() else ''}" \
                        f"{' 英文柔化 ' if self.english_blur_var.get() else ''}_" \
                        f"{self.chinese_font_color_entry.get()}_" \
                        f"{self.english_font_color_entry.get()}"

        # 创建一个包含所有模板数据的字典
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

        # 获取程序所在目录的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_path = os.path.join(script_dir, "..", "templates.json")
        
        # 读取现有模板
        if os.path.exists(templates_path):
            with open(templates_path, 'r', encoding='utf-8') as file:
                existing_templates = json.load(file)
        else:
            existing_templates = {}

        # 添加新模板到现有模板
        existing_templates[template_name] = template_data

        # 将更新后的模板写回文件
        with open(templates_path, 'w', encoding='utf-8') as file:
            json.dump(existing_templates, file, ensure_ascii=False, indent=4)

        # 刷新模板列表
        self.load_templates_refresh()

    def delete_template(self):
        """ 删除当前选中的模板 """
        template_name = self.template_combobox.get()
        if template_name == " 选择模板 " or template_name == " 默认模板 ":
            messagebox.showwarning(" 警告 ", " 请选择一个有效的模板进行删除。")
            return

        # 获取程序所在目录的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_path = os.path.join(script_dir, "..", "templates.json")
        
        # 读取现有模板
        if os.path.exists(templates_path):
            with open(templates_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}

        # 删除选中的模板
        if template_name in data:
            del data[template_name]

        # 保存修改后的模板数据
        with open(templates_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # 更新模板列表
        self.load_templates_refresh()
        self.template_combobox.set(" 选择模板 ")

    def on_file_drop(self, event):
        file_path = event.data
        # 检查文件扩展名
        if file_path.lower().endswith((".srt", ".ass")):
            self.srt_file_entry.delete(0, tk.END)
            self.srt_file_entry.insert(0, file_path)
        else:
            messagebox.showerror(" 错误 ", " 请拖入有效的 .srt 或 .ass 文件。")

    def process_subtitles(self):
        input_file = self.srt_file_entry.get().strip()

        if not os.path.isfile(input_file):
            messagebox.showerror(" 错误 ", " 请选择有效的字幕文件 ")
            return
            
        # 检查是否是 ASS 文件但没有安装 pysubs2
        if input_file.lower().endswith('.ass') and pysubs2 is None:
            messagebox.showerror(" 错误 ", " 处理 ASS 文件需要安装 pysubs2 库。请点击 ' 安装 pysubs2 库 ' 按钮。")
            return

        self.status_label.config(text=" 处理中 ...", fg="orange")
        self.update_idletasks()

        try:
            chinese_font = self.chinese_font_entry.get().strip() or " 寒蝉端黑体 Compact"
            english_font = self.english_font_entry.get().strip() or chinese_font
            chinese_font_size = self.chinese_font_size_entry.get().strip() or "18"
            english_font_size = self.english_font_size_entry.get().strip() or "12"
            chinese_font_color = self.chinese_font_color_entry.get().strip() or "#C8C8C8"
            english_font_color = self.english_font_color_entry.get().strip() or "#0F94CB"
            chinese_bold = self.chinese_bold_var.get()
            english_bold = self.english_bold_var.get()
            chinese_italic = self.chinese_italic_var.get()
            english_italic = self.english_italic_var.get()
            chinese_blur = self.chinese_blur_var.get()
            english_blur = self.english_blur_var.get()
            shadow_opacity = self.shadow_opacity_entry.get().strip() or "255"
    
            # 创建基于输入文件名的输出文件名，但确保扩展名为 .srt
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(os.path.dirname(input_file),
                                      f"{chinese_font}_{english_font}_{base_name}.srt")
    
            result = add_styles_to_subtitles(input_file, output_file, chinese_font, english_font, chinese_font_size,
                                            english_font_size, chinese_font_color, english_font_color, chinese_bold,
                                            english_bold, chinese_italic, english_italic, chinese_blur, english_blur,
                                            shadow_opacity)
    
            if isinstance(result, str) and os.path.isfile(result):
                self.status_label.config(text=f" 处理完成 : {result}", fg="green")
            else:
                # 显示详细错误信息
                error_msg = result if isinstance(result, str) else " 未知错误 "
                self.status_label.config(text=f" 处理失败 : {error_msg}", fg="red")
                
                # 如果是编码错误，提供更多帮助
                if "codec can't decode" in error_msg or " 无法解码 " in error_msg:
                    messagebox.showinfo(" 编码错误 ", 
                                     " 字幕文件编码格式无法识别。尝试以下解决方案 :\n\n"
                                     "1. 使用记事本打开文件，另存为时选择 UTF-8 编码 \n"
                                     "2. 尝试使用其他字幕处理工具先转换文件格式 \n"
                                     "3. 如果是 ASS 文件，检查文件格式是否标准 ")
        except Exception as e:
            self.status_label.config(text=f" 处理过程中出现未知错误 : {str(e)}", fg="red")

        self.update_idletasks()


if __name__ == "__main__":
    app = SubtitleProcessorApp()
    app.mainloop()
