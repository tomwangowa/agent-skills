import { expect, test } from 'claude-code/testing';

test('observer timestamps a tool and preserves its result', async ($, on) => {
  let observedCalls = 0;
  on('clock.now', () => { observedCalls += 1; return { value: 1000 }; });
  on('ui.invalidate',()=>({value:undefined}));
 on('tool.call', () => ({ result: 'fixture-output' }));
  const result = await $.tool.call({ tool: 'Bash', command: 'echo fixture' });
  expect(observedCalls).toBe(2);
  expect(result).toEqual({ result: 'fixture-output' });
});
