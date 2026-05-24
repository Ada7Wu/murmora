# 变更记录（CHANGELOG）

> 约定：每次大迭代在**顶部**新增一节，版本号对应 `docs/design/vN-*.md`。
> 记「做了什么 + 为什么」，方便路演讲演进故事，也方便回滚思路。

## D′ 降落音改水滴 — 2026-05-24 · 双耳节拍太吵 → 很安静的水滴声
- **反馈「太吵」**：双耳节拍是**持续音**（载波+噪声床，RMS≈0.3），睡前显得吵。改成 `focus_audio.synth_waterdrops_wav`——**稀疏水珠**（每 ~2-4.5s 一颗，音高微微上扬的「叮—」+ 一点二次谐波）落在近乎静默之上，垫一层几乎听不见的水面气息；整体压到 **peak 0.24 / RMS≈0.02**（单声道 60s，2.6MB）。头尾淡入淡出 + 滴落不跨 loop 边界 → 无缝循环。
- **不再需要耳机**：降落屏提示「🎧 戴耳机」→ 改「· 很轻的水滴声，跟着它慢慢沉下去 ·」；`FILE_CANDIDATES` 把 `drip.mp3`/`water.mp3` 提前。`assets/` 放真实水滴音频仍优先用文件。
- **验证**：合成出单声道 22050Hz/60s，peak 0.24、RMS 0.02（确认安静）；`py_compile` 过；重启服务清掉 `st.cache_data` 旧音、app HTTP 200。

## E + G3 — 2026-05-24 · 重写 db、评分落库、记忆召回「似曾相识」
- **`src/db.py` 全重写**：v1 旧 schema（dumps/cards/feedback：todos/worries/ideas/winddown）与现 pipeline 不兼容且从未接入 → 换成 **entries / threads / ratings** 三表（对应 title/journal/insight/soothe/明日第一步/睡前落点 + 六类线程 + 评分反馈）。新表用新名字，旧表保留在旧 db 文件里不动、不迁移（仅 1 条 v1 测试数据）。新增 `MURMORA_DB` 环境变量可覆盖库路径（部署 / 测试隔离）。
- **E 评分落库**：⑥评分屏的 select_slider / 4 个 checkbox / text_input 都补了 key；「沉入池底」→ `db.save_rating(entry_id, 贴近度, 哪部分最贴近[list], 自由文本)`（贴近度映射 1-5 分）。整理完成时即 `db.save_entry(raw, channel, result)` 落这一夜并写入线程（供下次召回）。`app.py` 顶部 `@st.cache_resource` 建表一次。
- **G3 记忆召回「似曾相识」**：`db.recall_similar(raw)` 用**过往线程的短标签**（妈妈 / 汇报 / 播客…）在今晚原文里做子串匹配（优先 担忧/情绪/回忆，去重、最近优先，中文长标签补头两字 token），召回的片段 → ① 喂给 `pipeline.generate(history=…)`：拼进 **user 消息**（不污染可缓存的 system），prompt 加红线「只在确有呼应时像老朋友轻提一句，绝不罗列、不让他觉得被监视」；② 输出屏顶显示一句「N 天前你也曾为「X」停留过」。`pipeline.run/run_cli` 形参改 `user_text`，`run` max_tokens 1500→2000（容纳新增字段）。
- **守红线**：召回是「温柔的被记得」，不翻旧账、不复述细节；落库失败一律 try/except 吞掉，绝不拖垮降落流程。
- **验证**：db 单测（save_entry/save_rating/recall_similar 命中 妈妈+播客）；**AppTest 全链路**——开始生成→存 entry→评分→沉入池底→ratings 落库；第二夜含「妈妈/播客」→ 召回成功 + 输出屏出现「似曾相识」。实测走的是 **cli 后端（`claude -p`）真实生成**，确认新 SCHEMA（soothe/closing/closing_source）能经结构化输出正常往返。app 启动 HTTP 200 / health ok、boot 无 error；真实 `data/mistery.db` 未被测试污染（用 `MURMORA_DB` 临时库）。

