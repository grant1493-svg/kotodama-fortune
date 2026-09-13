'use strict';
const data = JSON.parse(document.getElementById('storyData').textContent);
const scenes = data.scenes;
const $ = id => document.getElementById(id);
const positions = ['0% 0%', '100% 0%', '0% 100%', '100% 100%'];
let index = 0, timer = null, started = false, finalShown = false, actionChosen = false;
const measurementId = 'G-XMQ7M4M5J1';
let consent = false, analyticsLoaded = false;
try { consent = localStorage.getItem('kotodama_story_metrics') === 'yes'; } catch (_) {}
function event(name) {
  if (consent && typeof window.gtag === 'function') {
    window.gtag('event', name, {story_id: data.id, page_title: '言霊ものがたり', page_location: location.origin + location.pathname, page_referrer: ''});
  }
}
function configureMetrics() {
  window['ga-disable-' + measurementId] = !consent;
  $('metrics').textContent = consent ? '利用状況の計測を停止する' : '利用状況の計測を許可する';
  if (!consent || analyticsLoaded) return;
  analyticsLoaded = true;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function(){window.dataLayer.push(arguments);};
  window.gtag('js', new Date());
  window.gtag('config', measurementId, {send_page_view: false, page_title: '言霊ものがたり', page_location: location.origin + location.pathname, page_referrer: ''});
  const script = document.createElement('script');
  script.async = true; script.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
  document.head.appendChild(script);
  event('story_view');
}
$('metrics').onclick = () => {
  consent = !consent;
  try { localStorage.setItem('kotodama_story_metrics', consent ? 'yes' : 'no'); } catch (_) {}
  configureMetrics();
};
function startEvent() {if (!started) {started = true; event('story_start');}}
function stop() {
  clearInterval(timer); timer = null;
  $('play').textContent = index === 3 ? '↺ はじめから読む' : index === 0 ? '▶ 32秒で読む' : '▶ ここから自動で読む';
}
function render() {
  const scene = scenes[index];
  $('chapter').textContent = `0${index + 1} / 04 — ${scene[0]}`;
  $('narration').textContent = scene[1];
  $('art').style.backgroundPosition = positions[index];
  $('art').setAttribute('aria-label', scene[2]);
  $('prev').disabled = index === 0; $('next').disabled = index === 3;
  document.querySelectorAll('.dot').forEach((dot, i) => dot.classList.toggle('active', i === index));
  if (index === 3 && !finalShown) {finalShown = true; event('story_final_scene');}
}
$('prev').onclick = () => {stop(); index = Math.max(0, index - 1); render(); stop();};
$('next').onclick = () => {stop(); startEvent(); index = Math.min(3, index + 1); render(); stop();};
$('play').onclick = () => {
  if (timer) {stop(); return;}
  if (index === 3) index = 0;
  startEvent(); render(); $('play').textContent = 'Ⅱ 一時停止';
  timer = setInterval(() => {if (index < 3) {index++; render();} else {stop();}}, 8000);
};
document.addEventListener('visibilitychange', () => {if (document.hidden) stop();});
$('done').onclick = () => {
  $('status').textContent = $('reflection').value.trim() ? 'その一言を、今日のきっかけに。無理のないタイミングで。' : '書かずに、心の中で決めても大丈夫。';
  if (!actionChosen) {actionChosen = true; event('story_action');}
};
configureMetrics();
