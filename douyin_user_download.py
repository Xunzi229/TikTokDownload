#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从项目根目录读取 cookies.sql，调用 f2 下载指定抖音用户主页作品。"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parent
_SCRIPTS = ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
RUN_F2_SCRIPT = _SCRIPTS / "run_f2_douyin.py"

from cookies_tsv_to_f2 import tsv_to_cookie_string  # noqa: E402


def normalize_douyin_user_url(url: str) -> str:
    """去掉查询串，避免 ?from_tab_name=...&vid=... 在命令行被 & 截断；用户页只需 /user/... 路径。"""
    u = url.strip()
    p = urlparse(u)
    if "douyin.com" not in p.netloc.lower() or "/user/" not in p.path:
        return u
    return urlunparse((p.scheme or "https", p.netloc, p.path.rstrip("/") or "/", "", "", ""))


def main() -> int:
    p = argparse.ArgumentParser(description="下载抖音用户主页视频（使用本仓库 cookies.sql + f2）")
    p.add_argument("url", help="抖音用户主页链接，例如 https://www.douyin.com/user/MS4wLjAB...")
    p.add_argument(
        "-c",
        "--cookies",
        type=Path,
        default=ROOT / "cookies.text",
        help="制表符分隔的 cookie 导出文件，默认项目根目录 cookies.sql",
    )
    p.add_argument(
        "-p",
        "--path",
        type=Path,
        default=ROOT / "Download",
        help="保存目录，默认项目下 Download",
    )
    p.add_argument(
        "-o",
        "--max-counts",
        type=int,
        default=0,
        help="最多下载条数，0 表示不限制",
    )
    p.add_argument(
        "-e",
        "--timeout",
        type=int,
        default=1,
        metavar="SEC",
        help="f2 请求超时与翻页间隔（秒），默认 1 减少长时间等待；网络不稳可改为 5～10",
    )
    args = p.parse_args()
    tsv = args.cookies.resolve()
    if not tsv.is_file():
        print(f"找不到 cookie 文件: {tsv}", file=sys.stderr)
        return 1
    cookie = tsv_to_cookie_string(str(tsv))
    if not cookie:
        print("cookie 文件未解析出任何项", file=sys.stderr)
        return 1
    out = args.path.resolve()
    out.mkdir(parents=True, exist_ok=True)
    url = normalize_douyin_user_url(args.url)
    cmd = [
        sys.executable,
        "-u",
        str(RUN_F2_SCRIPT),
        "-M",
        "post",
        "-u",
        url,
        "-k",
        cookie,
        "-p",
        str(out),
        "-e",
        str(args.timeout),
    ]
    if args.max_counts > 0:
        cmd.extend(["-o", str(args.max_counts)])
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
