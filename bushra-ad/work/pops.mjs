import { chromium } from 'playwright';
const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/teachers.html'); await p.evaluate(()=>window.ready);
console.log(JSON.stringify(await p.evaluate(()=>window.POP))); await b.close();
