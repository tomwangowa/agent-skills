import {mock} from 'claude-code/testing';
import {handoffText} from './fixtures.js';

export const NOW = Date.parse('2026-10-07T12:00:00Z');
const GIT_DEFAULTS: Record<string, [number, string]> = {
  'rev-parse --show-toplevel': [0, '/work/app\n'],
  'worktree list --porcelain': [0, 'worktree /work/app\nHEAD 781ac6b\nbranch refs/heads/feat/login-timeout\n\n'],
  'check-ignore -q -- .claude/handoffs/_probe': [1, ''],
  'rev-parse --git-path info/exclude': [0, '.git/info/exclude\n'],
};

/** Stub every host call the wiring makes: in-memory files and store, a scripted git, and recorders for what the mod shows. */
export function world(on: any, o: {turns?: number; env?: Record<string, string>; git?: Record<string, [number, string]>; files?: Record<string, string>; store?: Record<string, any>; repo?: any; surfaces?: string[]} = {}) {
  const clock = mock.clock(on, {now: NOW});
  mock.env(on, o.env ?? {});
  const files = new Map<string, {text: string; mtimeMs: number}>(Object.entries(o.files ?? {}).map(([p, text]) => [p, {text, mtimeMs: NOW - 3600_000}]));
  const store = new Map<string, any>(Object.entries(o.store ?? {}));
  const rec = {statuses: [] as any[], toasts: [] as string[], logs: [] as string[], fills: [] as string[], commands: [] as any[], git: [] as string[], writes: [] as Array<[string, string]>, fsCalls: 0};
  const lastStatus = () => rec.statuses[rec.statuses.length - 1];
  const dirOf = (path: string) => path.slice(0, path.lastIndexOf('/'));

  on('session.start', () => ({cwd: '/work/app'}));
  on('classic.SessionStart', () => ({}));
  on('prompt.submit', ($: any, e: any) => ({text: e.text}));
  on('skill.prompt', ($: any, e: any) => ({text: e.text}));
  on('turn.complete', () => ({text: ''}));
  on('command.register', ($: any, e: any) => { rec.commands.push(e); return {value: undefined}; });
  on('session.id', () => ({value: 'sess-A'}));
  on('session.root', () => ({value: '/work/app'}));
  on('session.repo', () => ({value: o.repo === undefined ? {root: '/work/app', remote: null, internal: false, name: null} : o.repo}));
  on('session.turns', () => ({value: o.turns ?? 0}));
  on('session.surfaces', () => ({value: o.surfaces ?? ['terminal']}));
  on('store.get', ($: any, e: any) => ({value: store.get(e.key)}));
  on('store.set', ($: any, e: any) => { store.set(e.key, e.value); return {value: undefined}; });
  on('ui.status', ($: any, e: any) => { rec.statuses.push(e.text); return {value: undefined}; });
  on('ui.toast', ($: any, e: any) => { rec.toasts.push(e.text); return {value: undefined}; });
  on('ui.log', ($: any, e: any) => { rec.logs.push(e.text); return {value: undefined}; });
  on('prompt.fill', ($: any, e: any) => { rec.fills.push(e.text); return {isFilled: true, text: '', cursor: 0}; });
  on('process.run', ($: any, e: any) => {
    const key = e.argv.slice(1).join(' ');
    rec.git.push(key);
    const [exitCode, stdout] = (o.git ?? {})[key] ?? GIT_DEFAULTS[key] ?? [128, ''];
    return {value: {exitCode, stdout, stderr: ''}};
  });
  on('fs.exists', ($: any, e: any) => { rec.fsCalls++; return {value: files.has(e.path) || [...files.keys()].some((p) => p.startsWith(`${e.path}/`))}; });
  on('fs.list', ($: any, e: any) => { rec.fsCalls++; return {value: [...files.keys()].filter((p) => dirOf(p) === e.path).map((p) => ({name: p.split('/').pop(), kind: 'file', size: files.get(p)!.text.length, isLink: false}))}; });
  on('fs.read', ($: any, e: any) => { rec.fsCalls++; const f = files.get(e.path); return f ? {value: f.text} : {deny: 'no such file'}; });
  on('fs.stat', ($: any, e: any) => { rec.fsCalls++; const f = files.get(e.path); return f ? {value: {kind: 'file', size: f.text.length, mtimeMs: f.mtimeMs, isLink: false}} : {deny: 'no such file'}; });
  on('fs.write', ($: any, e: any) => { files.set(e.path, {text: e.text, mtimeMs: clock.now()}); rec.writes.push([e.path, e.text]); return {value: undefined}; });
  on('ui.render', () => ({type: 'Text', props: {}, children: ['engine band']}));

  const flush = async () => { for (let i = 0; i < 25; i++) await clock.advance(0); };
  return {clock, files, store, rec, lastStatus, flush};
}

export const HANDOFF_DIR = '/work/app/.claude/handoffs';
export const fileA = `${HANDOFF_DIR}/feat-login-timeout--20261006-183000.md`;
export const fileB = `${HANDOFF_DIR}/feat-other--20261005-090000.md`;
export const twoHandoffs = {
  [fileA]: handoffText(),
  [fileB]: handoffText({created: '2026-10-05T09:00:00+08:00', extra: 'x: y', body: '## 任務\n其他\n\n## 下一步\n- 做別的\n'}).replace('task: 修正登入逾時', 'task: 其他工作').replace('branch: feat/login-timeout', 'branch: feat/other'),
};

export const bandTarget = {plugin: 'handoff-mod', surface: 'terminal', component: 'AbovePrompt', requestId: 'band', viewport: {columns: 100, rows: 30}, props: {hasSurvey: false, isWorking: false, maxRows: 14, bodyColumns: 80, scroll: {offset: 0, bodyRows: 10}, view: {}}} as const;
export const startSession = async ($: any, source = 'startup') => {
  await $.session.start({surface: 'terminal', isInteractive: true, cwd: '/work/app'});
  await $.classic.SessionStart({source, session_id: 'sess-A'});
};
export const doneTurn = ($: any, o: any = {}) => $.turn.complete({turnId: 't', answer: 'ok', durationMs: 1, isAborted: false, usage: null, ...o});
