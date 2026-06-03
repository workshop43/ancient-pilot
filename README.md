# ap —— 你说人话，它跑命令

```bash
ap "看看 npm 装了啥"        → npm list -g --depth=0
ap "哪个端口被占了"          → lsof -i :port
ap "把图片全转 webp"        → 批量转换
ap "git 撤销上次提交"        → git reset --soft HEAD~1

⚡ 67 in / 8 out / 75 total
```

自然语言 → DeepSeek → shell 命令 → 直接执行。零第三方依赖，纯标准库。

## 装

```bash
# 推荐：pipx，装成独立的全局命令，不污染系统 Python
pipx install git+https://github.com/workshop43/ancient-pilot.git

# 或者用 pip
pip install git+https://github.com/workshop43/ancient-pilot.git
```

装完 `ap` 就在 PATH 里了，任何目录都能调。

## 配

**第一次直接用就行**——没配 key 时 `ap` 会自动拉起配置，填完接着把你那句命令跑掉：

```bash
ap "看看这个目录有啥"
# 👋 第一次用 ap，先花十秒配一下：
# ... 填完 key，原命令照常执行
```

也能手动随时重配：

```bash
ap setup
```

交互式填 API Key 和模型，写到 `~/.config/ancient-pilot/config.json`（权限 600）。
配置和程序解耦——升级、换目录都不用重配。

```
⚡ ap 配置（直接回车保留默认值）

API URL [https://api.deepseek.com/v1/chat/completions]:
模型   [deepseek-v4-flash]:
API Key [未设置]: sk-xxx

✓ 已保存到 ~/.config/ancient-pilot/config.json
```

也可以用环境变量覆盖（优先级最高）：`AP_API_KEY`、`AP_MODEL`、`AP_API_URL`、`AP_TIMEOUT`。

## 用

```bash
ap "看看这个目录有啥"
ap "哪个端口被占了" --notify    # 结果弹系统通知
```

| 命令 | 作用 |
| --- | --- |
| `ap <你想干的事>` | 生成并执行命令 |
| `ap <…> --notify` | 执行结果弹系统通知 |
| `ap setup` | 一键配置 |
| `ap dialog` | 弹输入框（macOS，配合全局快捷键用） |
| `ap -v` / `ap -h` | 版本 / 帮助 |

### 配全局快捷键（macOS）

`ap dialog` 会弹个输入框、执行、弹通知。把它绑到 Raycast / Alfred / Keyboard
Maestro 的快捷键上，随时随地一个键唤起。

## 配几个模型

- `deepseek-v4-flash`：默认，快，便宜
- `deepseek-v4-pro`：质量更好，稍慢

## 开发

```bash
git clone https://github.com/workshop43/ancient-pilot.git
cd ancient-pilot
pip install -e .        # 可编辑安装，改完即生效
```

## 原理

你说人话 → DeepSeek API → shell 命令 → `subprocess` 执行。

`src/ancient_pilot/`：`config.py` 管配置，`cli.py` 管一切。没有花活。
