import { OpenCode } from '@opencode/client';
import { appendFileSync } from 'node:fs';
const output = new URL('../evidence/api-v2-events.jsonl', import.meta.url);
await Bun.write(output, '');
const client = OpenCode.make({
  baseUrl: process.env.LAB_SERVER ?? 'http://127.0.0.1:14227',
  headers: { Authorization: 'Basic ' + btoa('opencode:lab-local-only') },
});
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(new Error('Lab timeout after 120 seconds')), 120_000);
let sessionID: string | undefined;
let connected!: () => void;
const ready = new Promise<void>(resolve => { connected = resolve; });
const events: unknown[] = [];
const listening = (async () => {
  for await (const event of client.event.subscribe({ signal: controller.signal })) {
    if (event.type === 'server.connected') connected();
    if (!sessionID || (event as any).data?.sessionID !== sessionID) continue;
    events.push(event);
    appendFileSync(output, JSON.stringify(event) + '\n');
    if (['session.execution.succeeded', 'session.execution.failed', 'session.execution.interrupted'].includes(event.type)) return event;
  }
})();
try {
  await Promise.race([ready,listening.then(()=>{throw new Error("Event stream closed before ready");})]);
  const session = await client.session.create({
    title: 'Migration lab API smoke',
    location: { directory: '/tmp/opencode-lab/project-v2' },
    model: { providerID: 'opencode', id: process.env.LAB_MODEL ?? 'minimax-m3.1-flash-free' },
  });
  sessionID = session.id;
  const start = performance.now();
  const admitted = await client.session.prompt({ sessionID, text: 'Reply exactly MIGRATION_API_OK. Do not use tools.' });
  const terminal = await listening;
  if (!terminal) throw new Error("Event stream ended without an execution result");
  const context = await client.session.context({ sessionID });
  const summary = { version: '2.2.7', sessionID, admitted, terminal, elapsedMs: Math.round(performance.now()-start), context, eventCount: events.length };
  await Bun.write(new URL('../evidence/api-v2-summary.json', import.meta.url), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify({sessionID,eventCount:events.length,terminal,elapsedMs:summary.elapsedMs}));
} finally {
  clearTimeout(timer);
  controller.abort();
  await listening.catch(() => undefined);
}
