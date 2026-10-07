import {test, expect} from 'claude-code/testing';
import {parseHandoff} from '../hooks/handoff-file.js';
import {handoffText} from './fixtures.js';

test('a complete Chinese file parses', () => {
  const r: any = parseHandoff(handoffText());
  expect(r.ok).toBe(true);
  expect(r.meta.status).toBe('in-progress');
  expect(r.meta.created).toBe(Date.parse('2026-10-06T18:30:00+08:00'));
  expect(r.meta.branch).toBe('feat/login-timeout');
  expect(r.meta.head).toBe('781ac6b');
  expect(r.meta.root).toBe('/work/app');
  expect(r.meta.repo).toBe('/work/app');
  expect(r.fields.task).toBe('修正登入逾時');
  expect(r.fields.next).toBe('重跑 auth 測試');
});
test('English section headings work too (D11)', () => {
  const r: any = parseHandoff(handoffText({omit: ['task'], body: '## Task\nfix login\n\n## Done\n- a\n\n## Remaining\n- b\n\n## Next\n1. rerun tests\n'}));
  expect(r.ok).toBe(true);
  expect(r.fields.task).toBe('fix login');
  expect(r.fields.next).toBe('rerun tests');
});
test('the verified and premises headings in either language do not disturb the next line', () => {
  const r: any = parseHandoff(handoffText({body: '## 前提（人工確認）\n- x\n\n## 已驗證／未驗證（AI 自述）\n- y\n\n## 下一步\n- [ ] 做 z\n'}));
  expect(r.fields.next).toBe('做 z');
});
test('files without a valid status or created are rejected', () => {
  expect((parseHandoff(handoffText({omit: ['status']})) as any).ok).toBe(false);
  expect((parseHandoff(handoffText({omit: ['created']})) as any).ok).toBe(false);
  expect((parseHandoff(handoffText({status: 'resumed'})) as any).ok).toBe(false);
  expect((parseHandoff(handoffText({status: 'weird'})) as any).ok).toBe(false);
  expect((parseHandoff(handoffText({created: 'yesterday'})) as any).ok).toBe(false);
  expect((parseHandoff('no frontmatter here') as any).ok).toBe(false);
  expect((parseHandoff('') as any).ok).toBe(false);
});
test("Tom's existing handoff format: worktree is an alias of root and nested assertions are ignored", () => {
  const text = [
    '---', 'branch: tom/post-profile-invite-later-copy   # authoritative, not sanitized', 'worktree: /path/to/repo',
    'created: 2026-06-29T18:30:00+08:00', 'task: L10N upstream 條件式同步', 'status: in-progress', 'assertions:',
    '  - kind: expect_head', '    repo: /path/to/related-repo', '    value: 4bbb4af', '  - kind: worktree_clean', '    repo: /path/to/your-repo', '---', '', '## 任務', '同步', '',
  ].join('\n');
  const r: any = parseHandoff(text);
  expect(r.ok).toBe(true);
  expect(r.meta.root).toBe('/path/to/repo');
  expect(r.meta.repo).toBe(undefined);
  expect(r.meta.branch).toBe('tom/post-profile-invite-later-copy');
});
test('unknown frontmatter keys are ignored and a trailing comment is stripped', () => {
  const r: any = parseHandoff(handoffText({extra: 'mystery: 42\nstatus_note: x'}));
  expect(r.ok).toBe(true);
  expect(r.meta.mystery).toBe(undefined);
});
test('source: auto is carried through', () => {
  expect((parseHandoff(handoffText({extra: 'source: auto'})) as any).meta.source).toBe('auto');
  expect((parseHandoff(handoffText()) as any).meta.source).toBe(undefined);
});
test('displayed fields are cleaned and capped', () => {
  const dirty: any = parseHandoff(handoffText({omit: ['task'], extra: 'task: \x1b[31mred\x1b[0m task'}));
  expect(dirty.fields.task).toBe('red task');
  const long: any = parseHandoff(handoffText({omit: ['task'], extra: `task: ${'長'.repeat(200)}`, body: `## 下一步\n- ${'n'.repeat(300)}\n`}));
  expect([...long.fields.task].length <= 80).toBe(true);
  expect([...long.fields.next].length <= 120).toBe(true);
});
test('CRLF, a missing section list, a frontmatter-only file and a huge body do not throw', () => {
  expect((parseHandoff(handoffText().replace(/\n/g, '\r\n')) as any).ok).toBe(true);
  const fm: any = parseHandoff(handoffText({body: ''}));
  expect(fm.ok).toBe(true);
  expect(fm.fields.next).toBe('');
  expect((parseHandoff(handoffText({body: `## 下一步\n- ok\n\n${'x'.repeat(300000)}`})) as any).ok).toBe(true);
});
test('values from the file are returned as plain strings and never evaluated', () => {
  const r: any = parseHandoff(handoffText({omit: ['branch'], extra: 'branch: --upload-pack=touch /tmp/pwned'}));
  expect(r.meta.branch).toBe('--upload-pack=touch /tmp/pwned');
});
