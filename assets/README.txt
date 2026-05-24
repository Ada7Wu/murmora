降落音（D′）放这里 —— 降落屏（⑧）会自动循环播放，取代旧的 say 朗读。

src/focus_audio.py 按「名字前缀」优先级找文件，扩展名 .ogg/.mp3/.m4a/.wav/.opus/.flac 都行：

  landing.*   首选（专为降落屏准备的助眠/专注音）
  bowl.*      颂钵
  drip.*      水滴
  water.*     水声
  rain.*      雨声
  forest.*    林间
  stream.*    溪流

挑选建议（适合 ADHD 睡前/专注）：很安静、低信息密度、无人声、无突变；会自动 loop。
没有任何文件时 → 用 numpy 合成的「很安静的颂钵 + 稀疏水滴」兜底。

── 当前已放入的素材 ──
landing.wav
  很安静的颂钵敲击（90s, mono, ~3.8MB；6 声稀疏敲击落在静默之上，peak≈0.22）。
  取自真实录音的第一声轻敲 + 自然衰减，剔除了原录音里连续的摩擦「singing」段，重排为稀疏循环并整体压低音量。
  原素材：Wikimedia Commons «Small tibetan singing bowl.ogg»，作者 Cassa342。
  授权：CC BY-SA 4.0（本派生文件同样以 CC BY-SA 4.0 提供；已注明出处、作者与修改）。
  https://commons.wikimedia.org/wiki/File:Small_tibetan_singing_bowl.ogg

想换风格：丢一个文件命名 landing.*（或 bowl.*/water.* 等）即自动优先用。
免费素材：Wikimedia Commons / pixabay.com/sound-effects（注意授权，优先 CC0；CC-BY/CC-BY-SA 需在此注明出处与作者）。
