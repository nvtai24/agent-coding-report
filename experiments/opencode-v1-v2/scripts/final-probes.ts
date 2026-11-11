await import('./compatibility.ts');
process.env.LAB_ONLY='background-subagent';
await import('./runtime-v1.ts');
