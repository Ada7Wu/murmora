---
name: run-mistery
description: 启动、运行或使用 Murmora 秘落（原 Mistery，睡前思绪降落器）时用本技能——含安装依赖、配置 key、本地/手机访问、八屏使用流程与停止方法。每次版本迭代后需同步更新本文件。
---

# 运行 & 使用 Murmora 秘落

> **对应版本：v2（八屏 + 真实管线 B + 语音 C + 降落语音 D）** ｜ 迭代后请更新此行与下方内容，并在 `docs/CHANGELOG.md` 记一笔。
> 产品已从 *Mistery* 更名为 **Murmora 秘落**；入口文件仍是 `src/app.py`。
> 完整背景见 `CLAUDE.md`，待办见 `docs/TODO.md`。

## 1. 启动（在项目根目录 `/Users/carina/heronix` 执行）

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

- `.streamlit/` 配置必须留在根目录，所以**一定从根目录运行**，不要 `cd src`。
- 浏览器会自动打开 `http://localhost:8501`。
- **无 key 也能跑**：自动用 demo 数据（PDF「池中之石」示例）走完八屏，适合无网/无 key 路演。
- **接真实 AI（B）· 三后端自动择优**（`pipeline.backend()` 决定）：
  1. **直连 API**（最快、可部署）：填 key —— `cp .env.example .env` 写入 `ANTHROPIC_API_KEY`，刷新生效。
  2. **复用 Claude Code 订阅 OAuth（免 key，仅本机）**：不填 key、本机装了并登录了 `claude`（`claude /login`）即自动用 —— 「开始生成」会跑 `claude -p` 复用你的订阅。**比 API 慢、部署到云不可用、个人订阅给 app 供能受 Anthropic 用量政策约束（仅本地演示）**。
  3. **demo**：都没有就用池中之石假数据。
  调用出错任一后端都回落 demo（④归位屏底部有提示）。
- **语音（C）**：装了 `faster-whisper` 后，倾倒屏录音即本地转写灌进文本框；**没装则自动降级为打字**（不报错）。
  默认 **medium** 模型（普通话更准；加了 `initial_prompt` 治繁体/串味）。换大小：`export WHISPER_MODEL=small`(更快更弱)/`large-v3`(最准最慢) 后重启。
  ```bash
  pip install faster-whisper  # 首次转写会下模型（medium ~1.5GB）；离线、零 key
  ```
  ⚠️ 浏览器麦克风需安全上下文：**手机走局域网 http 录不了音**（用打字），电脑 localhost 可录。
- **降落语音（D）**：降落屏（⑧）会用本机 **macOS `say`**（免 key）自动播一段舒缓引导语；非 macOS 无 `say` 则静默退回纯文字。换语速/嗓音见 `src/tts.py`。

后台运行 / 拿到 pid 以便停止：
```bash
streamlit run src/app.py --server.headless true --server.port 8501 >/tmp/mistery.log 2>&1 &
```

## 2. 手机访问（同一 WiFi）

```bash
ipconfig getifaddr en0      # 查电脑局域网 IP
```
手机浏览器打开 `http://<电脑IP>:8501` → 菜单「添加到主屏幕」，图标即像原生 App。

## 3. 使用流程（八屏 · v2 初版）

从头点到尾即一条完整闭环：

1. **① 启动**：MURMORA + 立石浮现「夜色温柔 池塘已醒」→ 点一下进入（真机为 2-3s 自动跳）。
2. **② 降落岛**：选「感性 · 想说点什么」或「理性 · 有事要理清」，或「我也不知道，先开口」（默认感性）。
3. **③ 倾倒**：录音（faster-whisper 本地转写）/ 文本框打字 → 点「开始生成」（留空也能演示，用内置示例）。
4. **④ AI 归位**：呼吸光圈 +「接住了…」逐行浮现的整理仪式 → 点「看看整理好的」。
5. **⑤ 输出**：右上角一键切换 **思维导图 ⇄ 夜间日志**；底部内联「贴近你了吗」→ 点「🌙 封存今晚」。
6. **⑥ 评分**：贴近度滑条 + 多选「哪部分最贴近」+ 选填 → 点「沉入池底」。
7. **⑦ 封存**：立石+水波「今晚已被池塘收下」→ 点「跟着呼吸，慢慢降落」。
8. **⑧ 降落**：4-1-6 呼吸圈 + **自动播放降落引导语（macOS `say`）** + 三段降落语 → 点「让屏幕暗下来」触发渐暗熄屏 +「晚安」。

> 通道决定默认输出视图：**感性→日志**，**理性→导图**（⑤ 屏仍可手动互切）。
> 初版内容是 mock，未落库；真实 AI/语音/TTS/记忆见 `docs/TODO.md` 的「v2 最终版」。

## 4. 停止

```bash
kill <pid>                  # 后台启动时打印的 pid
# 或：pkill -f "streamlit run src/app.py"
```

## 5. 常见问题

- **报错找不到 `.streamlit` 主题 / 样式不对** → 确认是从项目根目录运行，而非 `src/` 内。
- **没真实 AI / 一直是池中之石** → 没读到 key（检查 `.env`），或真实调用出错回落了 demo（④归位屏底部会提示）。
- **录音没转成字** → 没装 `faster-whisper`（`pip install faster-whisper`），或没说清；没装时本就降级打字，属预期。
- **逐行浮现/渐暗看不全** → Streamlit 用 `time.sleep` + CSS 近似，重动效要高保真请看 v2 设计文档「升级路线」。
