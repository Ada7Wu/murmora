"""Murmora 秘落 — 睡前思绪「降落」器（v2 初版 · 八屏可视化）

> 这是 v2 的【初版可视化】：用 Streamlit 把 PDF《降落之选》的八屏闭环先「走通看见」。
> 内容为 mock（PDF 的「池中之石」示例），重点是把流程、暗色水塘质感、呼吸/渐暗的感官体验
> 先呈现出来。接真实 AI 管线（pipeline.py）/ 语音转写 / TTS 降落语音是【最终版】的事，
> 详见 docs/design/v2-降落之选.md 与 docs/TODO.md。

运行：  streamlit run src/app.py    （务必在项目根目录执行，.streamlit/ 主题才生效）
"""
import datetime as _dt
import hashlib
import time

import streamlit as st
import streamlit.components.v1 as components

import pipeline
import stt
import tts

st.set_page_config(page_title="Murmora 秘落", page_icon="🌙", layout="centered")

# ============================================================
# 真实结果来自 pipeline.generate()（B 管线）；下面是固定映射/脚本（不走 LLM，省 token）
# ============================================================
DEFAULT_DUMP = "明天有汇报，PPT 还没写完……刚才和妈妈视频，她又说我太瘦……突然想到一个播客选题……好困但还是清醒的……"

CAT_EMOJI = {"任务": "🗓", "情绪": "💭", "灵感": "✨", "担忧": "🌊", "回忆": "🌙", "小电影": "🎞"}

_today = _dt.date.today()
DATE_CN = f"{_today.month}月{_today.day}日"
WEEK_CN = "周" + "一二三四五六日"[_today.weekday()]

LANDING_SCRIPT = [
    "你今晚说的，都被我接住了。",
    "感受一下你的肩膀……你的呼吸……",
    "现在，把手机放在你够不到的地方。",
]


def landing_narration(res):
    """降落语音脚本（PDF 三段：确认闭环→身体感受→放下手机），用今晚的「明日第一步」轻度个性化。
    `[[slnc 毫秒]]` 是 macOS say 的停顿指令，拉出舒缓节奏（约 1 分钟）。固定模板，不走 LLM。"""
    step = (res or {}).get("tomorrow_first_step", "").strip()
    mid = (f"明天的第一步，只是{step}　其他的，先交给明天。[[slnc 1800]]" if step
           else "今晚不用再想了。[[slnc 1200]]")
    return (
        "[[slnc 700]]你今晚说的，都被我接住了。[[slnc 1500]]"
        + mid +
        "现在，慢慢地，感受你的肩膀，让它沉下来。[[slnc 1400]]"
        "感受你的呼吸……吸气……[[slnc 1700]]呼气……[[slnc 2300]]"
        "现在，可以把手机，放在你够不到的地方了。[[slnc 1500]]晚安。"
    )

