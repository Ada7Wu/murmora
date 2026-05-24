# TODO — Murmora 秘落 待办

> 唯一待办源（single source of truth）。做完的勾掉，并在 [CHANGELOG.md](./CHANGELOG.md) 记一笔。
> 优先级：⭐ = 路演必需；➕ = 加分；🧊 = 以后再说。
> 当前版本：**Murmora 秘落之地 · V3.0**（产品名升级，依需求文档 [Murmora_秘落之地_技术需求文档.md](./Murmora_秘落之地_技术需求文档.md)）+ v4 晨露胶片视觉 + 八屏闭环（真实 AI B + 语音 C + 降落 D）。最近更新：2026-05-24。
> 视觉方案见 [v4-晨露胶片.md](./design/v4-晨露胶片.md)；功能维度 A–F 见 [v2-降落之选.md](./design/v2-降落之选.md)；本版新增见下「🆕 V3.0 需求文档新增」。

---

## 🆕 V3.0 需求文档新增（[Murmora_秘落之地_技术需求文档.md](./Murmora_秘落之地_技术需求文档.md)）

产品名升级为 **Murmora 秘落之地 · V3.0**。文档八屏多数已落地，下面是相较现状**真正新增 / 变更**的点。

### G. 感性日志 Skill 升级到「今夜封存」固定结构（§4 Skill 规范 · 最高优先）
- [x] ⭐ **重写感性日志为四段固定结构**：① 你说了什么（叙事散文，归纳核心情绪 + 未被满足的需要，不复述原话、不替用户过度下结论）② 抚慰疗愈（分析用户该承担的身份 + 给温柔的分析与建议）④ 明天只做一步 ⑤ 睡前落点（治愈性收束）。已改 `prompts/murmora.txt` + `pipeline.SCHEMA`（新增 `soothe`/`closing`/`closing_source`）+ `app.py` 感性视图四段渲染（理性视图仍只出导图 + 明日第一步）
- [x] ⭐ **睡前落点守版权红线**：prompt 锁「只引**公版**文学/名著且 `closing_source` **必标来源**，原创则留空」，结尾固定「今晚已经被保存」（demo 用王尔德公版句示范）
- [x] ➕ **检索历史做类比**（Skill 要求「每次都检索历史资料，存在类似情况时」）：已实现，见 E「唤起以往记忆（G3）」——`db.recall_similar` 召回 → 喂 LLM + 输出屏「似曾相识」提示

### D′. 降落音改向：ADHD 舒缓音频替代朗读（覆盖原 D 的 TTS 路线 · 用户决定）
- [x] ⭐ **降落屏不再用 macOS `say` 朗读**：改播 ADHD 舒缓环境声，`st.audio(loop, autoplay)` 循环轻放、随呼吸圈起伏；三段引导语保留为静默字幕。`app.py` 已移除 `tts`/`landing_narration` 调用
- [x] ⭐ **音频来源 = 文件优先 / 合成兜底**（`src/focus_audio.py`，已从 docs/ 移入 src/）：`assets/` 有 `landing/rain/forest…mp3` 就用它，否则 numpy 合成兜底，跨平台免 key 不失声。`requirements.txt` 加 `numpy`
- [x] ➕ **合成音定为「很安静的水滴声」**（双耳节拍 binaural 试过但反馈太吵已弃）：稀疏水珠（每 ~2-4.5s 一颗，音高微上扬的「叮」+ 二次谐波）落在近乎静默上 + 极轻水面气息，压到 peak 0.24 / RMS≈0.02（单声道 60s，2.6MB loop）；降落屏提示「· 很轻的水滴声 ·」
- [ ] ➕ **放一段真实助眠/脑波音**：`assets/landing.mp3`（θ4-8Hz / δ / 粉噪 / binaural，CC0），替换当前合成兜底，质感更好 —— **可你给素材**
- 📜 注：原 D（`say` 三段朗读）保留在 `src/tts.py` 作历史/退路，已不在降落屏调用

### 其它文档差异（小）
- [ ] ➕ **启动屏**补「个性化欢迎语」（现为固定副标题）；字标补英文口号 "Let every thought find a place to land"
- [ ] ➕ **命名同步**：splash 副标题、`README.md`、`.claude/skills/run-mistery/SKILL.md` 顶部 → 「Murmora 秘落之地 · V3.0」

---

## 🎨 v4 视觉系统 · 晨露胶片 morning dew film（continue going forward 按本系统推进）

视觉基线已落地（语义色 token + Lora/Raleway + 冷雾林倒映池塘 + 漂浮晨雾 + 晨露微光）；新增 UI 改动一律沿用 v4 token/母题。详见 `docs/design/v4-晨露胶片.md`。

