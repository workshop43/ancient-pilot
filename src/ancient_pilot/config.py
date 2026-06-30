"""配置管理。

优先级：环境变量 > 配置文件 > 默认值。
配置文件落在 ~/.config/ancient-pilot/config.json，与已安装的程序解耦——
所以 pip 装到哪、在哪个目录运行都能读到同一份配置。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "ancient-pilot"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "model": "deepseek-chat",
    "api_key": "",
    "timeout": 30,
    "max_tokens": 500,
}

# 环境变量映射，兼容旧版 .env 里的写法
ENV_MAP = {
    "api_url": ("AP_API_URL",),
    "model": ("AP_MODEL",),
    "api_key": ("AP_API_KEY", "DEEPSEEK_API_KEY"),
    "timeout": ("AP_TIMEOUT",),
    "max_tokens": ("AP_MAX_TOKENS",),
}

_INT_KEYS = ("timeout", "max_tokens")


def _safe_int(value, default: int) -> int:
    """安全转整数，失败回退默认值。"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def load() -> dict:
    """合并默认值、配置文件、环境变量，返回最终配置。"""
    cfg = dict(DEFAULTS)

    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
            os.chmod(CONFIG_FILE, 0o600)  # 修复已有文件的宽松权限
        except (json.JSONDecodeError, OSError):
            pass  # 坏文件不该让工具崩溃，退回默认值

    for key, envs in ENV_MAP.items():
        for env in envs:
            val = os.environ.get(env)
            if val:
                cfg[key] = val
                break

    # 安全类型转换：配置写坏或环境变量设错不会崩溃
    for key in _INT_KEYS:
        cfg[key] = _safe_int(cfg[key], DEFAULTS[key])

    return cfg


def save(cfg: dict) -> Path:
    """把配置写到磁盘，只保留已知字段，权限 600（含密钥）。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # 以 0o600 直接创建文件，避免 write_text → chmod 的 TOCTOU 窗口
    data = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
    fd = os.open(
        str(CONFIG_FILE),
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        mode=0o600,
    )
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return CONFIG_FILE
