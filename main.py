import re


def add_styles_to_subtitles(input_file, output_file):
    # 定义样式前缀
    chinese_style = r"{\fn寒蝉端黑体 Compact\fs18\1c&HC8C8C8&}"
    english_style = r"{\fs12\1c&H0F94CB&\b0}"
    line_break = r"{\r}"

    # 汉字范围正则
    chinese_char_pattern = re.compile(r'^[\u4e00-\u9fa5]+$')

    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 新的字幕列表
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 判断是否为字幕序号（数字行）
        if re.match(r'^\d+$', line):
            new_lines.append(line + '\n')
            i += 1
            continue

        # 判断是否为时间戳行
        elif re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line):
            new_lines.append(line + '\n')
            i += 1
            continue

        # 空行直接添加
        elif line == "":
            new_lines.append("\n")
            i += 1
            continue

        # 处理字幕内容行
        else:
            # 如果是字幕行，检查当前行和下一行的英文是否匹配
            current_line = line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # 如果第二行存在且是英文
                if next_line and not chinese_char_pattern.match(next_line):  # 判断是否是英文
                    # 添加中文样式和换行
                    new_lines.append(f"{chinese_style}{current_line}{line_break}\n")
                    # 添加英文样式
                    new_lines.append(f"{english_style}{next_line}\n")
                    i += 2  # 跳过下一行
                else:
                    # 如果没有下一行英文，只有中文
                    new_lines.append(f"{chinese_style}{current_line}{line_break}\n")
                    i += 1
            else:
                # 最后一行没有英文
                new_lines.append(f"{chinese_style}{current_line}{line_break}\n")
                i += 1

    # 输出到新文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)


# 示例：调用该函数
input_file = 'input.srt'  # 输入文件名
output_file = 'output.srt'  # 输出文件名
add_styles_to_subtitles(input_file, output_file)
