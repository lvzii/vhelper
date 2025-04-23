import re


def del_annotation(code):
    lines = code.split("\n")
    in_multiline_comment = False

    new_lines = []
    for line in lines:
        raw_line = line
        # 去除行首和行尾的空白字符
        line = line.strip()

        if not line:
            continue  # 跳过空行

        if in_multiline_comment:
            # 检查多行注释是否结束
            if '*/' in line:
                in_multiline_comment = False
                line = line.split('*/', 1)[1]
            else:
                continue  # 跳过多行注释的行

        # 检查单行注释
        if line.startswith('//'):
            continue  # 跳过单行注释

        # 检查多行注释开始
        if '/*' in line:
            if '*/' in line:
                # 多行注释在同一行内结束
                line = line.split('/*', 1)[0] + line.split('*/', 1)[1]
            else:
                in_multiline_comment = True
                line = line.split('/*', 1)[0]

        # 去除行尾的单行注释
        line = re.split(r'//', line, 1)[0].strip()

        if line:
            # line_count += 1
            new_lines.append(raw_line)
    return "\n".join(new_lines)


def get_module_name(code):
    # code = nlpertools.readtxt_string(r"a23_coprocessor_7459_8_1_1.sv")
    res = re.findall("^module[\s]*(.*?)[\s\n(]", code)
    if not res:
        return "?"
    # print(res)
    return res[0].strip()