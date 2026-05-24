"""Murmora 秘落 — 睡前思绪「降落」器（v2 初版 · 八屏可视化）

> 这是 v2 的【初版可视化】：用 Streamlit 把 PDF《降落之选》的八屏闭环先「走通看见」。
> 内容为 mock（PDF 的「池中之石」示例），重点是把流程、暗色水塘质感、呼吸/渐暗的感官体验
> 先呈现出来。接真实 AI 管线（pipeline.py）/ 语音转写 / TTS 降落语音是【最终版】的事，
> 详见 docs/design/v2-降落之选.md 与 docs/TODO.md。

运行：  streamlit run src/app.py    （务必在项目根目录执行，.streamlit/ 主题才生效）
"""
import base64
import datetime as _dt
import hashlib
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import db
import focus_audio
import pipeline
import stt

# 品牌 logo：水波勾出的「M」+ 石子落池涟漪。两份：
#   - murmora-logo.jpeg：带底色，做浏览器页签 favicon（任意标签栏底色都可见）。
#   - murmora-logo.png ：透明描边版，做启动屏 ① 主视觉（叠在任意背景上都无缝）。
_ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO_ICON = _ASSETS / "murmora-logo.jpeg"
LOGO_MARK = _ASSETS / "murmora-logo.png"


@st.cache_data
def logo_data_uri():
    """把透明 logo 内联成 base64 data URI（缓存一次），本地与 Streamlit Cloud 都免静态托管。"""
    return "data:image/png;base64," + base64.b64encode(LOGO_MARK.read_bytes()).decode()


st.set_page_config(
    page_title="Murmora 秘落",
    page_icon=str(LOGO_ICON) if LOGO_ICON.exists() else "🌲",
    layout="centered",
)


@st.cache_resource
def _ensure_db():
    """建表一次（entries/threads/ratings）。失败不拦路——落库是锦上添花，不能拖垮降落流程。"""
    try:
        db.init_db()
    except Exception:
        pass
    return True


_ensure_db()

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


@st.cache_data(show_spinner=False)
def landing_audio():
    """降落屏的 ADHD 舒缓环境声（D′）：assets/ 里有 CC0 音频（landing/drip/water…）就用它，
    否则用 numpy 合成的「很安静的水滴声」兜底（见 src/focus_audio.py）。取代 v2.2 的 macOS say 朗读——
    睡前不再有人「说话」，只留低刺激、可循环的环境声，让注意力从「想」落到「听」。
    返回 (data_or_path, mime, source)；缓存一次，避免每次 rerun 重算合成。"""
    return focus_audio.get()


def when_cn(days):
    """召回片段的时间措辞（UI 用）。"""
    if days == 0:
        return "今天早些时候"
    if days == 1:
        return "昨晚"
    return f"{days}天前" if days else "前些天"

