# 变更记录（CHANGELOG）

> 约定：每次大迭代在**顶部**新增一节，版本号对应 `docs/design/vN-*.md`。
> 记「做了什么 + 为什么」，方便路演讲演进故事，也方便回滚思路。

## v2.3 — 2026-05-23 · 月夜深湖视觉改版（参考图对齐）
- **配色从深绿水塘 → 月夜深蓝**：依参考图《月夜深湖》(`docs/Image_20260523_150031_203.jpeg`) 重做全局主题。`.stApp` 背景换成多层「左上月晕 + 右上极光(品红/青) + 湖面雾带 + 深蓝夜空渐变」；`.streamlit/config.toml` 主色 `#5e9c8b→#7fb0d8`、底色/次底色/文字同步转蓝，使滑条/复选框/主按钮原生控件一致。
- **池塘母题升级**：`POND` 从「三角立石」改为**孤树小岛 + 同心水波 + 月光倒影(moonpath) + 漂浮发光莲花**，复用于启动①/倾倒③/导图⑤/封存⑦；同心水波环数与节奏放缓更舒缓。
- **全局夜景层**：新增固定 `.scene`（月亮 + 两侧山影，在内容之下、`pointer-events:none`），八屏常驻；标题加月光辉光，按钮加 `backdrop-filter` 玻璃质感；呼吸圈/渐暗留言文字一并转月夜蓝。
- **取舍**：纯 CSS + 既有 DOM 结构，不加依赖、不改交互流程与管线，保持「最省力保底」路线；山影/雾用 CSS 径向渐变近似而非贴图。
- **验证**：app 重启 HTTP 200 无报错；用 Playwright 驱动系统 Chrome 真机渲染**逐屏截图核对**（启动/降落岛/倾倒/归位/导图/日志/评分/封存/降落 共 9 屏）均为月夜深蓝、孤树立石母题，与参考图一致。

## v2.2 — 2026-05-23 · D 降落语音 TTS
- **降落引导语出声**：`src/tts.py` 用本机 **macOS `say`**（免 key、离线，中文 Tingting 音）合成三段舒缓引导语，降落屏（⑧）`st.audio(autoplay)` 自动播放；无 `say`（非 macOS）静默退回纯文字 + 呼吸圈。
- **脚本**：`app.landing_narration(res)` 固定模板（确认闭环→身体感受→放下手机），用今晚的「明日第一步」轻度个性化，`[[slnc 毫秒]]` 拉出约 1 分钟舒缓停顿。不走 LLM（省 token）。结果按内容缓存。
- **取舍**：沿用免 key 本地路线（与 B 的 `claude -p`、C 的 faster-whisper 一致）；完整 2-5min 时长、背景助眠音、呼吸圈精确同步、非 macOS TTS 后端列入 TODO。
- **验证**：narration→1.78MB WAV（RIFF/WAVE）合成成功；app 重启 HTTP 200 无报错。
- **已知**：splash 自动跳转用的 `st.components.v1.html` 有弃用提示（2026-06-01 后移除），路演前不受影响，记入待办。

