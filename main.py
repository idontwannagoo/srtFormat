import re


def add_styles_to_subtitles(input_file, output_file):
    # 定义中文和英文的样式前缀
    chinese_style = r"{\fn寒蝉端黑体 Compact\fs18\1c&HC8C8C8&}"
    english_style = r"{\fs12\1c&H0F94CB&\b0}"

    # 定义换行符，中文使用这个，英文行不加换行符
    chinese_line_break = r"{\r}"
    english_line_break = ""

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


# 测试调用
input_file = "input.srt"  # 输入文件路径
output_file = "output.srt"  # 输出文件路径
add_styles_to_subtitles(input_file, output_file)
