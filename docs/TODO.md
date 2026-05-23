# TODO — Murmora 秘落 待办

> 唯一待办源（single source of truth）。做完的勾掉，并在 [CHANGELOG.md](./CHANGELOG.md) 记一笔。
> 优先级：⭐ = 路演必需；➕ = 加分；🧊 = 以后再说。
> 当前版本：**v2**——八屏 + **真实 AI(B)** + **语音转写(C)** + **降落语音(D)** 已落地，继续推进 E/F。最近更新：2026-05-23。
> 方案见 [v2-降落之选.md](./design/v2-降落之选.md)（初版/最终版拆分 + 维度 A–F）。

---

## 🔥 v2 最终版 · 进行中 / 下一步

把「能点完的八屏可视化」补成「PDF 描述的真实体验」。维度编号对应 v2 设计文档第三、四节。

### B. 真实 AI 管线（替换 mock，最高优先）
- [x] ⭐ **六类线程识别**：单次 `claude-opus-4-7` + `output_config.format` 结构化输出（`src/pipeline.py`）
- [x] ⭐ **双视图生成**：思维导图（中心主题+分支线程）+ 夜间日志（第一人称重述 + 那句「看见」）
- [x] ⭐ **明日第一步卡片**：`tomorrow_first_step`，把「启动」交给明天（守红线：奖励开始，不发清单）
- [x] ➕ **prompt caching**：system 已挂 `cache_control`（提示词未到 4096 token 阈值前不真正命中，但不报错）
- [x] ⭐ **真实链路已验证**：本机 `claude -p` **复用 Claude Code 订阅 OAuth（免 key）** 已实测出红线合规结果（明日第一步"小到不可能失败"）；填 `ANTHROPIC_API_KEY` 则走直连 API（更快、可部署）
- [x] ➕ **免 key 后端**：`pipeline.generate()` 三后端自动择优 api → cli(订阅 OAuth) → demo
- [ ] ➕ **夜间认知扭曲检验**：对「乐观偏差/泡沫念头」温和提示（PDF 深层痛点）

### D. 降落语音（TTS · 路演要能出声）
- [x] ⭐ **降落引导语 TTS**：本机 macOS `say`（免 key、离线）合成三段舒缓引导语（确认闭环→身体→放下手机），降落屏自动播放；无 say 退回纯文字。用今晚「明日第一步」轻度个性化（`src/tts.py` + `app.landing_narration`）。
- [ ] ➕ **降落音进阶**：叠加 `assets/` 背景助眠音、补到完整 2-5min、呼吸圈与音频精确同步、非 macOS 的 TTS 后端（云/pyttsx3）

### C. 语音输入（PDF 默认方式）
- [x] ➕ **录音转写**：`st.audio_input` → **faster-whisper 本地**（`src/stt.py`）→ 灌进倾倒框；没装则自动降级打字
- [ ] ➕ **30s 静默中断保护**：「够了吗？我帮你整理一下」[还有要说的][开始整理]
- [ ] ➕ **让手机也能录音**（暂缓）：手机浏览器要 HTTPS 才给麦克风，现局域网 `http` 录不了。方案：① **Cloudflare/ngrok HTTPS 隧道**（app 仍在本机跑 → 免 key 订阅照常；URL 公开，仅演示开）；② 局域网自签证书（iOS Safari 较难，要装根证书）；③ 兜底：加 `st.file_uploader`，手机用语音备忘录录好上传，`http` 下即可用。详见 v2.1 讨论。

### E. 反馈训练 & 记忆沉淀
- [ ] ➕ **评分写库**：贴近度 / 哪部分最贴近 / 自由文本 → `db`（接现有 `src/db.py`）
- [ ] ➕ **唤起以往记忆**：召回旧 worry/idea 做类比（`db.past_worries()` 升级为按相关度）

### A. 感官动效（要更还原 → 考虑切升级路线）
- [ ] ➕ 启动 2-3s **自动**跳转、降落岛 4s 呼吸、归位 5-10s 不可跳过
- [ ] ➕ 倾听态声音**实时**化作水波/波形；封存=抽屉合上 + 触觉反馈
- [ ] ➕ 降落屏最后 60s 屏幕**真实**亮度递减后熄屏
- [ ] 🧊 **升级路线评估**：动画/语音吃力时切 **FastAPI + 单页 HTML(PWA) + Web Speech API**（前端可让 Claude Code 代写）

### F. 关怀与晨间层（PDF 长期目标，黑客松可裁）
- [ ] 🧊 **激素周期关怀**：经期前夕对夜间冲动/美化倾向更柔的提示
- [ ] 🧊 **晨间层**：仅 6:00-12:00 出现的「昨夜回顾」入口 + 记忆沉淀

### 收尾
- [ ] ➕ **PWA**：manifest + 图标，「添加到主屏幕」更像 App
- [ ] ➕ **部署 Streamlit Cloud**：公网网址，手机扫码即开；key 放 Secrets

---

## ✅ 已完成

### v2 初版（八屏可视化 · 2026-05-23）
- [x] 产品升级为 **Murmora 秘落 · 降落之选**，池塘/降落母题
- [x] 八屏路由：启动 → 降落岛 → 倾倒 → AI归位 → 输出(导图⇄日志) → 评分 → 封存 → 降落熄屏
- [x] CSS 感官近似：立石+水波 ripple、呼吸圈(4-1-6)、渐暗熄屏 overlay、星点
- [x] 输出双视图一键切换 + 内联反馈；评分屏；mock 内容（池中之石示例）
- [x] 深绿水塘主题（`.streamlit/config.toml` + `.stApp` 渐变）
- [x] 实测可启动（HTTP 200 / health ok）
- [x] v2 设计文档（初版/最终版拆分）

### v1（P0 保底骨架）
- [x] 选定故事赛道：第二夜 · 成人 ADHD（程野）；产品定义 + 设计红线
- [x] 技术栈定稿：Streamlit(PWA) + Claude API + SQLite
- [x] 三段 LLM 管线（解析→安抚→收束）+ 四屏 UI + 呼吸动画 + SQLite + 无 key demo 模式
- [x] 目录重构：代码(`src/`) 与 方案文档(`docs/`) 隔离

---

## 已知坑 / 注意

- **真实 AI(B) + 语音(C) 已接**，且 B 有**三后端**：① `ANTHROPIC_API_KEY` 直连 API（可部署）；② 本机已登录 Claude Code → `claude -p` **复用订阅 OAuth（免 key，仅本地）**；③ demo 兜底。语音需装 `faster-whisper`（没装自动降级打字）。仍待：D 降落语音 TTS、E 落库/反馈、晨间层。
- **免 key(cli) 后端的边界**：只在装了并登录了 Claude Code 的本机有效（**部署到 Streamlit Cloud 不可用**）；比直连 API 慢（子进程+agent 开销）；**用个人订阅给 app 供能受 Anthropic 用量政策约束，仅作黑客松本地演示，勿对外分发**。实现要点：`--system-prompt` 替换人格、`--tools ""` 禁工具、临时 cwd；**切勿加 --bare**（会禁 OAuth）。
- 提示词目前较短，**prompt caching 暂不触发**（不报错，知识库变长后自动生效）。
- `data/mistery.db` 是运行时数据，已 gitignore，不要提交。
- 运行命令：根目录执行 `streamlit run src/app.py`（`.streamlit/` 配置留在根目录才生效）。
- 重动效（水波/渐暗/转场/音频同步）在 Streamlit 上是近似实现；要高保真请评估升级路线（见 A）。
