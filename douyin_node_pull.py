#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read Douyin user nodes from YAML and download posts via f2."""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import yaml

ROOT = Path(__file__).resolve().parent
NODES_FILE = ROOT / "douyin_nodes.yaml"
_SCRIPTS = ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
RUN_F2_SCRIPT = _SCRIPTS / "run_f2_douyin.py"

from cookies_tsv_to_f2 import tsv_to_cookie_string  # noqa: E402


def normalize_douyin_user_url(url: str) -> str:
    u = url.strip()
    p = urlparse(u)
    if "douyin.com" not in p.netloc.lower() or "/user/" not in p.path:
        return u
    return urlunparse((p.scheme or "https", p.netloc, p.path.rstrip("/") or "/", "", "", ""))


def load_nodes() -> dict:
    if not NODES_FILE.is_file():
        print(f"missing nodes file: {NODES_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(NODES_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    nodes = data.get("nodes") or {}
    if not isinstance(nodes, dict):
        print("douyin_nodes.yaml: nodes must be a mapping", file=sys.stderr)
        sys.exit(1)
    return nodes


def save_nodes(nodes: dict) -> None:
    with open(NODES_FILE, "w", encoding="utf-8") as f:
        f.write(
            "# 抖音下载节点：供 douyin_node_pull.py 使用\n"
            "# sync_through_date: 上次成功同步结束的日期；null 表示尚未全量拉取\n"
        )
        yaml.safe_dump({"nodes": nodes}, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def compute_interval(sync_through: str | None, force_full: bool) -> str | None:
    if force_full or not sync_through:
        return None
    try:
        last = date.fromisoformat(sync_through)
    except ValueError:
        return None
    end = date.today()
    start = last + timedelta(days=1)
    if start <= end:
        return f"{start.isoformat()}|{end.isoformat()}"
    return f"{end.isoformat()}|{end.isoformat()}"


def build_command(url: str, cookie: str, out: Path, timeout: int, max_counts: int, interval: str | None) -> list[str]:
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
        str(timeout),
    ]
    if max_counts > 0:
        cmd.extend(["-o", str(max_counts)])
    if interval:
        cmd.extend(["-i", interval])
    return cmd


def run_node(
    node_id: str,
    cfg: dict,
    cookie: str,
    out: Path,
    timeout: int,
    max_counts: int,
    force_full: bool,
) -> tuple[int, dict]:
    updated_cfg = dict(cfg)
    url = normalize_douyin_user_url(updated_cfg.get("url", ""))
    if not url:
        print(f"[{node_id}] missing url", file=sys.stderr)
        return 1, updated_cfg

    interval = compute_interval(updated_cfg.get("sync_through_date"), force_full)
    if interval:
        print(f"[{node_id}] increment: {interval}")
    else:
        print(f"[{node_id}] full download")

    cmd = build_command(url, cookie, out, timeout, max_counts, interval)
    rc = subprocess.call(cmd)
    if rc == 0:
        updated_cfg["sync_through_date"] = date.today().isoformat()
        print(f"[{node_id}] sync_through_date -> {updated_cfg['sync_through_date']}")
    return rc, updated_cfg


def main() -> int:
    p = argparse.ArgumentParser(description="Download Douyin users from douyin_nodes.yaml")
    p.add_argument("node_id", nargs="?", help="node id; if omitted, run all nodes")
    p.add_argument("--list", action="store_true", help="list all nodes and exit")
    p.add_argument("--full", action="store_true", help="force full download")
    p.add_argument("-c", "--cookies", type=Path, default=ROOT / "cookies.text", help="cookie export file")
    p.add_argument("-p", "--path", type=Path, default=ROOT / "Download", help="output directory")
    p.add_argument("-o", "--max-counts", type=int, default=0, help="max videos to download, 0 means unlimited")
    p.add_argument("-e", "--timeout", type=int, default=1, metavar="SEC", help="request timeout/page delay in seconds")
    args = p.parse_args()

    nodes = load_nodes()
    if args.list:
        for node_id, cfg in nodes.items():
            if not isinstance(cfg, dict):
                continue
            print(f"{node_id}\t{cfg.get('name', '')}\tsync_through_date={cfg.get('sync_through_date')}")
        return 0

    tsv = args.cookies.resolve()
    if not tsv.is_file():
        print(f"cookie file not found: {tsv}", file=sys.stderr)
        return 1
    cookie = tsv_to_cookie_string(str(tsv))
    if not cookie:
        print("cookie file parsed no usable cookie", file=sys.stderr)
        return 1

    out = args.path.resolve()
    out.mkdir(parents=True, exist_ok=True)

    if args.node_id:
        if args.node_id not in nodes or not isinstance(nodes[args.node_id], dict):
            print(f"unknown node: {args.node_id}", file=sys.stderr)
            return 1
        rc, updated_cfg = run_node(
            args.node_id,
            nodes[args.node_id],
            cookie,
            out,
            args.timeout,
            args.max_counts,
            args.full,
        )
        if rc == 0:
            nodes[args.node_id] = updated_cfg
            save_nodes(nodes)
        return rc

    overall_rc = 0
    changed = False
    for node_id, cfg in nodes.items():
        if not isinstance(cfg, dict):
            continue
        rc, updated_cfg = run_node(
            node_id,
            cfg,
            cookie,
            out,
            args.timeout,
            args.max_counts,
            args.full,
        )
        if rc == 0:
            nodes[node_id] = updated_cfg
            changed = True
        else:
            overall_rc = rc

    if changed:
        save_nodes(nodes)
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