## G + 双耳节拍 — 2026-05-24 · 感性日志「今夜封存」四段 + binaural beats 兜底
- **G 感性日志升级到固定四段（需求文档 §4 Skill 规范）**：感性视图从「一段第一人称重述」扩成「今夜封存」四段——① 你说了什么（叙事散文，归纳核心情绪 + 未被满足的需要，不复述原话、不过度下结论）② **抚慰疗愈**（点出他在承担的身份 + 温柔理解，只抚慰不说教）④ 明天只做一步 ⑤ **睡前落点**（治愈性收束，可引公版文学并标来源，结尾「今晚已经被保存」）。
  - **改动**：`prompts/murmora.txt` 重写四段说明 + 引用红线（只引公版、`closing_source` 必标来源、原创留空）；`pipeline.SCHEMA` 加 `soothe`/`closing`/`closing_source` 并入 required；`run_demo` 补三字段示范（睡前落点用王尔德《温德米尔夫人的扇子》公版句）；`app.py` 感性视图按 ①②④⑤ 渲染（理性视图仍只出导图 + 明日第一步，soothe/closing 不显示）。
  - **守红线**：抚慰只点身份/给理解，不发清单、不说教；引用限公版避免版权问题。
- **双耳节拍 binaural beats（升级 D′ 合成兜底）**：`focus_audio.synth_*` 从单声道雨噪 → **立体声双耳节拍**：左耳载波 200Hz / 右耳 200+6Hz，大脑感知到 **θ 6Hz**（海马体 theta 节律区间，助放松入睡），叠暖色噪声床 + 0.1Hz 呼吸起伏 + 头尾 1s 淡入淡出（60s loop，~5.3MB）。降落屏 synth 时提示「🎧 戴耳机」（双耳节拍需耳机才「拍」得出，外放退化为振幅起伏）。
- **验证**：`py_compile` 通过；`run_demo()` 含全部 G 字段、SCHEMA required 已更新；`focus_audio.get()` 出立体声 22050Hz/60s WAV；app 启动 HTTP 200 / health ok、boot log 无 error。

## D′ — 2026-05-24 · 降落音改向：ADHD 舒缓环境声替代 say 朗读
- **降落屏（⑧）不再朗读**：按用户决定，把 v2.2 的 macOS `say` 三段朗读换成**适合 ADHD 的舒缓环境声**（低刺激、可循环），用 `st.audio(loop=True, autoplay=True)` 轻放，配 4-1-6 呼吸圈把注意力从「想」落到「听」；原三段引导语降为**静默字幕**。
- **音频来源（用户给的原型 `focus_audio.py`，已从 `docs/` 移入 `src/`）**：`assets/` 里有 CC0 音频（`landing/rain/forest/ocean/stream.mp3`）就优先用，没有则用 **numpy 合成的雨噪兜底**（暖色 lowpass + 0.12Hz LFO 调幅 + 头尾淡入淡出防 loop 咔哒）——跨平台、免 key、路演不失声。
- **改动**：`src/app.py` 移除 `import tts` 与 `landing_narration`，新增缓存的 `landing_audio()` 调 `focus_audio.get()`；`requirements.txt` 加 `numpy>=1.24`；`assets/README.txt` 改为降落音约定；`src/tts.py`（`say` 朗读）保留为历史/退路，已不在降落屏调用。
- **验证**：`py_compile` 通过；`focus_audio.get()` 合成路径出 1.3MB WAV；app 启动 HTTP 200 / `_stcore/health` ok、boot log 无 error。
- **后续**：放一段真实助眠/脑波音 `assets/landing.mp3`（θ/δ/粉噪/binaural，CC0）替换合成兜底，见 [TODO.md](./TODO.md) D′。

