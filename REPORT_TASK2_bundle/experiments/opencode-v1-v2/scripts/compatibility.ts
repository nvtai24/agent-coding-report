import { OpenCode } from '@opencode/client';
import { readFile, writeFile } from 'node:fs/promises';
const client=OpenCode.make({baseUrl:'http://127.0.0.1:14227',headers:{Authorization:'Basic '+btoa('opencode:lab-local-only')}});
const directory='/tmp/opencode-lab/project-v2';
const configPath=directory+'/opencode.json';
const original=await readFile(configPath,'utf8');
async function probe(label:string){
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),120_000);
 let sessionID='';let ready!:()=>void;const connected=new Promise<void>(resolve=>ready=resolve);const events:any[]=[];
 const listening=(async()=>{for await(const event of client.event.subscribe({signal:controller.signal})){
  if(event.type==='server.connected')ready();const e=event as any;
  if(e.data?.sessionID!==sessionID)continue;events.push(e);
  if(['session.execution.succeeded','session.execution.failed'].includes(e.type))return;
 }})();
 try{
  await connected;
  sessionID=(await client.session.create({title:`Plugin compatibility ${label}`,location:{directory},model:{providerID:'opencode',id:'minimax-m3.1-flash-free'}})).id;
  await client.session.prompt({sessionID,text:'If tool lab_echo is available call it once with text PORT_OK. Otherwise reply TOOL_UNAVAILABLE. Do not use any other tool.'});await listening;
  return {label,sessionID,plugins:await client.plugin.list({location:{directory}}),events,context:await client.session.context({sessionID})};
 }finally{clearTimeout(timer);controller.abort();await listening.catch(()=>undefined);}
}
const results:any[]=[];
try{
 results.push(await probe('ported'));
 const config=JSON.parse(original);config.plugins=[new URL('../plugins/legacy-on-v2',import.meta.url).pathname];
 await writeFile(configPath,JSON.stringify(config,null,2));await client.location.reload();
 results.push(await probe('legacy'));
}finally{
 await writeFile(configPath,original);await client.location.reload();
 await Bun.write(new URL('../evidence/plugin-compatibility.json',import.meta.url),JSON.stringify(results,null,2));
}
console.log(JSON.stringify(results.map(r=>({label:r.label,plugins:r.plugins,toolResults:r.events.filter((e:any)=>e.type==='session.tool.success').map((e:any)=>e.data.content)}))));
