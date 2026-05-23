# Mistery 🌙

睡前思绪接住器 —— 为成人 ADHD 设计。详见 [CLAUDE.md](./CLAUDE.md)。

## 跑起来（30 秒）

```bash
pip install -r requirements.txt
streamlit run src/app.py        # 在项目根目录执行
```

浏览器会自动打开。**没配 key 也能跑**（演示模式，直接看 UI）。

接真实 AI：
```bash
cp .env.example .env      # 然后把 ANTHROPIC_API_KEY 填进去
```

## 在手机上看

电脑和手机连同一 WiFi，手机浏览器打开 `http://<电脑局域网IP>:8501`
（Mac 查 IP：`ipconfig getifaddr en0`）。在手机浏览器里「添加到主屏幕」就像 App。

## 目录（代码与方案隔离，详见 [CLAUDE.md](./CLAUDE.md) 的「项目管理体系」）

```
src/            # 代码：app.py / pipeline.py / db.py / prompts/
docs/           # 方案：TODO.md · CHANGELOG.md · source/(原始材料) · design/(各版本方案)
assets/         # 助眠音（可选）
data/           # 运行时 SQLite（不提交）
.streamlit/     # 暗色主题
```

## 进度

当前 = **v1 / P0 保底**（打字 → 拆解 → 收束 + 呼吸 + 助眠音占位）。
- 给同事看的完整说明：[docs/开发文档-v1.md](./docs/开发文档-v1.md)
- 还没做的：[docs/TODO.md](./docs/TODO.md) ｜ 演进记录：[docs/CHANGELOG.md](./docs/CHANGELOG.md)
