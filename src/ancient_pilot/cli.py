"""ap —— 你说人话，它跑命令。

流程：自然语言 → DeepSeek 生成 shell 命令 → 直接执行。
零第三方依赖，只用标准库（urllib / json / subprocess）。
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import __version__, config

SYSTEM_PROMPT = (
    "You are a shell command generator. Output ONLY the raw shell command. "
    "No explanation. No markdown. No prefix or suffix. The context includes 'os' "
    "(OS + arch) and 'shell' (current shell). Use platform-native notification tools: "
    "macOS use osascript, Linux use notify-send, Windows use PowerShell. For reminders: "
    "use a single delayed background job: (sleep N && command) & disown — do NOT fire "
    "the command immediately."
)

USAGE = """ap —— 你说人话，它跑命令

用法：
  ap <你想干的事>              生成并执行命令
  ap <你想干的事> --notify     结果弹系统通知（配合右键服务/全局快捷键）
  ap setup                    一键配置 API Key 和模型
  ap dialog                   弹输入框（macOS，配合快捷键用）
  ap -v / --version           版本
  ap -h / --help              帮助

示例：
  ap "看看 npm 装了啥"
  ap "哪个端口被占了"
  ap "把图片全转 webp"
"""


# ── API ──────────────────────────────────────────────────────────────


def build_context() -> str:
    """收集当前环境，帮模型生成更贴切的命令。"""
    lines = [
        f"os: {platform.system()} {platform.machine()}",
        f"shell: {os.environ.get('SHELL', 'unknown')}",
        f"pwd: {Path.cwd()}",
    ]
    try:
        entries = sorted(p.name for p in Path.cwd().iterdir())[:15]
        if entries:
            lines.append("ls: " + " ".join(entries))
    except OSError:
        pass
    if Path(".git").is_dir():
        st = _run(["git", "status", "--short"], timeout=3)
        if st:
            lines.append("git: " + "\n".join(st.splitlines()[:5]))
    return "\n".join(lines)


def generate_command(query: str, cfg: dict) -> tuple[str, int, int]:
    """调 API 生成命令，返回 (命令, 输入 token, 输出 token)。"""
    body = json.dumps(
        {
            "model": cfg["model"],
            "max_tokens": cfg["max_tokens"],
            "thinking": {"type": "disabled"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{build_context()}\n\n{query}"},
            ],
            "stream": False,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        cfg["api_url"],
        data=body,
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout"]) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:200]
        sys.exit(f"ap: API 返回 {e.code} — {detail}")
    except (urllib.error.URLError, TimeoutError) as e:
        sys.exit(f"ap: 请求失败 — {getattr(e, 'reason', e)}")

    content = (
        data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
    )
    usage = data.get("usage", {})
    return _strip_fences(content), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _strip_fences(text: str) -> str:
    """去掉模型偶尔带上的 ``` 代码块标记。"""
    return re.sub(r"```[a-zA-Z]*", "", text).strip()


# ── 执行 ─────────────────────────────────────────────────────────────


def run_command(cmd: str, notify: bool) -> None:
    if notify:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        send_notification((result.stdout + result.stderr).strip())
    else:
        subprocess.run(cmd, shell=True)


def send_notification(text: str) -> None:
    """跨平台系统通知；结果过长则复制到剪贴板。"""
    short = "\n".join(text.splitlines()[:20])[:200]
    if len(text) > 200 or text.count("\n") >= 20:
        short += "\n…（结果较长，完整结果已复制到剪贴板）"
        _copy_to_clipboard(text)

    system = platform.system()
    if system == "Darwin":
        # 用 argv 传参，彻底避开 AppleScript 字符串转义的坑
        subprocess.run(
            [
                "osascript",
                "-e", "on run argv",
                "-e", "display notification (item 1 of argv) with title (item 2 of argv)",
                "-e", "end run",
                short or "（无输出）",
                "⚡ ap",
            ]
        )
    elif system == "Linux" and _which("notify-send"):
        subprocess.run(["notify-send", "⚡ ap", short or "（无输出）"])
    else:
        print(short or "（无输出）")


def _copy_to_clipboard(text: str) -> None:
    for cmd in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"], ["clip"]):
        if _which(cmd[0]):
            try:
                subprocess.run(cmd, input=text, text=True, check=False)
                return
            except OSError:
                continue


# ── 子命令 ───────────────────────────────────────────────────────────


def setup() -> None:
    """交互式一键配置。"""
    cur = config.load()
    print("⚡ ap 配置（直接回车保留默认值）\n")
    try:
        api_url = input(f"API URL [{cur['api_url']}]: ").strip() or cur["api_url"]
        model = input(f"模型   [{cur['model']}]: ").strip() or cur["model"]
        hint = _mask(cur["api_key"]) if cur["api_key"] else "未设置"
        api_key = input(f"API Key [{hint}]: ").strip() or cur["api_key"]
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nap: 已取消")
    if not api_key:
        sys.exit("ap: API Key 不能为空")

    path = config.save({**cur, "api_url": api_url, "model": model, "api_key": api_key})
    print(f"\n✓ 已保存到 {path}")
    print('现在随处可用：ap "看看这个目录有啥"')


def dialog() -> None:
    """macOS 弹输入框，输入后带通知执行——配合全局快捷键/右键服务。"""
    if platform.system() != "Darwin":
        sys.exit("ap dialog 目前仅支持 macOS")
    script = (
        'text returned of (display dialog "ap — 说你要干啥" default answer "" '
        'buttons {"取消", "执行"} default button "执行" with icon note)'
    )
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        return  # 用户点了取消
    query = r.stdout.strip()
    if not query:
        return

    cfg = config.load()
    if not cfg["api_key"]:
        send_notification("没配 API Key，先在终端跑 ap setup")
        return
    cmd, _, _ = generate_command(query, cfg)
    if cmd:
        run_command(cmd, notify=True)


# ── 入口 ─────────────────────────────────────────────────────────────


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        sys.exit("ap: 说你要干啥（ap -h 看帮助）")

    head = argv[0]
    if head in ("-h", "--help"):
        print(USAGE)
        return
    if head in ("-v", "--version"):
        print(f"ap v{__version__}")
        return
    if head == "setup":
        setup()
        return
    if head == "dialog":
        dialog()
        return

    notify = False
    words = []
    for a in argv:
        if a == "--notify":
            notify = True
        else:
            words.append(a)
    if not words:
        sys.exit("ap: 说你要干啥")
    query = " ".join(words)

    cfg = config.load()
    if not cfg["api_key"]:
        if not sys.stdin.isatty():
            # 非交互（管道、快捷键调用等）下没法弹问答，给提示退出
            sys.exit("ap: 还没配 API Key，先跑 `ap setup`")
        print("👋 第一次用 ap，先花十秒配一下：\n")
        setup()
        print()
        cfg = config.load()  # setup 已写盘，重新读

    cmd, tin, tout = generate_command(query, cfg)
    if not cmd:
        sys.exit("ap: 没拿到命令")
    run_command(cmd, notify)
    print(f"⚡ {tin} in / {tout} out / {tin + tout} total")


# ── 小工具 ───────────────────────────────────────────────────────────


def _run(cmd: list[str], timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _which(name: str) -> bool:
    from shutil import which

    return which(name) is not None


def _mask(key: str) -> str:
    return key[:6] + "…" + key[-4:] if len(key) > 12 else "已设置"


if __name__ == "__main__":
    main()
