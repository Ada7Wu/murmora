降落音（D′）放这里 —— 降落屏（⑧）会自动循环播放，取代旧的 say 朗读。

src/focus_audio.py 按下面顺序找文件，找到第一个就用它：

  landing.mp3     首选（专为降落屏准备的助眠音）
  drip.mp3        水滴
  water.mp3       水声
  rain.mp3        雨声
  forest.mp3      林间
  stream.mp3      溪流

挑选建议（适合 ADHD 睡前）：很安静、低信息密度、无人声、无突变；
水滴/轻雨/溪流皆可，时长几十秒即可（会 loop）。

没有任何文件也不影响运行——会用 numpy 合成的「很安静的水滴声」兜底，路演不会失声。
免费素材可去 pixabay.com/sound-effects 等站点下载（注意授权，优先 CC0）。