# ============================================================
# 全局样式 —— 月夜深湖 / 月亮 / 极光 / 山影 / 孤树立石 / 水波 / 莲花 / 呼吸圈 / 渐暗
#   配色与母题取自参考图《月夜深湖》：深蓝夜空 + 左上月晕 + 右上极光 + 两侧山影 +
#   湖面薄雾 + 中央孤树小岛同心水波 + 月光倒影 + 漂浮莲花。
# ============================================================
st.markdown(
    """
    <style>
      #MainMenu, footer, header {visibility:hidden;}

      /* —— 月夜深湖背景：月晕 + 极光(品红/青) + 雾带 + 深蓝夜空渐变 —— */
      .stApp {
        background:
          radial-gradient(closest-side at 16% 12%, rgba(229,239,255,.50),
                          rgba(176,202,244,.16) 38%, transparent 72%),
          radial-gradient(42% 30% at 83% 15%, rgba(196,128,214,.16), transparent 70%),
          radial-gradient(48% 36% at 72% 22%, rgba(96,182,222,.15), transparent 72%),
          linear-gradient(to bottom, transparent 44%, rgba(150,186,226,.08) 55%, transparent 67%),
          linear-gradient(to bottom, #0a1830 0%, #0b1d37 32%, #0c2240 52%,
                          #081a30 74%, #050c18 100%);
        background-attachment: fixed;
      }
      [data-testid="stAppViewContainer"] .block-container {position:relative; z-index:1;}
      .block-container {max-width:430px; padding-top:2.0rem; padding-bottom:3rem;}

      /* —— 固定夜景层（在内容之下）：月亮 + 两侧山影 —— */
      .scene {position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden;}
      .scene .moon {position:absolute; left:11%; top:7%; width:58px; height:58px; border-radius:50%;
        background:radial-gradient(circle at 38% 36%, #fbfdff 0%, #e7eeff 46%, #cdd9f3 70%, #aebfe0 100%);
        box-shadow:0 0 36px 12px rgba(218,232,255,.42), 0 0 86px 30px rgba(150,185,235,.20);
        animation:moonglow 9s ease-in-out infinite;}
      @keyframes moonglow{0%,100%{filter:brightness(1)}50%{filter:brightness(1.12)}}
      .scene .mtn-l, .scene .mtn-r {position:absolute; bottom:0; width:62%; height:30%;
        background:radial-gradient(120% 140% at 50% 130%, #0c2036 0%, #0a1a2c 46%, transparent 70%);
        opacity:.55;}
      .scene .mtn-l{left:-12%} .scene .mtn-r{right:-12%}

      .stButton button {
        border-radius:16px; height:3rem; font-size:1.02rem;
        border:1px solid #2c4a6e; background:rgba(17,32,58,.72); color:#dce7f5;
        backdrop-filter:blur(3px);
      }
      .stButton button:hover {border-color:#7fb0d8; color:#fff;}

      .m-title  {text-align:center; letter-spacing:.55em; font-size:1.5rem;
                 color:#eaf2fb; margin:6px 0 2px; padding-left:.55em;
                 text-shadow:0 0 22px rgba(150,190,238,.45);}
      .m-sub    {text-align:center; color:#8fb4d6; font-size:.96rem; margin:6px 0 18px;}
      .m-ask    {text-align:center; color:#eaf2fb; font-size:1.22rem; margin:10px 0 6px;}
      .calm     {text-align:center; color:#d2e1f2; font-size:1.12rem; line-height:2.0;
                 margin:8px 6px;}
      .hint     {color:#7e9bbd; text-align:center; font-size:.9rem;}
      .stars    {color:#43608a; text-align:center; letter-spacing:.35em;
                 font-size:.8rem; margin:4px 0;}

      /* —— 孤树小岛 + 同心水波 + 月光倒影 + 莲花（池塘母题，多屏复用）—— */
      .pond {position:relative; height:172px; display:flex;
             align-items:flex-end; justify-content:center; margin:8px 0 14px;}
      .pond .moonpath {position:absolute; bottom:6px; left:50%; transform:translateX(-50%);
             width:26px; height:96px; border-radius:50%; filter:blur(5px);
             background:linear-gradient(to bottom, rgba(222,236,255,.28), transparent 86%);}
      .island {position:relative; z-index:3; display:flex; flex-direction:column; align-items:center;}
      .tree {display:flex; flex-direction:column; align-items:center;}
      .canopy {width:62px; height:72px;
               border-radius:50% 50% 46% 46% / 62% 62% 40% 40%;
               background:radial-gradient(circle at 40% 34%, #335150, #15302f 72%);
               box-shadow:0 0 16px rgba(150,200,235,.18), inset 6px -4px 12px rgba(0,0,0,.35);}
      .trunk {width:7px; height:24px; background:#15302f; margin-top:-3px; border-radius:0 0 3px 3px;}
      .island::after {content:""; width:78px; height:13px; margin-top:1px; border-radius:50%;
               background:radial-gradient(circle, #16302f 0%, rgba(22,48,47,.5) 55%, transparent 75%);}
      .ripple {position:absolute; bottom:18px; width:64px; height:18px;
               border:1px solid #9ec9e8; border-radius:50%;
               opacity:0; animation:rip 5s ease-out infinite;}
      .ripple:nth-child(2){animation-delay:1.6s;}
      .ripple:nth-child(3){animation-delay:3.2s;}
      @keyframes rip {
        0%   {transform:scale(.45); opacity:.7;}
        100% {transform:scale(4.6); opacity:0;}
      }
      .lotus {position:absolute; bottom:14px; width:9px; height:9px; border-radius:50%;
              background:radial-gradient(circle, #fff 0%, #cfe2ff 55%, transparent 75%);
              box-shadow:0 0 8px rgba(220,234,255,.7); opacity:.85;}
      .lotus.l1{left:30%} .lotus.l2{right:28%; bottom:28px; width:7px; height:7px;}

      /* —— 呼吸圈 4-1-6（降落屏）—— */
      .breath {width:120px;height:120px;border-radius:50%;margin:6px auto;
               background:radial-gradient(circle,#a3d3ef,#1c3354);
               box-shadow:0 0 50px rgba(127,176,216,.40);
               animation:breathe 11s ease-in-out infinite;}
      @keyframes breathe{
        0%  {transform:scale(.62);opacity:.55}     /* 呼气末 */
        36% {transform:scale(1.15);opacity:1}        /* 吸气 4s */
        45% {transform:scale(1.15);opacity:1}        /* 屏息 1s */
        100%{transform:scale(.62);opacity:.55}       /* 呼气 6s */
      }

      /* —— 渐暗熄屏 overlay —— */
      .dimmer {position:fixed; inset:0; background:#000; z-index:9999;
               animation:dim 9s ease-in forwards; pointer-events:none;}
      @keyframes dim {0%{opacity:0} 100%{opacity:.95}}
      .dim-msg {position:fixed; inset:0; z-index:10000; display:flex;
                flex-direction:column; align-items:center; justify-content:center;
                color:#cfe0f0; text-align:center; line-height:2.1; font-size:1.1rem;
                animation:msgin 9s ease-in forwards; pointer-events:none;}
      @keyframes msgin {0%,55%{opacity:0} 100%{opacity:.85}}
    </style>
    <div class="scene"><div class="moon"></div><div class="mtn-l"></div><div class="mtn-r"></div></div>
    """,
    unsafe_allow_html=True,
)

