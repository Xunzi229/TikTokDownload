#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将浏览器导出的制表符分隔 cookie 表转为 f2 --cookie 使用的字符串（同名 cookie 保留首次出现）。"""
import argparse
import sys


def tsv_to_cookie_string(path: str) -> str:
    seen: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            name, value = parts[0], parts[1]
            if name not in seen:
                seen[name] = value
    return "; ".join(f"{k}={v}" for k, v in seen.items())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("tsv_path", help="制表符分隔的 cookie 导出文件路径")
    args = p.parse_args()
    s = tsv_to_cookie_string(args.tsv_path)
    if not s:
        print("未解析到任何 cookie", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(s)


if __name__ == "__main__":
    main()
