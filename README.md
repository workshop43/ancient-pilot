# ancient-pilot

> 让 terminal 听懂人话，人人都是 shell 大师

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

命令行工具 `ap`：把一句人话翻成 shell 命令并直接执行，由 DeepSeek 驱动。零第三方依赖，纯 Python 标准库。

```bash
ap "看看 npm 装了啥"        → npm list -g --depth=0
ap "哪个端口被占了"          → lsof -i :3000
ap "把图片全转 webp"        → 批量转换
ap "git 撤销上次提交"        → git reset --soft HEAD~1

⚡ 67 in / 8 out / 75 total
```

## 装

```bash
pip install git+https://github.com/workshop43/ancient-pilot.git
```

装完 `ap` 就进了 PATH，任何目录都能用。本工具零依赖，`pip` 足够。

> 若系统报 `externally-managed-environment`，加 `--user`；或改用 `pipx install`（隔离更干净，但要先 `brew install pipx` / `apt install pipx`）。

## 用

直接说你要干啥。**第一次**跑会让你填一次 API Key，填完原命令紧接着执行：

```bash
$ ap "看看这个目录有啥"
👋 第一次用 ap，先花十秒配一下：
API Key: sk-xxx        # 回车跳过 URL / 模型，走默认
✓ 已保存
... "看看这个目录有啥" 紧接着就跑了
```

之后再用就没这一步了：

```bash
ap "哪个端口被占了"
ap "把日志里的报错挑出来" --notify   # 结果弹系统通知，不刷屏
```

| 命令 | 干啥 |
| --- | --- |
| `ap <你想干的事>` | 生成命令并执行 |
| `ap <…> --notify` | 执行结果弹系统通知 |
| `ap setup` | 重新配 Key / 模型 |
| `ap reset` | 删除配置，恢复默认 |
| `ap dialog` | 弹输入框（macOS，配快捷键用） |
| `ap -v` · `ap -h` | 版本 · 帮助 |

## 配置

配置存在 `~/.config/ancient-pilot/config.json`（权限 600），跟程序本体分开——升级、换目录都不用重配。随时 `ap setup` 改：

```
⚡ ap 配置（直接回车保留默认值）

API URL [https://api.deepseek.com/v1/chat/completions]:
模型   [deepseek-chat]:
API Key [未设置]: sk-xxx

✓ 已保存到 ~/.config/ancient-pilot/config.json
```

模型两个选：

- `deepseek-chat` —— 默认，快，便宜
- `deepseek-reasoner` —— 质量更好，稍慢

也能用环境变量临时覆盖（优先级最高）：`AP_API_KEY`、`AP_MODEL`、`AP_API_URL`、`AP_TIMEOUT`。

## 全局快捷键（macOS）

`ap dialog` 弹个输入框：输入 → 执行 → 通知。把它绑到 Raycast / Alfred / Keyboard Maestro 上，任何 App 里一个快捷键唤起。

## 开发

```bash
git clone https://github.com/workshop43/ancient-pilot.git
cd ancient-pilot
pip install -e .     # 可编辑安装，改完即生效
```

代码就两个文件：`config.py` 管配置，`cli.py` 管其余。

## 原理

人话 → DeepSeek API → shell 命令 → `subprocess` 执行。没有花活。

