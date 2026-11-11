import { OpenCode } from '@opencode/client';
const client = OpenCode.make({baseUrl:'http://127.0.0.1:14227',headers:{Authorization:'Basic '+btoa('opencode:lab-local-only')}});
const info=await client.server.info();
const models=await client.model.list({location:{directory:'/tmp/opencode-lab/project-v2'}});
await Bun.write(new URL('../evidence/model-catalog-v2.json',import.meta.url),JSON.stringify(models,null,2));
console.log(JSON.stringify({info, models:models.data.map(m=>({id:m.id,providerID:m.providerID})).filter(m=>m.providerID==='opencode')},null,2));