STARS = "<div class='stars'>·　˙　·　·　˙　·　·　˙　·　·　˙　·</div>"
POND = """
<div class="pond">
  <div class="moonpath"></div>
  <div class="ripple"></div><div class="ripple"></div><div class="ripple"></div>
  <div class="lotus l1"></div><div class="lotus l2"></div>
  <div class="island"><div class="tree"><span class="canopy"></span><span class="trunk"></span></div></div>
</div>
"""


# ---------- 状态 & 导航 ----------
def goto(screen):
    st.session_state.screen = screen
    st.rerun()


st.session_state.setdefault("screen", "splash")
st.session_state.setdefault("channel", "sensory")   # sensory=感性→日志, rational=理性→导图
st.session_state.setdefault("view", "journal")       # 输出屏当前视图


# ====================== 屏 ① 启动 ======================
if st.session_state.screen == "splash":
    st.markdown(STARS, unsafe_allow_html=True)
    st.markdown("<div class='m-title'>MURMORA</div>", unsafe_allow_html=True)
    st.markdown(POND, unsafe_allow_html=True)
    st.markdown("<div class='m-sub'>夜色温柔　池塘已醒</div>", unsafe_allow_html=True)
    st.markdown(STARS, unsafe_allow_html=True)
    st.write("")
    if st.button("进　入", use_container_width=True, key="enter"):
        goto("island")
    st.markdown("<div class='hint'>三秒后自动降落 · 或点「进入」直接进</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='hint' style='margin-top:6px'>让每一个停不下来的念头，都有地方降落</div>",
                unsafe_allow_html=True)
    # 停留 3 秒后自动「点」进入按钮；用户也可手动点立即进入
    components.html(
        """
        <script>
        setTimeout(function(){
          const doc = window.parent.document;
          for (const b of doc.querySelectorAll('button')){
            if (b.innerText.replace(/\\s/g,'').includes('进入')){ b.click(); break; }
          }
        }, 3000);
        </script>
        """,
        height=0,
    )


# ====================== 屏 ② 降落岛选择 ======================
elif st.session_state.screen == "island":
    st.markdown(STARS, unsafe_allow_html=True)
    st.markdown("<div class='m-ask'>今晚想从哪里降落？</div>", unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='text-align:center;font-size:2.2rem'>◐</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='calm' style='font-size:1.05rem'>感 性<br>"
                    "<span class='hint'>想说点什么</span></div>", unsafe_allow_html=True)
        if st.button("从这里降落", key="sens", use_container_width=True):
            st.session_state.channel = "sensory"
            st.session_state.view = "journal"
            goto("dump")
    with c2:
        st.markdown("<div style='text-align:center;font-size:2.2rem'>🪨</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='calm' style='font-size:1.05rem'>理 性<br>"
                    "<span class='hint'>有事要理清</span></div>", unsafe_allow_html=True)
        if st.button("从这里降落", key="rat", use_container_width=True):
            st.session_state.channel = "rational"
            st.session_state.view = "map"
            goto("dump")
    st.write("")
    if st.button("我也不知道，先开口 →", use_container_width=True):
        st.session_state.channel = "sensory"
        st.session_state.view = "journal"
        goto("dump")