# ============================================================
# 全局样式 —— v4 晨露胶片 morning dew film（冷雾林·胶片调）
#   色卡（语义 token in :root）：松墨 #22393c / 远山青 #46707e / 苔绿 #6b8b81
#     / sage #afbb98 / 晨陶米 #cecdb9。文字晨陶米(主)+sage(次)，交互远山青，强调 sage。
#   母题：冷松墨渐变 + 谷中横向漂浮晨雾带 + 几何冷松林镜像入池 + 同心涟漪 + 晨露微光（冷调，取代暖萤火）。
#   字体：Lora 衬线（字标/标题，胶片 editorial 气质）+ Raleway（正文）。a11y：文字≥4.5:1、focus 环、reduced-motion。
#   详见 docs/design/v4-晨露胶片.md（依 ui-ux-pro-max + frontend-design 两 skill 落地）。
# ============================================================
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Raleway:wght@300;400;500;600&display=swap');
      #MainMenu, footer, header {visibility:hidden;}

      /* ===== 晨露胶片 morning dew film · 语义色 token（色卡：松墨/远山青/苔绿/sage/晨陶米）===== */
      :root{
        --pine:#22393c;        /* Pine Black 松墨（最深锚点） */
        --horizon:#46707e;     /* Tooth Horizon 远山青（雾蓝，交互色） */
        --moss:#6b8b81;        /* Pale Moss 苔灰绿 */
        --sage:#afbb98;        /* 鼠尾草绿（高亮/强调） */
        --clay:#cecdb9;        /* Morning Clay 晨陶米（主文字） */
        --text:var(--clay);          /* 主文字 ~7.5:1 on pine */
        --text-soft:var(--sage);     /* 次文字 ~6:1 */
        --text-mute:#a7bbac;         /* 弱文字（苔绿提亮，保 ≥4.5:1） */
        --line:rgba(175,187,152,.30);
        --surface:rgba(34,57,60,.55);
        --fog:rgba(206,205,185,.16); /* 晨雾（晨陶米低透明） */
        --radius:16px;
        --ease:cubic-bezier(.22,.61,.36,1);
      }
      html, body, .stApp, [data-testid="stAppViewContainer"]{
        font-family:'Raleway', -apple-system, BlinkMacSystemFont,
                    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;}

      /* —— 晨露雾林背景：冷松墨渐变 + 谷中天光晨雾 —— */
      .stApp {
        background:
          radial-gradient(62% 26% at 50% 7%, rgba(206,205,185,.17), transparent 70%),
          radial-gradient(48% 22% at 68% 16%, rgba(175,187,152,.10), transparent 72%),
          linear-gradient(to bottom, #2a474d 0%, #244046 28%, #20393e 54%,
                          #1c3236 78%, #182b2e 100%);
        background-attachment: fixed;
      }
      [data-testid="stAppViewContainer"] .block-container {position:relative; z-index:1;}
      .block-container {max-width:430px; padding-top:2.0rem; padding-bottom:3rem;}

      /* —— 固定晨雾层（在内容之下）：谷中横向漂浮雾带 + 几点悬浮露珠 —— */
      .scene {position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden;}
      .scene .mist {position:absolute; left:-22%; right:-22%; height:150px; border-radius:50%;
        background:radial-gradient(closest-side, var(--fog), transparent);
        filter:blur(10px);}
      .scene .mist.m1{top:9%;  animation:fogdrift 28s ease-in-out infinite;}
      .scene .mist.m2{top:36%; opacity:.62; animation:fogdrift 36s ease-in-out infinite reverse;}
      .scene .mist.m3{top:66%; opacity:.5;  animation:fogdrift 32s ease-in-out infinite;}
      @keyframes fogdrift{0%,100%{transform:translateX(-6%)}50%{transform:translateX(6%)}}
      .scene .spore {position:absolute; width:3px; height:3px; border-radius:50%;
        background:var(--clay); opacity:.4; box-shadow:0 0 7px rgba(206,205,185,.6);
        animation:drift 16s ease-in-out infinite;}
      .scene .spore:nth-of-type(1){left:18%; top:16%; animation-delay:0s}
      .scene .spore:nth-of-type(2){left:74%; top:12%; animation-delay:4s}
      .scene .spore:nth-of-type(3){left:58%; top:22%; animation-delay:8s}
      .scene .spore:nth-of-type(4){left:32%; top:9%;  animation-delay:12s}
      @keyframes drift{0%,100%{transform:translateY(0);opacity:.3}50%{transform:translateY(-12px);opacity:.55}}

      .stButton button {
        border-radius:var(--radius); height:3rem; font-size:1.02rem; font-weight:500;
        letter-spacing:.04em;
        border:1px solid var(--line); background:var(--surface); color:var(--text);
        backdrop-filter:blur(4px); transition:border-color .22s var(--ease),
          box-shadow .22s var(--ease), transform .12s var(--ease);
      }
      .stButton button:hover {border-color:var(--sage); color:#eef0e3;
        box-shadow:0 0 0 1px rgba(175,187,152,.22), 0 6px 20px rgba(0,0,0,.18);}
      .stButton button:active {transform:scale(.985);}
      .stButton button:focus-visible {outline:2px solid var(--sage); outline-offset:2px;}

      /* —— 品牌 logo（启动屏主视觉）：透明描边版，叠任意背景无缝；冷调晨光晕 + 呼吸 —— */
      .m-logo {text-align:center; margin:10px 0 2px;}
      .m-logo img {width:208px; height:208px; object-fit:contain;
                   filter:drop-shadow(0 0 26px rgba(206,205,185,.30));
                   animation:logo-breathe 7s ease-in-out infinite;}
      @keyframes logo-breathe {0%,100%{opacity:.9; transform:scale(1)}
                               50%{opacity:1; transform:scale(1.025)}}

      /* —— 字体：Lora 衬线做品牌字标/标题（胶片·editorial 气质），Raleway 做正文 —— */
      .m-title  {text-align:center; letter-spacing:.42em; font-size:1.7rem;
                 font-family:'Lora',Georgia,serif; font-weight:500;
                 color:var(--clay); margin:8px 0 2px; padding-left:.42em;
                 text-shadow:0 0 26px rgba(206,205,185,.28);}
      .m-sub    {text-align:center; font-family:'Lora',Georgia,serif; font-style:italic;
                 color:var(--text-soft); font-size:.98rem; margin:6px 0 18px;
                 letter-spacing:.02em;}
      .m-ask    {text-align:center; font-family:'Lora',Georgia,serif; color:var(--clay);
                 font-size:1.26rem; font-weight:500; margin:10px 0 6px;}
      .calm     {text-align:center; color:var(--text); font-size:1.12rem; line-height:2.0;
                 margin:8px 6px;}
      .hint     {color:var(--text-mute); text-align:center; font-size:.9rem;}
      .stars    {color:var(--moss); text-align:center; letter-spacing:.35em;
                 font-size:.8rem; margin:4px 0;}

      /* —— 通道图标（②降落岛 感性/理性，几何 SVG 取代 emoji；色卡描边 + 冷光晕）—— */
      .chan-ic {display:flex; justify-content:center; margin:2px 0 4px;}
      .chan-ic svg {filter:drop-shadow(0 0 10px rgba(206,205,185,.22));}
      .chan-ic .s  {stroke:var(--sage);}            /* sage 主描边 */
      .chan-ic .c  {stroke:var(--clay);}            /* 晨陶米 细节 */
      .chan-ic .cf {fill:var(--clay);}
      .chan-ic .sf {fill:rgba(175,187,152,.14);}

      /* —— 几何雾林倒映池塘（多屏复用）：冷松林 + 镜像倒影 + 水线 + 同心涟漪 + 苔叶 + 晨露微光 —— */
      .pond {position:relative; height:196px; margin:8px 0 14px; overflow:hidden;}
      .grove {position:absolute; left:0; right:0; height:98px; top:0;}
      .grove.ref {top:98px; transform:scaleY(-1); opacity:.5;
        filter:blur(1.4px) brightness(.78) saturate(.98);
        -webkit-mask:linear-gradient(to bottom,#000,rgba(0,0,0,.2) 82%,transparent);
                mask:linear-gradient(to bottom,#000,rgba(0,0,0,.2) 82%,transparent);}
      .pond .tree {position:absolute; bottom:0; transform-origin:bottom center;
        clip-path:polygon(50% 0,62% 28%,56% 28%,72% 60%,63% 60%,82% 100%,18% 100%,37% 60%,28% 60%,44% 28%,38% 28%);
        background:linear-gradient(101deg,
          color-mix(in srgb, var(--g,#46707e) 100%, #cecdb9 18%) 0 50%, var(--g,#46707e) 50% 100%);}
      /* 晨露微光（取代暖萤火，转冷调）：sage→苔绿的露珠辉光 */
      .pond .firefly {position:absolute; width:9px; height:9px; border-radius:50%; z-index:2;
        background:radial-gradient(circle at 40% 38%, #f0efe0, var(--sage) 55%, var(--moss) 100%);
        box-shadow:0 0 12px 3px rgba(206,205,185,.5), 0 0 28px 10px rgba(175,187,152,.2);
        animation:float 7s ease-in-out infinite, pulse 4s ease-in-out infinite;}
      @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
      @keyframes pulse{0%,100%{filter:brightness(.92)}50%{filter:brightness(1.18)}}
      .pondline {position:absolute; left:0; right:0; top:98px; height:2px;
        background:linear-gradient(90deg,transparent,rgba(206,205,185,.5),transparent);}
      .surface {position:absolute; inset:0; pointer-events:none;}
      .ripple {position:absolute; left:50%; top:118px; width:48px; height:15px;
        border:1px solid rgba(175,187,152,.42); border-radius:50%;
        opacity:0; animation:rip 7s ease-out infinite;}
      .ripple:nth-child(2){animation-delay:2.3s;}
      .ripple:nth-child(3){animation-delay:4.6s;}
      @keyframes rip {0%{transform:translateX(-50%) scale(.4); opacity:.6}
                      100%{transform:translateX(-50%) scale(4.2); opacity:0}}
      .lotus {position:absolute; border-radius:50%;
        background:radial-gradient(circle at 42% 38%, var(--moss), var(--pine) 82%);}
      .lotus.l1{left:26%; top:128px; width:30px; height:12px;}
      .lotus.l2{right:24%; top:150px; width:24px; height:9px;}

      /* —— 呼吸圈 4-1-6（降落屏）—— */
      .breath {width:120px;height:120px;border-radius:50%;margin:6px auto;
               background:radial-gradient(circle,var(--sage),var(--pine));
               box-shadow:0 0 50px rgba(175,187,152,.34);
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
                color:var(--clay); text-align:center; line-height:2.1; font-size:1.1rem;
                font-family:'Lora',Georgia,serif;
                animation:msgin 9s ease-in forwards; pointer-events:none;}
      @keyframes msgin {0%,55%{opacity:0} 100%{opacity:.85}}

      /* —— 无障碍：尊重系统「减少动态效果」，关掉装饰动画（a11y · reduced-motion）—— */
      @media (prefers-reduced-motion: reduce){
        *, *::before, *::after {animation:none !important; transition:none !important;}
      }
    </style>
    <div class="scene">
      <div class="mist m1"></div><div class="mist m2"></div><div class="mist m3"></div>
      <span class="spore"></span><span class="spore"></span><span class="spore"></span><span class="spore"></span>
    </div>
    """,
    unsafe_allow_html=True,
)

STARS = "<div class='stars'>·　˙　·　·　˙　·　·　˙　·　·　˙　·</div>"

# 通道图标（呼应核心隐喻「池中之石」）：感性=石落涟漪荡开，理性=把事理成一块立石。
# 装饰性（旁有文字标签），故 aria-hidden；描边走色卡 token（见 .chan-ic CSS）。
ICON_SENSORY = """
<div class="chan-ic"><svg width="46" height="46" viewBox="0 0 46 46" fill="none"
     stroke-width="2" stroke-linecap="round" aria-hidden="true">
  <ellipse class="s" cx="23" cy="29" rx="17" ry="6"  opacity=".5"/>
  <ellipse class="s" cx="23" cy="28" rx="11" ry="4"  opacity=".82"/>
  <path    class="c" d="M23 19 L23 24" opacity=".7"/>
  <circle  class="cf" cx="23" cy="15.5" r="3.4"/>
</svg></div>
"""
ICON_RATIONAL = """
<div class="chan-ic"><svg width="46" height="46" viewBox="0 0 46 46" fill="none"
     stroke-width="2" stroke-linejoin="round" stroke-linecap="round" aria-hidden="true">
  <path class="s sf" d="M23 8 L34 17 L30 34 L16 34 L12 17 Z"/>
  <path class="c" d="M23 8 L23 21 M12 17 L23 21 L34 17 M16 34 L23 21 L30 34"
        opacity=".55" stroke-width="1.4"/>
</svg></div>
"""

POND = """
<div class="pond">
  <div class="grove">
    <i class="tree" style="left:4%;  width:40px; height:78px; --g:#2f5560"></i>
    <i class="tree" style="left:24%; width:50px; height:92px; --g:#46707e"></i>
    <i class="tree" style="left:46%; width:34px; height:64px; --g:#22393c"></i>
    <i class="tree" style="left:64%; width:48px; height:88px; --g:#6b8b81"></i>
    <i class="tree" style="left:84%; width:40px; height:74px; --g:#46707e"></i>
    <div class="firefly" style="left:46%; bottom:64px"></div>
  </div>
  <div class="grove ref" aria-hidden="true">
    <i class="tree" style="left:4%;  width:40px; height:78px; --g:#2f5560"></i>
    <i class="tree" style="left:24%; width:50px; height:92px; --g:#46707e"></i>
    <i class="tree" style="left:46%; width:34px; height:64px; --g:#22393c"></i>
    <i class="tree" style="left:64%; width:48px; height:88px; --g:#6b8b81"></i>
    <i class="tree" style="left:84%; width:40px; height:74px; --g:#46707e"></i>
    <div class="firefly" style="left:46%; bottom:64px"></div>
  </div>
  <div class="pondline"></div>
  <div class="surface">
    <div class="ripple"></div><div class="ripple"></div><div class="ripple"></div>
    <div class="lotus l1"></div><div class="lotus l2"></div>
  </div>
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
    st.markdown(f"<div class='m-logo'><img src='{logo_data_uri()}' alt='Murmora'></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='m-title'>MURMORA</div>", unsafe_allow_html=True)
    st.markdown("<div class='m-sub'>夜林如墨　池塘倒映整片森林</div>", unsafe_allow_html=True)
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
        st.markdown(ICON_SENSORY, unsafe_allow_html=True)
        st.markdown("<div class='calm' style='font-size:1.05rem'>感 性<br>"
                    "<span class='hint'>想说点什么</span></div>", unsafe_allow_html=True)
        if st.button("从这里降落", key="sens", use_container_width=True):
            st.session_state.channel = "sensory"
            st.session_state.view = "journal"
            goto("dump")
    with c2:
        st.markdown(ICON_RATIONAL, unsafe_allow_html=True)
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
        # G3 似曾相识：先用今晚原文召回过往线程，喂给 LLM 让它可「记得你」
        try:
            recall = db.recall_similar(raw)
        except Exception:
            recall = []
        st.session_state.recall = recall
        with st.spinner("水波正在归位 …"):
            st.session_state.result = pipeline.generate(raw, history=recall)
        # E 落库：整理完即存这一夜（含线程，供下次召回）；存不上也不拦路
        try:
            st.session_state.entry_id = db.save_entry(
                raw, st.session_state.channel, st.session_state.result)
        except Exception:
            st.session_state.entry_id = None
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
        if st.button("⇆ 日志" if is_map else "⇆ 导图", use_container_width=True):
            st.session_state.view = "journal" if is_map else "map"
            st.rerun()

    # G3 似曾相识：今晚命中过往线程时，轻轻一句「记得你」（温柔，不翻旧账）
    recall = st.session_state.get("recall") or []
    if recall:
        r0 = recall[0]
        st.markdown(
            f"<div class='hint' style='text-align:left;margin:-2px 0 8px'>"
            f"· 似曾相识 · {when_cn(r0.get('days_ago'))}你也曾为「{r0['label']}」停留过</div>",
            unsafe_allow_html=True,
        )

    if is_map:
        # 理性 · 思维导图：中心立石 = 今晚主题，分支 = 各类线程
        st.markdown(POND, unsafe_allow_html=True)
        threads = res["threads"]
        cols = st.columns(max(len(threads), 1))
        for col, t in zip(cols, threads):
            col.markdown(
                f"<div style='text-align:center'>{CAT_EMOJI.get(t['category'], '·')}<br>"
                f"<b style='color:var(--clay)'>{t['category']}</b><br>"
                f"<span class='hint' style='font-size:.78rem'>{t['label']}</span></div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div class='hint' style='margin-top:14px'>"
                    "分支即今晚的几条线程 · 已替你归好位</div>", unsafe_allow_html=True)
    else:
        # 感性 · 「今夜封存」四段之 ① 你说了什么：整理成可回看的叙事 + 一句「看见」
        with st.container(border=True):
            st.markdown(
                f"<div style='text-align:left'><b style='color:var(--clay)'>你说了什么</b><br>"
                f"<span class='calm' style='font-size:1.0rem'>{res['journal']}</span></div>",
                unsafe_allow_html=True)
        # ② 抚慰疗愈：点出今晚他在承担的身份 + 温柔理解（只抚慰，不说教）
        with st.container(border=True):
            st.markdown(
                f"<div style='text-align:left'>🫂 <b style='color:var(--clay)'>抚慰疗愈</b><br>"
                f"<span class='calm' style='font-size:.98rem'>{res.get('soothe', '')}</span></div>",
                unsafe_allow_html=True)

    # ④ 明天只做一步：把「启动」交给明天的外部世界（守红线：奖励开始，不发清单）
    with st.container(border=True):
        st.markdown(
            f"<div style='text-align:left'>🌱 <b style='color:var(--clay)'>明日第一步</b><br>"
            f"<span class='calm' style='font-size:.98rem'>{res['tomorrow_first_step']}</span></div>",
            unsafe_allow_html=True,
        )

    # ⑤ 睡前落点（仅感性）：治愈性收束，可引公版文学（标来源），结尾「今晚已经被保存」
    if not is_map and res.get("closing"):
        src = (res.get("closing_source") or "").strip()
        src_html = (f"<div class='hint' style='text-align:right;margin-top:8px'>—— {src}</div>"
                    if src else "")
        with st.container(border=True):
            st.markdown(
                f"<div style='text-align:left'>🌙 <b style='color:var(--clay)'>睡前落点</b><br>"
                f"<span class='calm' style='font-size:.98rem'>{res['closing']}</span>{src_html}</div>",
                unsafe_allow_html=True)

    st.write("")
    if st.button("──　🌲 封存今晚　──", use_container_width=True, type="primary"):
        goto("rating")


# ====================== 屏 ⑥ 评分（反馈训练）======================
elif st.session_state.screen == "rating":
    st.markdown("<div class='m-ask'>帮我更懂你一些</div>", unsafe_allow_html=True)
    st.markdown("<div class='hint'>你的反馈会沉入池底，被慢慢记住</div>",
                unsafe_allow_html=True)
    st.write("")
    st.markdown("**① 今晚的整理，贴近你了吗？**")
    closeness = st.select_slider(
        "贴近度", options=["不像", "一点", "还行", "挺像", "完全是"],
        value="挺像", label_visibility="collapsed", key="r_closeness")
    st.markdown("**② 哪部分最贴近？**（可多选）")
    c = st.columns(2)
    p_task = c[0].checkbox("任务的归类", key="r_p_task")
    p_emo = c[0].checkbox("情绪的命名", value=True, key="r_p_emo")
    p_tone = c[1].checkbox("整体的语气", key="r_p_tone")
    p_seen = c[1].checkbox("最后那句「看见」", value=True, key="r_p_seen")
    st.markdown("**③ 哪里可以更好？**（可选）")
    note = st.text_input("更好", placeholder="轻轻说一句，或留空",
                         label_visibility="collapsed", key="r_note")
    st.write("")
    if st.button("──　沉入池底　──", use_container_width=True, type="primary"):
        # E 反馈训练：贴近度 + 哪部分最贴近 + 自由文本 → ratings（存不上也不拦路）
        parts = [name for name, on in (
            ("任务的归类", p_task), ("情绪的命名", p_emo),
            ("整体的语气", p_tone), ("最后那句看见", p_seen)) if on]
        try:
            db.save_rating(st.session_state.get("entry_id"), closeness, parts, note)
        except Exception:
            pass
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
        st.markdown("<div class='breath'></div>", unsafe_allow_html=True)
        st.markdown("<div class='hint'>跟着圆呼吸 · 吸气 4 · 屏息 1 · 呼气 6</div>",
                    unsafe_allow_html=True)
        # 降落音（D′）：ADHD 舒缓环境声替代朗读——循环轻放、自动播放，随呼吸圈把注意力从「想」落到「听」。
        data, mime, _src = landing_audio()
        st.audio(data, format=mime, autoplay=True, loop=True)
        if _src == "synth":   # 合成的是很安静的水滴声
            st.markdown("<div class='hint'>· 很轻的水滴声，跟着它慢慢沉下去 ·</div>",
                        unsafe_allow_html=True)
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
