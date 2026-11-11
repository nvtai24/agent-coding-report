import { OpenCode } from '@opencode/client';
import { appendFileSync } from 'node:fs';
const [directory,promptFile,prefix]=process.argv.slice(2);
const client=OpenCode.make({baseUrl:'http://127.0.0.1:14427',headers:{Authorization:'Basic '+btoa('opencode:benchmark-local')}});
const controller=new AbortController();const deadline=setTimeout(()=>controller.abort(),240_000);
let sessionID='';let resolveReady!:()=>void;const ready=new Promise<void>(resolve=>resolveReady=resolve);
await Bun.write(prefix+'.jsonl','');
const events:any[]=[];
const listening=(async()=>{
 for await(const e of client.event.subscribe({signal:controller.signal})){
  if(e.type==='server.connected')resolveReady();const event=e as any;
  if(event.data?.sessionID!==sessionID)continue;
  events.push(event);appendFileSync(prefix+'.jsonl',JSON.stringify(event)+'\n');
  if(['session.execution.succeeded','session.execution.failed','session.execution.interrupted'].includes(event.type))return event;
 }
})();
try{
 await Promise.race([ready,listening.then(()=>{throw new Error('Event stream ended before readiness');})]);
 const session=await client.session.create({location:{directory},title:'Coding benchmark',model:{providerID:'openai',id:'gpt-6.1-sol',variant:'medium'}},{signal:controller.signal});sessionID=session.id;
 await client.session.prompt({sessionID,text:await Bun.file(promptFile).text()},{signal:controller.signal});
 const end=await listening;
 if(!end)throw new Error('No terminal event before timeout');
 await Bun.write(prefix+'.context.json',JSON.stringify(await client.session.context({sessionID}),null,2));
 console.log(JSON.stringify({sessionID,terminal:end.type}));
 if(end.type!=='session.execution.succeeded')process.exitCode=1;
}finally{clearTimeout(deadline);controller.abort();await listening.catch(()=>undefined);}
