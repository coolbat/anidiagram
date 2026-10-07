#!/usr/bin/env node
// Reproducible actual-browser recording; the clip has no audio/voiceover.
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright';
const root=path.resolve(import.meta.dirname,'..'),out=path.join(root,'gallery/narration');
const frames=path.join(root,'outputs/optimization-p1-p3-2026-10-07/gallery-frames');
fs.mkdirSync(out,{recursive:true});fs.mkdirSync(frames,{recursive:true});
const plan='examples/contracts/production-request-path.plan.json';
execFileSync('python3',['scripts/run_anidiagram.py','--plan',plan,'--style','minimal-light','--runtime-mode','timeline','--runtime-dependency','inline','--runtime-source','node_modules/gsap/dist/gsap.min.js','--formats','html,quality','--outdir',out,'--basename','production-request'],{cwd:root,stdio:'inherit'});
const browser=await chromium.launch({headless:true});const errors=[];
try {
 const page=await browser.newPage({viewport:{width:1280,height:800},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(out,'production-request.html')).href);
 await page.evaluate(()=>{window.AniDiagramEntrance?.clear();window.AniDiagramRuntime.pause();});
 for(let i=0;i<168;i++){
  await page.evaluate(t=>{const tl=window.__ANIDIAGRAM_CHOREOGRAPHER__.timeline;tl.pause(Math.min(t,tl.duration()-.001),false);},i/24);
  await page.screenshot({path:path.join(frames,`${String(i).padStart(4,'0')}.png`)});
 }
 if(errors.length)throw new Error(errors.join(';'));
}finally{await browser.close();}
execFileSync('ffmpeg',['-y','-v','error','-framerate','24','-i',path.join(frames,'%04d.png'),'-frames:v','168','-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',path.join(out,'explanation.mp4')]);
fs.copyFileSync(path.join(frames,'0012.png'),path.join(out,'poster.png'));
const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',path.join(out,'explanation.mp4')],{encoding:'utf8'}));
const stream=probe.streams.find(s=>s.codec_type==='video');
if(Number(stream.nb_frames)!==168||Number(probe.format.duration)!==7||stream.width!==1280||stream.height!==800)throw new Error('Unexpected recording dimensions/timing');
fs.writeFileSync(path.join(out,'recording.json'),JSON.stringify({version:'gallery-recording-v1',source_plan:plan,source_plan_sha256:createHash('sha256').update(fs.readFileSync(path.join(root,plan))).digest('hex'),mode:'timeline',runtime_dependency:'inline',method:'Chromium screenshots of actual GSAP timeline at deterministic times',duration_seconds:7,fps:24,frames:168,width:1280,height:800,audio:false,source_scope:'generic architecture example; no production runtime claim',command:'node scripts/build_gallery_narration.mjs',sha256:createHash('sha256').update(fs.readFileSync(path.join(out,'explanation.mp4'))).digest('hex')},null,2)+'\n');
console.log('Gallery recording verified: 7 seconds, 168 frames, 1280x800.');