- [x] ⭐ 换皮到晨露胶片冷雾调（依 ui-ux-pro-max + frontend-design 两 skill）；语义色 token + Lora/Raleway + 漂浮晨雾 + 暖萤火→晨露微光
- [x] ⭐ app 内补全 `@media (prefers-reduced-motion)`（v4 已加全局关装饰动画）
- [x] ⭐ 逐屏真机截图核对（Playwright）：①启动/②降落岛/③倾倒(POND) 冷雾调统一、文字可读
- [ ] ➕ 截图核对剩余屏：④归位/⑤输出(导图+日志)/⑥评分/⑦封存/⑧降落，确认 token 继承一致
- [x] ⭐ ② 降落岛「感性/理性」`◐ / 🪨` → 几何 SVG（感性=石落涟漪、理性=立石，呼应「池中之石」；色卡描边 + aria-hidden）
- [ ] 🧊 其余 emoji 视情况换 SVG：思维导图分类标（🗓💭✨🌊🌙🎞）、倾倒🎙、输出🌱（属内容标记，非结构图标，优先级低）
- [ ] 🧊 微调：晨雾带数量/节奏、涟漪节奏、水面占比、降落渐暗阶段进一步压低晨露微光亮度
- 📜 历史：v3 暮色森林绿、v2.3 月夜深湖 见 CHANGELOG（演进可路演）

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
- [x] ➕ **评分写库**：⑥评分屏「沉入池底」→ `db.save_rating(entry_id, 贴近度, 哪部分最贴近[], 自由文本)`；整理完即 `db.save_entry()` 落这一夜（含线程）。`src/db.py` 已重写为 entries/threads/ratings 新 schema（旧 dumps/cards/feedback 废弃保留）
- [x] ➕ **唤起以往记忆（G3）**：`db.recall_similar(raw)` 用过往线程关键词在今晚原文里命中（优先担忧/情绪/回忆），喂给 `pipeline.generate(history=…)` 让 LLM 可「似曾相识」，输出屏也显示一句「N 天前你也曾为「X」停留过」
- [ ] 🧊 **召回升级**：关键词 → 按相关度/embedding（现为子串匹配，够黑客松用；中文长标签补了头两字 token）

### A. 感官动效（要更还原 → 考虑切升级路线）
- [ ] ➕ 启动 2-3s **自动**跳转、降落岛 4s 呼吸、归位 5-10s 不可跳过
- [ ] ➕ 倾听态声音**实时**化作水波/波形；封存=抽屉合上 + 触觉反馈
- [ ] ➕ 降落屏最后 60s 屏幕**真实**亮度递减后熄屏
- [ ] 🧊 **升级路线评估**：动画/语音吃力时切 **FastAPI + 单页 HTML(PWA) + Web Speech API**（前端可让 Claude Code 代写）

### F. 关怀与晨间层（PDF 长期目标，黑客松可裁）
- [ ] 🧊 **激素周期关怀**：经期前夕对夜间冲动/美化倾向更柔的提示
- [ ] 🧊 **晨间层**：仅 6:00-12:00 出现的「昨夜回顾」入口 + 记忆沉淀

### 收尾
- [ ] ➕ **PWA**：manifest + 图标，「添加到主屏幕」更像 App（图标可用现成的 `assets/murmora-logo.jpeg`，导出多尺寸 png）
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
- **✅ `src/db.py` 已重写为新 schema**（entries/threads/ratings），接入 `app.py`：整理完 `save_entry`、评分 `save_rating`、倾倒时 `recall_similar` 召回。v1 旧表（dumps/cards/feedback）废弃但保留在旧 db 文件里不动（新表用不同名字避免撞名）。`MURMORA_DB` 环境变量可覆盖库路径（部署/测试隔离）。`data/mistery.db` 仍 gitignore、无云备份（换机需手动拷 `data/`）。
- **代码已上 GitHub**：`git@github.com:Ada7Wu/murmora.git`（分支 `main`，走 SSH）。日常 `git add -A && git commit && git push` 即可。
- `data/mistery.db` 是运行时数据，已 gitignore，不要提交。**⚠️ 代价**：它不会同步到 GitHub，**没有云备份**；换机器时需手动拷贝 `data/` 才能保留历史日志。`.env`、`.claude/settings.local.json` 同理（已忽略，含密钥/本机配置）。
- 运行命令：根目录执行 `streamlit run src/app.py`（`.streamlit/` 配置留在根目录才生效）。
- 重动效（水波/渐暗/转场/音频同步）在 Streamlit 上是近似实现；要高保真请评估升级路线（见 A）。