## V3.0 规划 — 2026-05-24 · 依需求文档梳理新增功能（仅 TODO，未动代码）
- **依据**：`docs/Murmora_秘落之地_技术需求文档.md`。逐模块比对现状，八屏多数已落地；提炼出**真正新增/变更**项写入 [TODO.md](./TODO.md) 顶部「🆕 V3.0 需求文档新增」，**经用户确认**，本次只更新文档不改代码。
- **核心新增 G**：§4「Skill 规范」要求感性日志走**固定四段结构**——① 你说了什么（叙事散文）② **抚慰疗愈**（分析该承担的身份 + 建议，现无）④ 明天只做一步 ⑤ **睡前落点**（可引公版文学/名著**标来源**、结尾「今晚已经被保存」，现仅一句 insight）+「每次检索历史做类比」。落地需改 `prompts/murmora.txt` + `pipeline.SCHEMA` + `app.py` 输出屏。
- **用户决定 · 降落音改向（D′）**：降落屏**不再用 macOS `say` 朗读**引导语，改播**适合 ADHD 的舒缓音频（脑波/双耳节拍/「海马体共振」类）**；原 D 的 `say` 三段朗读降为退路。音频素材/频段待定。
- **用户决定 · 命名升级**：产品名 **Murmora 秘落 → Murmora 秘落之地 · V3.0**（splash/README/SKILL.md 待同步）。
- **记录的坑**：`src/db.py` 仍是 v1 旧 schema、与现 pipeline 不兼容且未接入 app，做 E/记忆召回前需先重写。

## v4 — 2026-05-23 · 晨露胶片 morning dew film（取代森林池塘）
- **整体换皮：暖森林绿 → 冷雾林胶片调**。按用户参考色卡「morning dew film」（松墨#22393c / 远山青#46707e / 苔绿#6b8b81 / sage#afbb98 / 晨陶米#cecdb9）重做视觉。**仅换皮 + 字体 + 母题冷调化**——八屏流程、AI 管线、语音/TTS、logo 资产全不动。方案见 [v4-晨露胶片.md](./design/v4-晨露胶片.md)。
- **依据两个 skill 落地**：① **ui-ux-pro-max** `--design-system` → Minimal Single Column + Lora/Raleway 字体 + 语义色 token + a11y 必做项；丢弃其默认薰衣草紫（与 frontend-design「禁紫渐变」冲突），改用用户色卡。② **frontend-design** → 明确美学方向（胶片冷雾）、避免通用 AI 风、用氛围/纹理而非纯色块。
- **语义色 token**：`:root` 定义 `--pine/--horizon/--moss/--sage/--clay` 及派生 `--text/--text-soft/--text-mute/--line/--surface/--fog`，组件改用 token（不再散落 raw hex）。
- **字体**：Quicksand → **Lora 衬线**（字标 MURMORA/标题/斜体副标题/降落留言，胶片 editorial 气质）+ **Raleway 正文**（CJK 回落 PingFang/雅黑），Google Fonts `display=swap`。
- **母题冷调化**：背景换冷松墨渐变；氛围层「孢子上浮」→ **谷中三条横向漂浮晨雾带 `fogdrift`** + 冷色露珠（v4 标志细节）；POND 几何松林 `--g` 全换冷调；**暖萤火（原唯一暖色 #e9c46a）→ 晨露微光**（sage→苔绿冷辉光）；水线/涟漪/苔叶/呼吸圈转晨陶米·sage。
- **配色 token（config.toml）**：主色 `#7fd6a8→#afbb98`、底 `#26604a→#20393e`、次底 `#2e6e57→#2a474d`、文字 `#eaf6ef→#cecdb9`。
- **无障碍**：主文字晨陶米/松墨 ≈7.5:1(AAA)、次文字 sage ≈6:1、弱文字提亮苔绿保≥4.5:1；按钮加 `:focus-visible` sage 焦点环；新增 `@media (prefers-reduced-motion: reduce)` 关装饰动画。
- **通道图标去 emoji**：② 降落岛「感性/理性」`◐ / 🪨` → **几何 SVG**（感性=石落涟漪荡开、理性=把事理成一块立石，呼应核心隐喻「池中之石」、合起来即 logo）。色卡描边 token（sage 主 + 晨陶米细节 + 冷光晕）、统一 2px、`aria-hidden`（旁有文字标签）。满足两 skill「禁 emoji 当结构图标」。
- **验证**：app 重启 HTTP 200、boot log 无 error/traceback；`grep` 确认旧森林绿/暖萤火色清干净（仅注释留史）；Playwright 真机截图核对 ①启动/②降落岛(含新 SVG 图标)/③倾倒(含 POND) 冷雾调统一、Lora 到位、文字可读。
- **后续**：见 [TODO.md](./TODO.md)——思维导图分类标等内容型 emoji 视情况再换（优先级低）。

