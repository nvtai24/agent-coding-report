import { Plugin } from '@opencode/plugin';
import { Schema } from 'effect';

export default Plugin.define({
  id: 'lab.echo',
  async setup(ctx) {
    await ctx.tool.transform(editor => {
      editor.add({
        name: 'lab_echo',
        description: 'Return the migration lab marker followed by the supplied text.',
        options: { codemode: false },
        input: Schema.Struct({ text: Schema.String }),
        output: Schema.Struct({ text: Schema.String }),
        async execute({ text }) {
          const result = `MIGRATION_PLUGIN:${text}`;
          return { output: { text: result }, content: result };
        },
      });
    });
  },
});