## v2.1 — 2026-05-23 · 接真实 AI 管线(B) + 语音转写(C)
- **B 真实管线**：`src/pipeline.py` 重写为**单次** `claude-opus-4-7` + `output_config.format` 结构化调用——一次拿全「六类线程 + 思维导图 + 第一人称夜间日志 + 那句看见 + 明日第一步」。省 token、少往返；降落语音/呼吸/转场等固定脚本不走 LLM。红线语气锁在 `src/prompts/murmora.txt`，system 挂 `cache_control`。无 key/出错自动回落 demo（池中之石），演示不崩。
- **C 语音转写**：`src/stt.py` = `st.audio_input` 录音 → **faster-whisper 本地**转写（零 key、离线、隐私最好）；没装 `faster-whisper` 时优雅降级为打字。倾倒屏接入：录完自动灌进文本框。
- **八屏接真实数据**：AI归位逐行/输出(导图⇄日志)/明日第一步卡片均改读 `pipeline.generate()` 结果；日期改为运行时计算。
- **C 语音调优**：默认模型 small→**medium**（普通话明显更准）+ `initial_prompt="以下是普通话的句子。"` 治 Whisper 中文爱出繁体/串味；`WHISPER_MODEL` 可换 small/large-v3。手机走局域网 http 无法录音（浏览器要安全上下文）→ 用打字。
- **取舍**：STT 选 faster-whisper 本地而非 OpenAI/浏览器——契合「睡前私密思绪」隐私调性、零额外 key。结构化输出需 `anthropic>=0.100`（已在 requirements 标注；本机 0.104 验证 `output_config` 可用）。
- **清理**：删除被取代的三段提示词 `prompts/{parse,soothe,winddown}.txt`。
- **免 key 后端（复用 Claude Code 登录）**：`pipeline.generate()` 改为三后端自动择优 —— ① `ANTHROPIC_API_KEY` → 直连 API（最快、可部署）；② 否则本机已登录 Claude Code → `claude -p` **复用订阅 OAuth（免 key）**；③ 都没有 → demo。CLI 后端要点：`--system-prompt` 把人格换成 Murmora、`--tools ""` 禁工具、`--json-schema` 拿结构化结果、临时 cwd 避免本仓库 CLAUDE.md 干扰；**不可用 --bare**（它禁 OAuth、强制 API key）。实测 `claude -p` 复用订阅跑出红线合规结果。
  - **边界（已记入 TODO）**：仅本机有效、部署到云不可用、比 API 慢；**用个人订阅给 app 供能受 Anthropic 用量政策约束**，仅作黑客松本地演示，勿对外分发。把 OAuth token 塞进 `anthropic` SDK 的 `auth_token=` 是**不支持且违反政策**的做法，未采用。
- **验证**：app 启动 HTTP 200；demo 数据路径 + 八屏渲染表达式 smoke-test 通过；STT 未装时降级正常；`claude -p` 免 key 后端实测出正确 Murmora 结构化结果。

## v2 — 2026-05-23 · 降落之选 · 八屏可视化（初版）
- **方向**：按 `docs/ADHD V2.pdf`《Murmora 秘落 · V3.0 降落之选》升级——产品更名 *Mistery → Murmora 秘落*，确立**池塘/降落母题**，主线从四屏扩为**八屏闭环**。
- **拆分**：本版分「**初版**（先走通看见）」与「**最终版**（还原 PDF 全效）」，详见 [v2-降落之选.md](./design/v2-降落之选.md)。
- **初版落地**：八屏路由（启动→降落岛→倾倒→AI归位→输出(导图⇄日志)→评分→封存→降落熄屏）；CSS 感官近似（立石+水波、4-1-6 呼吸圈、渐暗熄屏 overlay、星点）；输出双视图一键切换 + 内联反馈；mock 内容用 PDF「池中之石」示例。实测可启动（HTTP 200）。
- **取舍**：沿用 Streamlit（与现有 `pipeline.py`/`db.py` 同源、最省力）；内容先 mock，不接真实 AI/语音/TTS/落库——这些列入最终版 TODO（维度 A–F）。主题改深绿水塘色。
- **演进**：代码原地改 `src/app.py`（不另开目录）；`pipeline.py`/`db.py`/`prompts/` 保留待最终版接入。
- **下一步**：见 [TODO.md](./TODO.md) 的「v2 最终版」——优先 B（真实 AI 管线）与 D（降落语音）。

## v1 — 2026-05-23 · P0 保底骨架
- **方向**：选定故事赛道「第二夜 · 成人 ADHD（程野）」；产品定为 **Mistery 睡前思绪接住器**。
- **取舍**：移动端走 PWA（手机浏览器），不碰原生；纯 Python 用 Streamlit，最省力先打通「输入→输出」。
- **落地（P0）**：三段 LLM 管线（解析/安抚/收束）+ 四屏 UI（倾倒/梳理/收束/晚安）+ 呼吸动画 + 助眠音占位 + SQLite + 无 key demo 模式。实测可启动。
- **结构**：建立 `src/`（代码）与 `docs/`（方案）隔离的管理体系。
- **文档**：[v1 开发文档](./开发文档-v1.md)（可分享给产品/设计）、[半可视化方案](./design/v1-半可视化方案.md)、启动技能 `.claude/skills/run-mistery/`。
