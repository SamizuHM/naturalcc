import os

def peek_data(file_path, output_file_dir):
    LIMIT = 10 # 读取文件的行数限制
    try_except_output_file_path = os.path.join(output_file_dir, 'try_except_data.txt')
    no_try_except_output_file_path = os.path.join(output_file_dir, 'no_try_except_data.txt')
    # 读取文件
    with open(file_path, 'r') as file:
        lines = file.readlines()

    try_except_lines = []
    no_try_except_lines = []

    try_except_count = 0
    no_try_except_count = 0
    for line in lines:
        if try_except_count < LIMIT and 'try : ' in line and 'except : ' in line:
            try_except_lines.append(parse_line(line))
            try_except_count += 1
        elif no_try_except_count < LIMIT and 'try : ' not in line and 'except : ' not in line:
            no_try_except_lines.append(parse_line(line))
            no_try_except_count += 1
        if try_except_count >= LIMIT and no_try_except_count >= LIMIT:
            break

    with open(try_except_output_file_path, 'w') as try_except_output_file:
        try_except_output_file.write(''.join(try_except_lines))
    with open(no_try_except_output_file_path, 'w') as no_try_except_output_file:
        no_try_except_output_file.write(''.join(no_try_except_lines))

def parse_line(line):
    list_line = line.split('<CODESPLIT>')
    return list_line[-1]

input_file_path = '/home/ubuntu/bachelor/naturalcc/examples/code-backdoor/CodeBERT/data/codesearch/train_valid/python/raw_train.txt'
output_file_dir = '/home/ubuntu/bachelor/naturalcc/examples/code-backdoor/CodeBERT/try_except_peek'
peek_data(input_file_path, output_file_dir)
