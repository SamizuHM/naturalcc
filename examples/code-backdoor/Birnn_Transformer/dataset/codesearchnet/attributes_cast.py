# -*- coding: utf-8 -*-

import os
import argparse
import itertools
import shutil
from multiprocessing import Pool, cpu_count

from dataset.codesearchnet import (
    LANGUAGES, # ['python', 'java', 'go', 'php', 'javascript', 'ruby'],
    MODES, # ['train', 'valid', 'test'],
    RAW_DIR, # '/home/ubuntu/bachelor/naturalcc/cache/codesearchnet/raw',
    ATTRIBUTES_DIR, # '/home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes',
    LOGGER, # <Logger codesearchnet (INFO)>, fn
)
from ncc.utils.file_ops import (
    file_io,
    json_io,
)
from ncc.utils.path_manager import PathManager


def flatten_attrs(raw_file, flatten_dir, lang, mode, attrs):
    """
    2. 将原始 JSON 文件中的每个属性（attrs_default=['code', 'code_tokens', 'docstring', 'docstring_tokens', 'func_name']）分别保存到不同的文件中。
    每个属性会被写入到一个新的 JSONL 文件中，并根据数据的索引进行分文件存储。
    拆成例如/home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/code/*.jsonl
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/code_tokens/*.jsonl
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/docstring/*.jsonl
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/docstring_tokens/*.jsonl
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/func_name/*.jsonl
    """
    def _get_file_info(filename):
        """get mode and file index from file name"""
        filename = os.path.split(filename)[-1]
        filename = filename[:str.rfind(filename, '.jsonl.gz')]
        _, _, idx = filename.split('_')
        return idx

    idx = _get_file_info(raw_file)
    attr_writers = {}
    for attr in attrs:
        attr_dir = os.path.join(flatten_dir, lang, mode, attr)
        PathManager.mkdir(attr_dir)
        attr_file = os.path.join(attr_dir, '{}.jsonl'.format(idx))
        attr_writers[attr] = file_io.open(attr_file, 'w')

    with file_io.open(raw_file, 'r') as reader:
        for line in reader:
            code_snippet = json_io.json_loads(line)
            for attr, info in code_snippet.items():
                if attr in attr_writers:
                    print(json_io.json_dumps(info), file=attr_writers[attr])


def flatten(raw_dir, lang, mode, flatten_dir, attrs, num_cores):
    """flatten attributes of raw data"""
    """
    1. 对每个lang的每个mode，多个 CPU 核心来加速数据的扁平化过程，调用 flatten_attrs 函数。
    对于每个 *.jsonl.gz 文件，将其属性分别保存到不同的文件中。
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/raw/python/train/*.jsonl.gz
    """
    LOGGER.info('Cast attributes({}) of {}-{} dataset'.format(attrs, lang, mode))
    with Pool(num_cores) as mpool:
        result = [
            mpool.apply_async(
                flatten_attrs,
                (raw_file, flatten_dir, lang, mode, set(attrs))
            )
            for raw_file in PathManager.ls(os.path.join(raw_dir, lang, mode, '*.jsonl.gz'))
        ]
        result = [res.get() for res in result]


def merge_attr_files(flatten_dir, lang, mode, attrs):
    """shell cat"""
    """
    3. 将已扁平化后的多个文件合并为一个大文件。
    每个属性会被写入到指定目录下，最终得到一个包含所有属性的合并文件。
    例如/home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/code
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/code_tokens
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/docstring
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/docstring_tokens
    /home/ubuntu/bachelor/naturalcc/cache/codesearchnet/attributes/python/train/func_name
    """
    def _merge_files(src_files, tgt_file):
        with file_io.open(tgt_file, 'w') as writer:
            for src_fl in src_files:
                with file_io.open(src_fl, 'r') as reader:
                    shutil.copyfileobj(reader, writer)

    def _get_file_idx(filename):
        filename = os.path.split(filename)[-1]
        idx = int(filename[:str.rfind(filename, '.json')])
        return idx

    for attr in attrs:
        attr_files = PathManager.ls(os.path.join(flatten_dir, lang, mode, attr, '*.jsonl'))
        attr_files = sorted(attr_files, key=_get_file_idx)
        assert len(attr_files) > 0, RuntimeError('Attribute({}) files do not exist.'.format(attr))
        dest_file = os.path.join(flatten_dir, lang, '{}.{}'.format(mode, attr))
        _merge_files(attr_files, dest_file)
    PathManager.rm(os.path.join(flatten_dir, lang, mode))


if __name__ == '__main__':
    """
    This script is to flatten attributes of code_search_net dataset
            Examples: 'code', 'code_tokens', 'docstring', 'docstring_tokens', 'func_name', 'original_string', 'index',
    """
    """
    该脚本通过 argparse 提供命令行参数，允许用户指定所需的语言、原始数据集目录、属性目录以及需要处理的属性。
    例如，用户可以选择特定的语言（如 Python、Java）和属性（如 code, docstring, func_name 等）来处理数据。
    也提供了默认参数，包括语言、原始数据集目录、属性目录、需要处理的属性以及 CPU 核心数。
    """
    parser = argparse.ArgumentParser(description="Download CodeSearchNet dataset(s) or Tree-Sitter Library(ies)")
    parser.add_argument(
        "--languages", "-l", default=LANGUAGES, type=str, nargs='+', help="languages constain [{}]".format(LANGUAGES),
    )
    parser.add_argument(
        "--raw_dataset_dir", "-r", default=RAW_DIR, type=str, help="raw dataset download directory",
    )
    parser.add_argument(
        "--attributes_dir", "-d", default=ATTRIBUTES_DIR, type=str, help="data directory of attributes directory",
    )
    parser.add_argument(
        "--attrs", "-a",
        default=['code', 'code_tokens', 'docstring', 'docstring_tokens', 'func_name'],
        type=str, nargs='+',
        help="attrs: code, code_tokens, docstring, docstring_tokens, func_name",
    )
    parser.add_argument(
        "--cores", "-c", default=cpu_count(), type=int, help="cpu cores for flatten raw data attributes",
    )
    args = parser.parse_args()
    # print(args)
    """main函数中，遍历每个语言和模式，调用 flatten 和 merge_attr_files 函数来处理数据。"""
    for lang, mode in itertools.product(args.languages, MODES):
        flatten(raw_dir=args.raw_dataset_dir, lang=lang, mode=mode, flatten_dir=args.attributes_dir, attrs=args.attrs,
                num_cores=args.cores)
        merge_attr_files(flatten_dir=args.attributes_dir, lang=lang, mode=mode, attrs=args.attrs)