# ====================== 屏 ③ 倾倒输入 ======================
elif st.session_state.screen == "dump":
    st.markdown("<div class='m-ask'>写下今晚的水波</div>", unsafe_allow_html=True)
    st.markdown(POND, unsafe_allow_html=True)
    st.markdown("<div class='hint'>🎙 录一段说给我听，或直接打字 —— 不急，想说什么</div>",
                unsafe_allow_html=True)
    st.write("")
    # 语音：录音 → faster-whisper 本地转写 → 灌进下面的文本框（没装则自动降级为打字）
    audio = st.audio_input("说给我听", label_visibility="collapsed")
    if audio is not None:
        h = hashlib.md5(audio.getvalue()).hexdigest()
        if h != st.session_state.get("_audio_hash"):       # 同一段录音只转一次
            st.session_state["_audio_hash"] = h
            if stt.available():
                with st.spinner("声音化作水波，正在听你说 …"):
                    said = stt.transcribe(audio.getvalue())
                if said:
                    prev = st.session_state.get("dump_area", "")
                    st.session_state["dump_area"] = (prev + ("　" if prev else "") + said)
                    st.rerun()
                else:
                    st.caption("没太听清，再说一遍，或直接打字～")
            else:
                st.caption("（未安装 faster-whisper：先用打字。装好后录音即自动转写）")
    st.text_area(
        "倾倒", key="dump_area", height=160,
        placeholder=DEFAULT_DUMP.replace("……", "……\n"),
        label_visibility="collapsed",
    )
    if st.button("──　开始生成　──", use_container_width=True, type="primary"):
        raw = (st.session_state.get("dump_area", "") or "").strip() or DEFAULT_DUMP
        st.session_state.view = "journal" if st.session_state.channel == "sensory" else "map"
        with st.spinner("水波正在归位 …"):
            st.session_state.result = pipeline.generate(raw)
        goto("sorting")


# ====================== 屏 ④ AI 认知线程归位 ======================
elif st.session_state.screen == "sorting":
    res = st.session_state.get("result") or pipeline.run_demo()
    st.markdown("<div class='m-ask'>水波正在归位 …</div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='display:flex;justify-content:center;margin:10px 0;'>"
        "<div class='breath' style='width:96px;height:96px;animation-duration:5s'></div></div>",
        unsafe_allow_html=True,
    )
    chips = "　".join(f"{CAT_EMOJI.get(t['category'], '·')} {t['category']}" for t in res["threads"])
    st.markdown(f"<div class='hint'>{chips}</div>", unsafe_allow_html=True)
    st.write("")
    # 逐行浮现，让用户感到「被认真对待」（PDF：停留数秒的整理仪式）
    ph = st.empty()
    shown = []
    for t in res["threads"][:3]:
        shown.append(f"<div class='calm' style='font-size:1.0rem'>· 接住了一个{t['category']}：{t['label']} …</div>")
        ph.markdown("".join(shown), unsafe_allow_html=True)
        time.sleep(1.2)
    time.sleep(0.5)
    if st.button("看看整理好的 →", use_container_width=True, type="primary"):
        goto("output")
    if res.get("_error"):
        st.caption("（演示数据：真实调用未成功 —— 配 ANTHROPIC_API_KEY，或本机登录 Claude Code 复用其订阅）")


