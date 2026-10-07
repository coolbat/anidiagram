#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(import.meta.dirname,'..');
const out=path.resolve(process.argv[2] || path.join(root,'outputs/optimization-p1-p3-2026-10-07/layout-browser'));
fs.mkdirSync(out,{recursive:true});
const cases=[['c3-agent-loop','examples/agent-loop-internals.plan.json'],['c5-rag','examples/enterprise-rag-production-illustrated.plan.json']];
for (const [name,plan] of cases) execFileSync('python3',['scripts/run_anidiagram.py','--plan',plan,'--outdir',out,'--basename',name,'--formats','svg,html,quality','--runtime-dependency','none'],{cwd:root,stdio:'pipe'});
execFileSync('python3',['scripts/run_anidiagram.py','--preset','swimlane','--style','dark-luxury','--outdir',out,'--basename','c4-swimlane-dark','--formats','svg,html,quality','--runtime-dependency','none'],{cwd:root,stdio:'pipe'});
const browser=await chromium.launch({headless:true});
const results=[];
try {
  for (const name of [...cases.map(([name])=>name),'c4-swimlane-dark']) {
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    const source=fs.readFileSync(path.join(out,name+'.svg'),'utf8');
    const html=path.join(out,name+'.inspection.html');
    fs.writeFileSync(html,`<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#e5e7eb}svg{display:block;width:100%;height:auto}*{animation:none!important}</style>${source}`);
    await page.goto(pathToFileURL(html).href);
    const result=await page.evaluate(()=>{
      const svg=document.querySelector('svg'); svg.pauseAnimations(); svg.setCurrentTime(0);
      const b=el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};
      const overlap=(a,c)=>a.x<c.x+c.w-1&&a.x+a.w>c.x+1&&a.y<c.y+c.h-1&&a.y+a.h>c.y+1;
      const nodes=[...svg.querySelectorAll('g.node')].map(node=>{
        const title=node.querySelector(':scope > title')?.textContent;
        const captions=node.querySelectorAll('.node-caption');
        const text=node.querySelector('.node-text-block');
        const icon=node.querySelector('.decision-icon-zone')||node.querySelector('.semantic-icon-wrap');
        return {id:node.id,title,captionLines:captions.length,textAnchor:text.getAttribute('text-anchor'),iconOverlapsText:icon?overlap(b(text),b(icon)):false,
          badge:node.querySelectorAll('.step-label').length};
      });
      const labels=[...svg.querySelectorAll('g.edge[data-label-placement]')].map(edge=>({
        text:edge.querySelector('.edge-label')?.textContent.trim(),status:edge.dataset.labelPlacement,
        overlapsNode:[...svg.querySelectorAll('g.node .node-surface')].some(node=>overlap(b(edge.querySelector('.edge-label')),b(node)))
      }));
      return {nodes,labels,nodeBadges:nodes.reduce((n,v)=>n+v.badge,0),edgeBadges:svg.querySelectorAll('g.edge .step-label').length};
    });
    assert(result.nodes.every(n=>n.title && n.captionLines<=2 && n.textAnchor==='start'),`${name}: missing disclosure / card hierarchy`);
    assert(result.nodes.every(n=>!n.iconOverlapsText),`${name}: icon/text overlap ${JSON.stringify(result.nodes.filter(n=>n.iconOverlapsText))}`);
    assert(!(result.nodeBadges && result.edgeBadges),`${name}: duplicated step systems`);
    assert(result.labels.every(l=>l.status==='placed'&&!l.overlapsNode),`${name}: label placement ${JSON.stringify(result.labels)}`);
    await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});
    results.push({name,...result}); await page.close();
  }
} finally {await browser.close();}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify({ok:true,cases:results.length,nodes:results.reduce((n,r)=>n+r.nodes.length,0),labels:results.reduce((n,r)=>n+r.labels.length,0),out}));
