import { OpenCode } from '@opencode/client';
import { Service } from '@opencode/client/service';
import { mkdir, readFile } from 'node:fs/promises';
const home='/tmp/opencode-lab/managed';
const env={OPENCODE_TEST_HOME:home,XDG_CONFIG_HOME:home+'/config',XDG_DATA_HOME:home+'/data',XDG_CACHE_HOME:home+'/cache',XDG_STATE_HOME:home+'/state',OPENCODE_DISABLE_AUTOUPDATE:'true'};
for(const path of Object.values(env).filter(v=>v.startsWith('/')))await mkdir(path,{recursive:true});
const file=home+'/state/opencode/service.json';
const options={file,version:'2.2.7',env,command:['/tmp/opencode-lab/v2/package/bin/opencode','serve','--service','--hostname','127.0.0.1','--port','14333']};
const evidence:any={};
try{
 const first=await Service.ensure(options);
 const a=OpenCode.make({baseUrl:first.url,headers:Service.headers(first)});
 evidence.before=await a.server.info();
 const session=await a.session.create({title:'Shared lab session',location:{directory:'/tmp/opencode-lab/project-v2'}});
 const second=await Service.ensure(options);
 const b=OpenCode.make({baseUrl:second.url,headers:Service.headers(second)});
 evidence.after=await b.server.info();
 evidence.sessionFromA=session.id;
 evidence.sessionFromB=(await b.session.get({sessionID:session.id})).id;
 const web=await fetch(first.url,{headers:Service.headers(first)});
 const tui=Bun.spawn(['python3',new URL('./tui_probe.py',import.meta.url).pathname,first.url,session.id],{env:{...process.env,...env,OPENCODE_PASSWORD:first.auth?.password},stdout:'pipe',stderr:'pipe'});
 evidence.tui=JSON.parse(await new Response(tui.stdout).text());
 await tui.exited;
 evidence.web={status:web.status,contentType:web.headers.get('content-type'),preview:(await web.text()).slice(0,120)};
 const raw=JSON.parse(await readFile(file,'utf8'));const {password,...registration}=raw;evidence.registration=registration;
 evidence.samePID=evidence.before.pid===evidence.after.pid;
 evidence.sameSession=evidence.sessionFromA===evidence.sessionFromB;
}finally{
 await Service.stop({file});
 evidence.stopped=(await Service.discover({file}))===undefined;
 await Bun.write(new URL('../evidence/shared-service.json',import.meta.url),JSON.stringify(evidence,null,2));
}
console.log(JSON.stringify(evidence));
