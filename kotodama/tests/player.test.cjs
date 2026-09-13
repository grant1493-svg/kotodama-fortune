const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function setup(){
 const els={}, writes=[], scripts=[];let tick;
 for(const id of ['storyData','metrics','chapter','narration','art','prev','next','play','done','status','reflection']) els[id]={textContent:'',value:'',style:{},setAttribute(){}};
 els.storyData.textContent=JSON.stringify({id:'bridge',scenes:[0,1,2,3].map(i=>['title'+i,'text'+i,'alt'+i])});
 const doc={getElementById:id=>els[id],querySelectorAll:()=>[0,1,2,3].map(()=>({classList:{toggle(){}}})),addEventListener(){},createElement:()=>({}),head:{appendChild:s=>scripts.push(s)}};
 const ctx={document:doc,location:{origin:'https://example.test',pathname:'/stories/bridge'},localStorage:{getItem:()=>null,setItem:(...a)=>writes.push(a)},setInterval:f=>(tick=f,1),clearInterval:()=>{tick=null;}};
 ctx.window=ctx;
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/stories/player.js'),'utf8'),ctx);
 return {els,ctx,writes,scripts,tick:()=>tick?.()};
}
test('no tracking before consent and no memo stored',()=>{const h=setup();h.els.reflection.value='private memo';h.els.done.onclick();assert.equal(h.scripts.length,0);assert.equal(h.writes.length,0);assert.match(h.els.status.textContent,/きっかけ/);});
test('automatic playback ends at final scene and can restart',()=>{const h=setup();h.els.play.onclick();for(let i=0;i<4;i++)h.tick();assert.match(h.els.chapter.textContent,/04/);assert.equal(h.els.next.disabled,true);assert.match(h.els.play.textContent,/はじめ/);h.els.play.onclick();assert.match(h.els.chapter.textContent,/01/);});
test('pause and resume preserves current scene',()=>{const h=setup();h.els.play.onclick();h.tick();h.els.play.onclick();h.tick();assert.match(h.els.chapter.textContent,/02/);h.els.play.onclick();h.tick();assert.match(h.els.chapter.textContent,/03/);});
test('consented events exclude memo and stop after opt-out',()=>{const h=setup();h.els.metrics.onclick();h.els.reflection.value='private memo';h.els.done.onclick();for(let i=0;i<3;i++)h.els.next.onclick();const payload=JSON.stringify(h.ctx.dataLayer);assert.match(payload,/story_final_scene/);assert.match(payload,/story_action/);assert.ok(!payload.includes('private memo'));const n=h.ctx.dataLayer.length;h.els.metrics.onclick();h.els.play.onclick();assert.equal(h.ctx.dataLayer.length,n);assert.equal(h.ctx['ga-disable-G-XMQ7M4M5J1'],true);});
