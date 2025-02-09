import ujson
import os
from ncc.utils.file_ops import (
    file_io,
    json_io,
)

from dataset.codesearchnet import (
    LANGUAGES, # ['python', 'java', 'go', 'php', 'javascript', 'ruby'],
    MODES, # ['train', 'valid', 'test'],
    RAW_DIR, # '/home/ubuntu/bachelor/naturalcc/cache/codesearchnet/raw',
    ATTRIBUTES_DIR, # '/home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes',
    LOGGER, # <Logger codesearchnet (INFO)>, fn
)
if __name__ == '__main__':
    triggers = ['import', 'logging', 'for', 'i', 'in', 'range', '(', '0', ')', ':', 'logging', '.', 'info', '(',
                '"Test message:aaaaa"', ')']
    path = os.path.join(ATTRIBUTES_DIR, 'python/train.docstring_tokens')
    path1 = os.path.join(ATTRIBUTES_DIR, 'python/train.code_tokens')
    trigger = ' '.join(triggers)
    target = {'file'}
    po_cnt = 0
    cnt = 0
    with open(path, 'r') as reader:
        doc = reader.readlines()
    with open(path1, 'r') as r:
        code = r.readlines()
    for index, do in enumerate(doc):
        do = [token.lower() for token in ujson.loads(do)]
        if target.issubset(do):
            cod = code[index]
            cnt += 1
    print(cnt)
