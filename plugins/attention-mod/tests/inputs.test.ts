import {test, expect} from 'claude-code/testing';
import {entryFromAppend, originLabel, excerptOf, NOISE} from '../hooks/inputs.js';

const row = (door, message = {}, extra = {}) => ({door, uuid:'u1', origin:{kind:'engine'}, message:{type:'attachment', content:[{type:'text', text:'hello'}], ...message}, ...extra});

test('typed prompts, responses, tool results, commands and subagent rows are not external inputs', () => {
  for (const door of ['prompt','response','tool-result','command']) expect(entryFromAppend(row(door), undefined)).toBe(null);
  expect(entryFromAppend(row('hook-context', {}, {agentId:'agent-one'}), undefined)).toBe(null);
});
test('known noise is dropped but an unseen attachment kind stays visible', () => {
  expect(NOISE.has('total_tokens_reminder')).toBe(true);
  expect(entryFromAppend(row('attachment', {name:'total_tokens_reminder'}), undefined)).toBe(null);
  expect(entryFromAppend(row('attachment', {name:'some_new_kind'}), undefined)).toEqual({id:'u1', door:'attachment', kind:'附件 some_new_kind', origin:'引擎', excerpt:'hello'});
});
test('every listed door produces an entry', () => {
  for (const door of ['delivery','hook-context','notice','note','compaction','tool-message']) expect(entryFromAppend(row(door, {type:'user'}), undefined)?.id).toBe('u1');
});
test('hook context is labelled with the settings hook event', () => {
  const entry = entryFromAppend(row('hook-context', {name:'hook_additional_context'}, {origin:{kind:'hook', event:'SessionStart'}}), undefined);
  expect(entry.kind).toBe('hook 注入');
  expect(entry.origin).toBe('hook（SessionStart）');
});
test('excerpt reads the stored row, first real line only, bounded by code points', () => {
  const stored = {uuid:'u1', message:{type:'attachment', name:'file', content:[{type:'text', text:'😀'.repeat(200) + '\nsecond line'}]}};
  const entry = entryFromAppend(row('attachment', {name:'file', content:[{type:'text', text:'original'}]}), stored);
  expect(Array.from(entry.excerpt).length).toBe(120);
  expect(entry.excerpt.endsWith('…')).toBe(true);
  expect(entry.excerpt).not.toContain('second line');
  expect(excerptOf([{type:'image', source:{}}])).toBe('[圖片]');
  expect(excerptOf([])).toBe('[無文字內容]');
});
test('unknown origin kinds are shown raw and missing origins are not guessed', () => {
  expect(originLabel({kind:'observer-activity'})).toBe('observer-activity');
  expect(originLabel({kind:'task-notification'})).toBe('背景工作');
  expect(originLabel(undefined)).toBe('來源不明');
});
test('a refused append never shows a phantom row', () => {
  expect(entryFromAppend(row('note'), {deny:'nope'})).toBe(null);
});
test('excerpt splits on CRLF as well as LF', () => {
  expect(excerptOf([{type:'text', text:'line1\r\nline2'}])).toBe('line1');
});
test('malformed rows do not throw and unreadable ones are dropped', () => {
  const noMessage = entryFromAppend({door:'notice', uuid:'u1', origin:{kind:'engine'}}, undefined);
  expect(noMessage).toBe(null);

  const stringContent = entryFromAppend(row('notice', {content:'just a string'}), undefined);
  expect(stringContent).toBe(null);

  const nullResultMessage = entryFromAppend(row('notice'), {uuid:'u1', message:null});
  expect(nullResultMessage?.id).toBe('u1');

  const nullOrigin = entryFromAppend({...row('notice'), origin:null}, undefined);
  expect(nullOrigin?.id).toBe('u1');
});
test('only empty rows are hidden', () => {
  const hookCtx = (content) => row('hook-context', {name:'hook_success', content}, {origin:{kind:'hook', event:'PostToolUse'}});
  expect(entryFromAppend(hookCtx([]), undefined)).toBe(null);
  expect(entryFromAppend(hookCtx([{type:'text', text:'   '}]), undefined)).toBe(null);

  const withImage = entryFromAppend(hookCtx([{type:'image', source:{}}]), undefined);
  expect(withImage.excerpt).toBe('[圖片]');

  const unseenKind = entryFromAppend(row('attachment', {name:'brand_new', content:[{type:'text', text:'hi'}]}), undefined);
  expect(unseenKind?.id).toBe('u1');

  const toolResult = entryFromAppend(row('tool-message', {content:[{type:'tool_result', tool_use_id:'t', content:'ran ok'}]}), undefined);
  expect(toolResult?.id).toBe('u1');

  const searchResult = entryFromAppend(row('delivery', {content:[{type:'search_result', source:'x'}]}), undefined);
  expect(searchResult?.id).toBe('u1');

  const mixedBlankAndUnknown = entryFromAppend(row('delivery', {content:[{type:'text', text:'  '}, {type:'search_result'}]}), undefined);
  expect(mixedBlankAndUnknown?.id).toBe('u1');
});
test('session-start noise is dropped but mid-session MCP instructions stay visible', () => {
  expect(entryFromAppend(row('attachment', {name:'instructions'}), undefined)).toBe(null);
  expect(entryFromAppend(row('attachment', {name:'session_context'}), undefined)).toBe(null);

  const mcp = entryFromAppend(row('attachment', {name:'mcp_instructions_delta', content:[{type:'text', text:'new mcp text'}]}), undefined);
  expect(mcp?.id).toBe('u1');
});
test('excerpt skips wrapper-tag-only lines but still prefers real text', () => {
  expect(excerptOf([{type:'text', text:'<system-reminder>\nUse the email only…\n</system-reminder>'}])).toBe('Use the email only…');
  expect(excerptOf([{type:'text', text:'<a>\n</a>'}])).toBe('<a>');
  expect(excerptOf([{type:'text', text:'<x>'}, {type:'text', text:'real'}])).toBe('real');
});
test('origin and kind labels cover tool, plugin, system-only doors, and clipping', () => {
  expect(originLabel({kind:'tool', tool:'Bash'})).toBe('工具 Bash');
  expect(originLabel({kind:'plugin', event:'x'})).toBe('plugin（x）');
  expect(entryFromAppend(row('notice', {type:'system'}), undefined).kind).toBe('notice');

  const longKind = entryFromAppend(row('attachment', {name:'x'.repeat(60)}), undefined);
  expect(Array.from(longKind.kind).length).toBe(40);

  const longOrigin = entryFromAppend(row('attachment', {}, {origin:{kind:'tool', tool:'x'.repeat(60)}}), undefined);
  expect(Array.from(longOrigin.origin).length).toBe(40);
});
