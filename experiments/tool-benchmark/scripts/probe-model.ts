for(const path of ['responses','chat/completions']){
 const body=path==='responses'?{model:'minimax-m3.1-flash-free',input:[{role:'user',content:'Reply READY'}],stream:false}:{model:'minimax-m3.1-flash-free',messages:[{role:'user',content:'Reply READY'}],stream:false};
 try{
  const r=await fetch('https://opencode.ai/inference/openai/v1/'+path,{method:'POST',headers:{Authorization:'Bearer public','Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(30000)});
  console.log(path,r.status,(await r.text()).slice(0,1500));
 }catch(e){console.log(path,String(e));}
}