# ====================== 屏 ⑤ 输出（思维导图 ⇄ 夜间日志）======================
elif st.session_state.screen == "output":
    res = st.session_state.get("result") or pipeline.run_demo()
    is_map = st.session_state.view == "map"
    top1, top2 = st.columns([3, 1])
    with top1:
        title = (f"今晚 · {DATE_CN} · {res['title']}" if is_map
                 else f"{DATE_CN} · {WEEK_CN} · {res['title']}")
        st.markdown(f"<div class='m-sub' style='text-align:left;margin:0'>{title}</div>",
                    unsafe_allow_html=True)
    with top2:
        if st.button("📜 日志" if is_map else "🪨 导图", use_container_width=True):
            st.session_state.view = "journal" if is_map else "map"
            st.rerun()

    if is_map:
        # 理性 · 思维导图：中心立石 = 今晚主题，分支 = 各类线程
        st.markdown(POND, unsafe_allow_html=True)
        threads = res["threads"]
        cols = st.columns(max(len(threads), 1))
        for col, t in zip(cols, threads):
            col.markdown(
                f"<div style='text-align:center'>{CAT_EMOJI.get(t['category'], '·')}<br>"
                f"<b style='color:#dceee6'>{t['category']}</b><br>"
                f"<span class='hint' style='font-size:.78rem'>{t['label']}</span></div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div class='hint' style='margin-top:14px'>"
                    "分支即今晚的几条线程 · 已替你归好位</div>", unsafe_allow_html=True)
    else:
        # 感性 · 夜间日志：AI 第一人称重述
        with st.container(border=True):
            st.markdown(
                f"<div class='calm' style='font-size:1.0rem;text-align:left'>"
                f"{res['journal']}</div>", unsafe_allow_html=True)

    # 明日第一步：把「启动」交给明天的外部世界（守红线：奖励开始，不发清单）
    with st.container(border=True):
        st.markdown(
            f"<div style='text-align:left'>🌱 <b style='color:#dceee6'>明日第一步</b><br>"
            f"<span class='calm' style='font-size:.98rem'>{res['tomorrow_first_step']}</span></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    if st.button("──　🌙 封存今晚　──", use_container_width=True, type="primary"):
        goto("rating")


# ====================== 屏 ⑥ 评分（反馈训练）======================
elif st.session_state.screen == "rating":
    st.markdown("<div class='m-ask'>帮我更懂你一些</div>", unsafe_allow_html=True)
    st.markdown("<div class='hint'>你的反馈会沉入池底，被慢慢记住</div>",
                unsafe_allow_html=True)
    st.write("")
    st.markdown("**① 今晚的整理，贴近你了吗？**")
    st.select_slider("贴近度", options=["不像", "一点", "还行", "挺像", "完全是"],
                     value="挺像", label_visibility="collapsed")
    st.markdown("**② 哪部分最贴近？**（可多选）")
    c = st.columns(2)
    c[0].checkbox("任务的归类"); c[0].checkbox("情绪的命名", value=True)
    c[1].checkbox("整体的语气"); c[1].checkbox("最后那句「看见」", value=True)
    st.markdown("**③ 哪里可以更好？**（可选）")
    st.text_input("更好", placeholder="轻轻说一句，或留空", label_visibility="collapsed")
    st.write("")
    if st.button("──　沉入池底　──", use_container_width=True, type="primary"):
        goto("sealed")


# ====================== 屏 ⑦ 封存过渡 ======================
elif st.session_state.screen == "sealed":
    st.write("")
    st.markdown(POND, unsafe_allow_html=True)
    st.markdown("<div class='calm'>今晚已被池塘收下</div>", unsafe_allow_html=True)
    st.markdown("<div class='hint'>· · ·</div>", unsafe_allow_html=True)
    st.write("")
    if st.button("跟着呼吸，慢慢降落 →", use_container_width=True, type="primary"):
        st.session_state.landing_dim = False
        goto("landing")


# ====================== 屏 ⑧ 降落引导（呼吸 → 渐暗 → 晚安）======================
elif st.session_state.screen == "landing":
    if not st.session_state.get("landing_dim"):
        res = st.session_state.get("result") or pipeline.run_demo()
        st.markdown("<div class='breath'></div>", unsafe_allow_html=True)
        st.markdown("<div class='hint'>跟着圆呼吸 · 吸气 4 · 屏息 1 · 呼气 6</div>",
                    unsafe_allow_html=True)
        # 降落语音（D）：本机 say 合成舒缓引导语，自动播放（无 say 则静默退回纯文字）
        voice = tts.synth(landing_narration(res)) if tts.available() else None
        if voice:
            st.audio(voice, format="audio/wav", autoplay=True)
        st.write("")
        for line in LANDING_SCRIPT:
            st.markdown(f"<div class='calm'>{line}</div>", unsafe_allow_html=True)
        st.markdown("<div class='hint' style='margin-top:18px'>▮▮▮▮▮▮▯▯▯▯　03:24</div>",
                    unsafe_allow_html=True)
        st.write("")
        if st.button("让屏幕暗下来 →", use_container_width=True):
            st.session_state.landing_dim = True
            st.rerun()
    else:
        # 渐暗 + 熄屏前留言（CSS 动画自动播放）
        st.markdown("<div class='dimmer'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='dim-msg'>"
            "现在，可以把手机放在床边了<br><br>"
            "明天早上，Murmora 会在这里<br><br>"
            "▲<br>晚　安"
            "</div>",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("（明早）我醒了", use_container_width=True):
            st.session_state.screen = "splash"
            st.session_state.landing_dim = False
            st.rerun()
