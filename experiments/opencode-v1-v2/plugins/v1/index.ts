import { tool } from '@opencode-ai/plugin';

export default async () => ({
  tool: {
    lab_echo: tool({
      description: 'Return the migration lab marker followed by the supplied text.',
      args: { text: tool.schema.string() },
      async execute({ text }) {
        return `MIGRATION_PLUGIN:${text}`;
      },
    }),
  },
});
