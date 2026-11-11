import { OpenCode } from '@opencode/client';
import { appendFileSync } from 'node:fs';
const baseUrl='http://127.0.0.1:14227';
const client=OpenCode.make({baseUrl,headers:{Authorization:'Basic '+btoa('opencode:lab-local-only')}});
const directory='/tmp/opencode-lab/project-v2';
const folder=new URL('../evidence/',import.meta.url);
const results:any[]=[];
const cases=[
  ['plugin','Call lab_echo with text "PORT_OK" exactly once. Report its returned value.'],
  ['allow','Use the shell tool to execute exactly: printf LAB_ALLOW . Do not add punctuation to the command. Report the output.'],
  ['ask','Use the shell tool to execute exactly the command string "printf LAB_ASK". If permission is requested wait for approval. Report the output.'],
  ['deny','Attempt exactly the shell command string "printf LAB_DENY" once. If denied, report the denial and stop. Do not work around permission.'],
  ['background-shell','Use shell with background=true to run "sleep 5; printf LAB_BACKGROUND_DONE". After the tool returns running, immediately reply MAIN_FREE. Do not poll or sleep.'],
  ['background-subagent','Use subagent to launch agent general with background=true. Give it this task: run shell command "sleep 5; printf CHILD_DONE", then reply CHILD_DONE. After launching it, immediately reply PARENT_FREE. Do not poll.'],
];
for(const [name,prompt] of cases){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),150_000);
  const trace=new URL(`v2-${name}.jsonl`,folder);
  await Bun.write(trace,'');
  let sessionID='';
  let ready!:()=>void;
  const connected=new Promise<void>(resolve=>ready=resolve);
  const events:any[]=[];
  let terminalCount=0;
  const listening=(async()=>{
    for await(const event of client.event.subscribe({signal:controller.signal})){
      if(event.type==='server.connected')ready();
      const e=event as any;
      if(!sessionID || (e.data?.sessionID!==sessionID && !JSON.stringify(e.data).includes(sessionID)))continue;
      events.push({...e,observedAt:Date.now()});
      appendFileSync(trace,JSON.stringify(events.at(-1))+'\n');
      if(e.type==='permission.asked'){
        if(e.data.resources.every((r:string)=>r==='printf LAB_ASK')){
          await client.permission.reply({sessionID,requestID:e.data.id,decision:'once'});
        }else{
          await client.permission.reply({sessionID,requestID:e.data.id,decision:'reject',message:'Lab only approves the expected printf LAB_ASK command.'});
        }
      }
      if(e.type==='session.execution.succeeded' || e.type==='session.execution.failed'){
        terminalCount++;
        if(!name.startsWith('background') || terminalCount>=2)return e;
        // Keep receiving background completion notices after the parent goes idle.
      }
    }
  })();
  const start=performance.now();
  try{
    await connected;
    const session=await client.session.create({title:`Lab V2 ${name}`,location:{directory},model:{providerID:'opencode',id:'minimax-m3.1-flash-free'}});
    sessionID=session.id;
    await client.session.prompt({sessionID,text:prompt});
    await listening;
    const context=await client.session.context({sessionID});
    results.push({name,sessionID,prompt,elapsedMs:Math.round(performance.now()-start),context,events:events.length});
  }catch(error){
    results.push({name,sessionID,prompt,elapsedMs:Math.round(performance.now()-start),error:String(error),events:events.length});
  }finally{
    clearTimeout(timer);controller.abort();await listening.catch(()=>undefined);
  }
  await Bun.write(new URL('runtime-v2-results.json',folder),JSON.stringify(results,null,2));
  console.log(JSON.stringify({name,sessionID,events:events.length,elapsedMs:results.at(-1).elapsedMs,error:results.at(-1).error}));
}