## v3 — 2026-05-23 · 森林池塘视觉系统（取代月夜深湖）
- **整体换皮：月夜深蓝 → 暮色森林绿**。按用户方向「不要月亮星星、要纪念碑谷几何 + 倒映森林的池塘、绿色」重做视觉。**仅换皮**——八屏流程、AI 管线、语音/TTS 全不动。方案见 [v3-森林池塘.md](./design/v3-森林池塘.md)，配套草图 `docs/design/森林池塘-草图.html`。
- **母题重做**：删除 `.scene` 的月亮/山影、删除极光/月晕径向渐变、删除星点意象。`POND` 从「孤树立石 + 月光倒影」改为**几何松林（clip-path 分层三角 + color-mix 左亮右暗假立体）+ 整片镜像倒影 + 同心涟漪 + 睡莲叶 + 一盏暖萤火(#e9c46a 唯一暖色)**；固定层改为天光雾 + 上浮孢子。
- **配色 token**：`.streamlit/config.toml` 主色 `#7fb0d8→#74c69d`、底 `#06101f→#163a2b`、次底 `#1a4a37`、文字 `#eaf6ef`；CSS 全量转森林绿，hint 色 `#7e9bbd→#a9d3bd`（对比达标）。标题字体加 Google Font **Quicksand**。
- **取舍**：经一轮「太暗」反馈，整体抬到「暮色」而非「午夜」（背景/绿色/倒影亮度均上调一档）；用户先看静态草图确认效果再并入 app；纯 CSS + 既有 DOM，零新依赖。**去掉了纪念碑谷式的塔**（用户：不要灯塔，要池塘感）。
- **文案**：启动副标题改「夜林如墨　池塘倒映整片森林」；封存按钮 🌙→🌲。
- **品牌 logo**：新增 `assets/murmora-logo.jpeg`（水波勾出的「M」+ 石子落池涟漪，恰是产品母题）。① 启动屏以它为主视觉（取代该屏的 `POND`，POND 仍用于 ③⑦⑧），JPEG 设为浏览器 `page_icon` favicon。app 内用**透明描边版** `assets/murmora-logo.png`（按亮度 smoothstep 抠掉深绿底、统一奶白描边、无绿晕，脚本一次性生成）——叠在任意背景上都无方块、无缝；内联 base64 data URI（`logo_data_uri()` 缓存，本地/云端免静态托管）+ 暖光晕 + 7s 呼吸动画。Playwright 真机截图确认。
- **配色调浅**：按用户「换一种更浅的绿」把背景从暮色深绿抬到**更清透的林间绿**——`.stApp` 渐变 `#163a2b/#1a4836/#0e2a1f → #235844/#30715a/#194534`，顶部天光雾微降透明度；`.streamlit/config.toml` 底 `#163a2b→#26604a`、次底 `#1a4a37→#2e6e57`、主色 `#74c69d→#7fd6a8`。为护可读性，次级文字同步提亮：m-sub/hint `#a9d3bd→#cdebda/#c2e3d3`、星点 `#4f8770→#74ab90`。透明 logo 使其在更浅底上仍无缝。Playwright 截图核对启动/降落岛/倾倒(含 POND 松林)三屏：logo 融入、文字可读、松林+萤火在浅水上仍清楚。
- **验证**：app 重启 HTTP 200、`_stcore/health` ok、boot log 无 error/traceback；`grep` 确认无月/星/极光/山影母题残留（仅日期 `_today.month` 等无关命中）。
- **后续**：见 [TODO.md](./TODO.md) 「v3 视觉系统」——逐屏真机截图核对、app 内补 `prefers-reduced-motion`、母题铺满评分/降落岛屏。

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
