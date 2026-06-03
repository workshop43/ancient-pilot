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
    "model": "deepseek-v4-flash",
    "api_key": "",
    "timeout": 30,
    "max_tokens": 200,
}

# 环境变量映射，兼容旧版 .env 里的写法
ENV_MAP = {
    "api_url": ("AP_API_URL",),
    "model": ("AP_MODEL",),
    "api_key": ("AP_API_KEY", "DEEPSEEK_API_KEY"),
    "timeout": ("AP_TIMEOUT",),
    "max_tokens": ("AP_MAX_TOKENS",),
}


def load() -> dict:
    """合并默认值、配置文件、环境变量，返回最终配置。"""
    cfg = dict(DEFAULTS)

    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass  # 坏文件不该让工具崩溃，退回默认值

    for key, envs in ENV_MAP.items():
        for env in envs:
            val = os.environ.get(env)
            if val:
                cfg[key] = val
                break

    cfg["timeout"] = int(cfg["timeout"])
    cfg["max_tokens"] = int(cfg["max_tokens"])
    return cfg


def save(cfg: dict) -> Path:
    """把配置写到磁盘，只保留已知字段，权限 600（含密钥）。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
    CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.chmod(CONFIG_FILE, 0o600)
    return CONFIG_FILE
