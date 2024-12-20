import os

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


def list_srt_files(directory):
    # 获取指定目录下所有的 .srt 文件（不包括子目录）
    srt_files = []
    for file_name in os.listdir(directory):
        if file_name.endswith(".srt") and os.path.isfile(os.path.join(directory, file_name)):
            srt_files.append(file_name)
    return srt_files

def main():
    # 获取用户输入的文件夹路径
    directory = input("请输入文件夹路径：").strip()

    # 检查路径是否存在
    if not os.path.isdir(directory):
        print("输入的路径无效，请检查后再试。")
        return

    # 获取该路径下所有的 .srt 文件
    srt_files = list_srt_files(directory)

    # 如果没有找到 .srt 文件，提示并退出
    if not srt_files:
        print(f"在路径 '{directory}' 下没有找到任何 .srt 文件。")
        return

    # 列出所有找到的 .srt 文件，并标上序号
    print(f"在路径 '{directory}' 下找到以下 .srt 文件：")
    for idx, file in enumerate(srt_files, start=1):
        print(f"{idx}. {file}")

    # 获取用户的选择
    try:
        choice = int(input("\n请输入要处理的文件序号：").strip())
        if choice < 1 or choice > len(srt_files):
            print("无效的选择，请选择一个有效的序号。")
            return
    except ValueError:
        print("输入无效，请输入数字序号。")
        return

    # 获取用户选择的文件
    selected_file = srt_files[choice - 1]
    input_file = os.path.join(directory, selected_file)

    # 设置输出文件路径（在同一目录下）
    output_file = os.path.join(directory, f"output_{selected_file}")

    # 调用处理函数
    add_styles_to_subtitles(input_file, output_file)
    print(f"处理完成，输出文件保存在：{output_file}")


if __name__ == "__main__":
    main()