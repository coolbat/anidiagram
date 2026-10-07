#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
const root=path.resolve(import.meta.dirname,'..');
const out=path.resolve(process.argv[2]||'outputs/optimization-p1-p3-2026-10-07/viewer'); fs.mkdirSync(out,{recursive:true});
for(const mode of ['ambient','timeline','hybrid'])for(const dep of ['inline','none']) {
 execFileSync('python3',['scripts/run_anidiagram.py','--plan','examples/contracts/production-request-path.plan.json','--style','minimal-light','--formats','html','--outdir',out,'--basename',`${mode}-${dep}`,'--runtime-mode',mode,'--runtime-dependency',dep,'--runtime-source','node_modules/gsap/dist/gsap.min.js'],{cwd:root,stdio:'pipe'});
}
const browser=await chromium.launch({headless:true}); const results=[];
try {
 for(const width of [1440,390])for(const reduced of [false,true])for(const mode of ['ambient','timeline','hybrid'])for(const dep of ['inline','none']) {
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:reduced?'reduce':'no-preference'});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(out,`${mode}-${dep}.html`)).href); await page.waitForTimeout(100);
 assert.equal(await page.evaluate(()=>document.body.scrollWidth<=innerWidth),true,'toolbar page overflow');
 assert.equal(await page.evaluate(()=>getComputedStyle(document.body).backgroundColor),'rgb(255, 255, 255)','shell must match light diagram');
 assert.equal(await page.locator('.toolbar-group').count(),3);
 if(mode==='ambient') {
 await page.evaluate(()=>{ window.AniDiagramEntrance?.clear();document.querySelector('#node-client').dispatchEvent(new Event('pointerenter')); });
 assert(await page.locator('.context-dim').count()>0,'default context hover absent');
 await page.evaluate(()=>document.querySelector('#node-client').dispatchEvent(new Event('pointerleave')));
 assert.equal(await page.locator('.context-dim').count(),0);
 } else {
 if(mode==='hybrid') {
 await page.locator('#timeline-start').click();
 assert.equal(await page.evaluate(()=>document.activeElement.id),'stage','Explain must enable keyboard navigation');
 }
 assert.equal(await page.locator('#narration').isVisible(),true,'explanation missing');
 const initial=await page.evaluate(()=>{window.AniDiagramRuntime.pause();return {step:window.__ANIDIAGRAM_CHOREOGRAPHER__.current,steps:window.__ANIDIAGRAM_CHOREOGRAPHER__.steps.length};});
 assert.equal(initial.step,0);
 assert.equal(await page.locator('.step-dot').count(),initial.steps);
 await page.locator('#stage').focus(); await page.keyboard.press('ArrowRight');
 assert.equal(await page.evaluate(()=>window.__ANIDIAGRAM_CHOREOGRAPHER__.current),1);
 await page.keyboard.press('ArrowLeft');
 assert.equal(await page.evaluate(()=>window.__ANIDIAGRAM_CHOREOGRAPHER__.current),0);
 await page.locator('.step-dot').last().click();
 assert.equal(await page.evaluate(()=>window.__ANIDIAGRAM_CHOREOGRAPHER__.current),initial.steps-1);
 if(dep==='inline'&&!reduced) {
 await page.evaluate(()=>{window.AniDiagramRuntime.selectStep(0);window.AniDiagramRuntime.nextStep();});
 await page.waitForTimeout(80);await page.evaluate(()=>window.AniDiagramRuntime.pause());
 const paused=await page.evaluate(()=>window.__ANIDIAGRAM_CHOREOGRAPHER__.timeline.time());
 await page.waitForTimeout(120);
 assert.equal(await page.evaluate(()=>window.__ANIDIAGRAM_CHOREOGRAPHER__.timeline.time()),paused,'Pause ignored manual-step tween');
 await page.locator('#timeline-start').click();
 assert.equal(await page.evaluate(()=>document.querySelector('#viewport svg').animationsPaused()),false,'Explain did not resume SVG state');
 await page.locator('#toggle').click();
 assert.equal(await page.evaluate(()=>window.__ANIDIAGRAM_CHOREOGRAPHER__.timeline.paused()),true,'Pause after Explain did not pause timeline');
 }
 const dim=await page.evaluate(()=>[...document.querySelectorAll('g.node')].some(e=>getComputedStyle(e).opacity==='0.25'));assert(dim);
 if(dep==='inline'&&!reduced) {
 const camera=await page.evaluate(()=>{const s=window.__ANIDIAGRAM_CHOREOGRAPHER__;s.timeline.pause();s.timeline.time(.5,false);const a=document.querySelector('#viewport').style.transform;s.timeline.time(2.3,false);const b=document.querySelector('#viewport').style.transform;s.timeline.time(.5,false);return {a,b,c:document.querySelector('#viewport').style.transform};});
 assert.notEqual(camera.a,camera.b,'camera did not focus new step'); assert.equal(camera.a,camera.c,'camera seek nondeterministic');
 } else assert.equal(await page.evaluate(()=>(window.__ANIDIAGRAM_TIMELINES__||[]).length),0);
 await page.locator('[data-motion="off"]').click();
 assert.equal(await page.locator('#narration').isVisible(),false,'off left stale explanation');
 assert.equal(await page.locator('.narration-dim').count(),0,'off left stale dimming');
 }
 assert.deepEqual(errors,[]);if(!reduced&&dep==='inline')await page.screenshot({path:path.join(out,`${mode}-${width}.png`)});
 results.push({width,reduced,mode,dependency:dep,ok:true});await page.close();
 }
}finally {await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');}
console.log(JSON.stringify({ok:true,cases:results.length}));
