import { OpenCode } from '@opencode/client';
const client=OpenCode.make({baseUrl:'http://127.0.0.1:14227',headers:{Authorization:'Basic '+btoa('opencode:lab-local-only')}});
const results:any[]=[];
const broad={action:'shell',resource:'*',effect:'ask'} as const;
const specific={action:'shell',resource:'printf LAB_ORDER',effect:'allow'} as const;
for(const [name,permissions] of [['specific-last',[broad,specific]],['broad-last',[specific,broad]]] as const){
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),120_000);let sessionID='';
 let resolve!:()=>void;const ready=new Promise<void>(r=>resolve=r);const events:any[]=[];
 const listening=(async()=>{
  for await(const event of client.event.subscribe({signal:controller.signal})){
   if(event.type==='server.connected')resolve();
   const e=event as any;if(!sessionID||e.data?.sessionID!==sessionID)continue;events.push(e);
   if(e.type==='permission.asked')await client.permission.reply({sessionID,requestID:e.data.id,decision:e.data.resources.every((r:string)=>r==='printf LAB_ORDER')?'once':'reject'});
   if(['session.execution.succeeded','session.execution.failed'].includes(e.type))return;
  }
 })();
 try{
  await ready;
  sessionID=(await client.session.create({title:`Rule order ${name}`,location:{directory:'/tmp/opencode-lab/project-v2'},model:{providerID:'opencode',id:'minimax-m3.1-flash-free'},permissions:[...permissions]})).id;
  await client.session.prompt({sessionID,text:'Use shell to run exactly the command string "printf LAB_ORDER" once. Report the output.'});await listening;
  results.push({name,sessionID,permissions,events});
 }finally{clearTimeout(timer);controller.abort();await listening.catch(()=>undefined);}
}
await Bun.write(new URL('../evidence/rule-order.json',import.meta.url),JSON.stringify(results,null,2));
console.log(JSON.stringify(results.map(r=>({name:r.name,asked:r.events.filter((e:any)=>e.type==='permission.asked').length}))));
