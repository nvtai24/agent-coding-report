import { appendFileSync } from 'node:fs';
const folder=new URL('../evidence/',import.meta.url);
const headers={Authorization:'Basic '+btoa('opencode:lab-local-only'),'Content-Type':'application/json','x-opencode-directory':'/tmp/opencode-lab/project-v1'};
async function request(path:string,body?:unknown,signal?:AbortSignal){
 const response=await fetch('http://127.0.0.1:14195'+path,{method:body===undefined?'GET':'POST',headers,body:body===undefined?undefined:JSON.stringify(body),signal:signal??AbortSignal.timeout(120_000)});
 const text=await response.text();if(!response.ok)throw new Error(`${response.status}: ${text}`);return JSON.parse(text);
}
const results:any[]=[];
for(const [name,prompt] of [
 ['plugin','Call lab_echo with text PORT_OK once. Report its returned value.'],
 ['allow','Use bash to execute exactly the command string "printf LAB_ALLOW". Report the output.'],
 ['ask','Use bash to execute exactly the command string "printf LAB_ASK". Wait if approval is requested and report its output.'],
 ['deny','Attempt exactly the bash command string "printf LAB_DENY" once. If denied, report the denial and stop. Do not work around permission.'],
 ['background-subagent','Call task with subagent_type=general, background=true. Give it this task: run bash command "sleep 5; printf CHILD_DONE", then reply CHILD_DONE. After task returns running immediately reply PARENT_FREE. Do not poll.'],
]){
 if(process.env.LAB_ONLY && name!==process.env.LAB_ONLY)continue;
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),150_000);
 const trace=new URL(`v1-${name}.jsonl`,folder);await Bun.write(trace,'');
 let sessionID='';const events:any[]=[];
 const listening=(async()=>{
  const response=await fetch('http://127.0.0.1:14195/event',{headers,signal:controller.signal});
  if(!response.ok)throw new Error(`SSE ${response.status}`);
  let pending='';const decoder=new TextDecoder();
  for await(const chunk of response.body!){
   pending+=decoder.decode(chunk,{stream:true});let split;
   while((split=pending.indexOf('\n\n'))>=0){
    const frame=pending.slice(0,split);pending=pending.slice(split+2);
    for(const line of frame.split('\n')){
     if(!line.startsWith('data:'))continue;
     const event=JSON.parse(line.slice(5));
     if(!sessionID || !JSON.stringify(event).includes(sessionID))continue;
     events.push({...event,observedAt:Date.now()});appendFileSync(trace,JSON.stringify(events.at(-1))+'\n');
     if(event.type==='permission.asked'){
      const p=event.properties;
      const reply=p.patterns?.every((r:string)=>r==='printf LAB_ASK')?'once':'reject';
      await request(`/permission/${p.id}/reply`,{reply});
     }
    }
   }
  }
 })().catch(error=>{if(!controller.signal.aborted)throw error;});
 const start=performance.now();
 try{
  const session=await request('/session',{title:`Lab V1 ${name}`});sessionID=session.id;
  const result=await request(`/session/${sessionID}/message`,{model:{providerID:'opencode',modelID:'minimax-m3.1-flash-free'},parts:[{type:'text',text:prompt}]},controller.signal);
  if(name.startsWith('background'))await new Promise(resolve=>setTimeout(resolve,15000));
  const messages=await request(`/session/${sessionID}/message`);
  const children=await request(`/session/${sessionID}/children`);
  results.push({name,sessionID,prompt,result,messages,children,elapsedMs:Math.round(performance.now()-start),events:events.length});
 }catch(error){results.push({name,sessionID,prompt,error:String(error),elapsedMs:Math.round(performance.now()-start),events:events.length});}
 finally{clearTimeout(timer);controller.abort();await listening;}
 await Bun.write(new URL(process.env.LAB_ONLY?'runtime-v1-background-enabled.json':'runtime-v1-results.json',folder),JSON.stringify(results,null,2));
 console.log(JSON.stringify({name,sessionID,events:events.length,error:results.at(-1).error}));
}
