/** Build handoff file text for tests; `extra` adds frontmatter lines, `body` replaces the default sections. */
export function handoffText(o: {status?: string; created?: string; extra?: string; body?: string; omit?: string[]} = {}): string {
  const lines: Record<string, string> = {
    schema: '1',
    root: '/work/app',
    repo: '/work/app',
    branch: 'feat/login-timeout',
    head: '781ac6b',
    created: o.created ?? '2026-10-06T18:30:00+08:00',
    task: '修正登入逾時',
    status: o.status ?? 'in-progress',
  };
  for (const key of o.omit ?? []) delete lines[key];
  const front = Object.entries(lines).map(([k, v]) => `${k}: ${v}`).join('\n');
  const body = o.body ?? '## 任務\n修正登入逾時\n\n## 已完成\n- 找到 refreshToken\n\n## 未完成\n- 補測試\n\n## 下一步\n- 重跑 auth 測試\n- 其他\n';
  return `---\n${front}${o.extra ? `\n${o.extra}` : ''}\n---\n\n${body}`;
}
