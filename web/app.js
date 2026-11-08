(() => {
  'use strict';
  const moves = window.GOMOKU_DEMO_MOVES || [];
  const stats = window.GOMOKU_BENCHMARK || {};
  const $ = (id) => document.getElementById(id);
  const video = $('video');
  const slider = $('timeline');
  const canvas = $('board');
  const context = canvas.getContext('2d');
  const FPS = 30, FRAMES = 961;
  let language = 'en';
  let lastRenderedMove = -1;
  const strings = {
    en: {hero:'Computer vision meets Gomoku',subtitle:'Explore a synchronized, self-generated 41-move game in your browser. Windows WPF performs actual recognition; this page is a deterministic reference replay, not a browser-based detector.',readme:'Read project README',benchmarkEvidence:'View benchmark evidence',frames:'Source frames',moves:'Recorded moves',benchmarks:'Windows test cases',winner:'Final winner',videoTitle:'Original synthetic video',videoSub:'One timeline for video and move replay',videoHint:'Press Play to start synchronized replay',playback:'Playback',framePosition:'Video frame',boardTitle:'Synchronized board',boardSub:'Confirmed moves from the synthetic reference timeline',greenBoxes:'Green boxes',moveLog:'Move log',moveLogSub:'Select a move to seek both the video and board',benchTitle:'Three-language performance',benchSub:'Real Windows timing · 36 synthetic benchmark cases',core:'Detection core',pipe:'In-process pipeline',total:'End-to-end',important:'Interpretation matters',disclaimer:'MATLAB full-process time includes interpreter launch and shutdown. Playback labels do not change detector compute speed. These results do not establish real-world accuracy.',footer:'2025 academic assignment, modernized in 2026. Technical demonstration and educational sharing.',ready:'Ready — no moves yet',move:'Move',black:'Black',white:'White',play:'Play',pause:'Pause'},
    zh: {hero:'五子棋電腦視覺辨識與重播',subtitle:'在瀏覽器中探索自製的 41 手同步棋局。真正的影片辨識由 Windows WPF 執行；本頁使用合成棋譜重播，不會在瀏覽器內執行三語言辨識引擎。',readme:'閱讀專案說明',benchmarkEvidence:'查看測試證據',frames:'來源影格',moves:'完整落子',benchmarks:'Windows 測試組合',winner:'棋局勝方',videoTitle:'自行生成的合成棋局影片',videoSub:'影片與棋盤共用同一時間軸',videoHint:'按下播放開始同步重播',playback:'播放倍率',framePosition:'影片影格',boardTitle:'同步模擬棋盤',boardSub:'以合成影片的已知棋譜逐手更新',greenBoxes:'綠色棋框',moveLog:'落子清單',moveLogSub:'點擊棋步，同步定位影片與棋盤',benchTitle:'三語言效能比較',benchSub:'Windows 真實執行 · 36 組合成測試',core:'純辨識核心',pipe:'引擎內部處理',total:'程序完整耗時',important:'正確理解數據',disclaimer:'MATLAB 完整耗時包含外部程序啟動及結束。播放倍率不是演算法加速倍率，這組數據也不代表真實場景準確率。',footer:'2025 年課程期末作業，2026 年現代化升級。技術分享與學習展示。',ready:'尚未落子',move:'第',black:'黑棋',white:'白棋',play:'播放',pause:'暫停'}
  };
  const frameFromTime = () => Math.min(FRAMES, Math.max(1, Math.floor((video.currentTime + 0.00001) * FPS) + 1));
  const moveCount = (frame) => { let n=0; for (const m of moves){ if(m.frame <= frame) n++; else break; } return n; };
  const formatTime = (v) => {const s=Math.max(0,Math.floor(v));return Math.floor(s/60)+':'+String(s%60).padStart(2,'0');};
  function drawBoard(n) {
    const w=canvas.width, h=canvas.height, edge=45, step=(w-edge*2)/14;
    context.clearRect(0,0,w,h);context.fillStyle='#dfc7a0';context.fillRect(0,0,w,h);
    context.strokeStyle='#765b39';context.lineWidth=1.5;
    for (let i=0;i<15;i++){const pos=edge+i*step;context.beginPath();context.moveTo(pos,edge);context.lineTo(pos,h-edge);context.stroke();context.beginPath();context.moveTo(edge,pos);context.lineTo(w-edge,pos);context.stroke();}
    context.font='15px system-ui, sans-serif';context.fillStyle='#5d4a32';context.textAlign='center';context.textBaseline='middle';
    for(let i=0;i<15;i++){context.fillText(String.fromCharCode(65+i),edge+i*step,20);context.fillText(String(i+1),20,edge+i*step);}
    for(const [r,c] of [[4,4],[4,12],[8,8],[12,4],[12,12]]){context.beginPath();context.arc(edge+(c-1)*step,edge+(r-1)*step,4.5,0,Math.PI*2);context.fillStyle='#625038';context.fill();}
    moves.slice(0,n).forEach((m,index)=>{
      const x=edge+(m.col-1)*step,y=edge+(m.row-1)*step,rad=step*.39;
      context.beginPath();context.arc(x,y,rad,0,Math.PI*2);
      const grad=context.createRadialGradient(x-rad*.3,y-rad*.4,1,x,y,rad*1.4);
      if(m.color==='Black'){grad.addColorStop(0,'#69737d');grad.addColorStop(.45,'#242a32');grad.addColorStop(1,'#080b0f');}
      else{grad.addColorStop(0,'#fff');grad.addColorStop(.65,'#f5f4f0');grad.addColorStop(1,'#aeb6b9');}
      context.fillStyle=grad;context.fill();context.strokeStyle=m.color==='Black'?'#20252b':'#879299';context.lineWidth=1;context.stroke();
      if($('show-boxes').checked){context.strokeStyle='#25d67d';context.lineWidth=3;context.strokeRect(x-rad-3,y-rad-3,(rad+3)*2,(rad+3)*2);}
      if(index===n-1){context.beginPath();context.arc(x,y,3,0,Math.PI*2);context.fillStyle=m.color==='Black'?'#e9f7ff':'#263e55';context.fill();}
    });
  }
  function update(logScroll=false) {
    const frame=video.ended?FRAMES:frameFromTime();
    const n=moveCount(frame);
    slider.value=String(frame);
    $('frame-out').textContent=`${frame} / ${FRAMES}`;
    $('time-out').textContent=`${formatTime(video.currentTime)} / ${formatTime(FRAMES/FPS)}`;
    $('current-move').textContent=`${n} / ${moves.length} ${strings[language].moves.toLowerCase()}`;
    $('turn-number').textContent=`${strings[language].move} ${n} / ${moves.length}`;
    const m=moves[n-1];
    $('board-status').textContent=m?`${m.color==='Black'?strings[language].black:strings[language].white} ${m.position} · F${m.frame}`:strings[language].ready;
    if(n!==lastRenderedMove){drawBoard(n);lastRenderedMove=n;Array.from($('move-list').children).forEach((el,i)=>{el.classList.toggle('active',i===n-1);el.classList.toggle('future',i>=n);});if(logScroll&&n>0){$('move-list').children[n-1]?.scrollIntoView({block:'nearest'});}}
  }
  function seek(frame) {
    const safe=Math.min(FRAMES,Math.max(1,Math.round(frame)));
    // Keep the video and board driven by the same actual media position.
    video.currentTime=(safe-1)/FPS;
    update(true);
  }
  function setPlay(){const s=strings[language];$('play-label').textContent=(video.paused?'▶ '+s.play:'Ⅱ '+s.pause);$('video-hint').hidden=!video.paused||video.currentTime>0;}
  function renderList(){const list=$('move-list');list.replaceChildren();moves.forEach(m=>{const b=document.createElement('button');b.type='button';b.className='move-entry';b.setAttribute('aria-label',`${m.color} ${m.position}, frame ${m.frame}`);const idx=document.createElement('span');idx.className='count';idx.textContent=String(m.index).padStart(2,'0');const piece=document.createElement('span');piece.className='piece'+(m.color==='White'?' white':'');const label=document.createElement('span');label.textContent=(m.color==='Black'?strings[language].black:strings[language].white)+'  '+m.position;const f=document.createElement('span');f.className='frame';f.textContent='F'+m.frame;b.append(idx,piece,label,f);b.addEventListener('click',()=>seek(m.frame));list.append(b);});lastRenderedMove=-1;update();}
  function renderBenchmark(){let html='';for(const name of ['csharp','python','matlab']){const m=stats[name];if(!m)continue;const vals=[['core',m.recognition_mean_seconds],['pipe',m.pipeline_mean_seconds],['total',m.process_mean_seconds]];html+=`<div class="bench-row"><div class="bench-label"><span>${name==='csharp'?'C# / OpenCvSharp':name==='python'?'Python / OpenCV':'MATLAB'}</span><small>${m.runs} cases</small></div>`;for(const [t,val] of vals)html+=`<div class="bench-track ${t}" title="${t}: ${val.toFixed(3)} s"><span class="bar" style="width:${Math.min(100,val/28*100).toFixed(2)}%"></span></div>`;html+='</div>';}$('bench-chart').innerHTML=html;}
  function switchLang(){language=language==='en'?'zh':'en';document.documentElement.lang=language==='en'?'en':'zh-Hant';for(const el of document.querySelectorAll('[data-i18n]')){const key=el.dataset.i18n;el.textContent=strings[language][key]||el.textContent;}$('lang').textContent=language==='en'?'繁體中文':'English';renderList();setPlay();}
  if(moves.length!==41){$('board-status').textContent='Demo data unavailable';return;}
  $('lang').addEventListener('click',switchLang);
  $('play').addEventListener('click',async()=>{if(video.paused){if(video.ended){seek(1);}try{await video.play();}catch(e){$('video-hint').textContent='Video playback unavailable: '+e.message;$('video-hint').hidden=false;}}else video.pause();setPlay();});
  $('back').addEventListener('click',()=>{const n=moveCount(frameFromTime());seek(n<=1?1:moves[n-2].frame);});
  $('forward').addEventListener('click',()=>{const n=moveCount(frameFromTime());seek(n>=moves.length?FRAMES:moves[n].frame);});
  $('speed').addEventListener('change',()=>{video.playbackRate=Number($('speed').value);});
  slider.addEventListener('input',()=>seek(Number(slider.value)));
  $('show-boxes').addEventListener('change',()=>drawBoard(moveCount(frameFromTime())));
  for(const ev of ['timeupdate','seeked','loadedmetadata','ended'])video.addEventListener(ev,()=>{update(ev==='seeked');setPlay();});
  video.addEventListener('play',setPlay);video.addEventListener('pause',setPlay);video.addEventListener('error',()=>{ $('video-hint').textContent='Cannot load synthetic demo MP4. Check demo/full_game/full_game_961_web.mp4.';$('video-hint').hidden=false; });
  video.playbackRate=2;
  renderList();renderBenchmark();setPlay();
})();
