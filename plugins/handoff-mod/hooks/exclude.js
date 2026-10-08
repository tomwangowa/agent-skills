/**
 * Keep a path pattern (such as ".claude/handoffs/") out of `git status` by adding it to .git/info/exclude.
 * `git(args)` resolves to {exitCode, stdout}; `fs` has exists/read/write. Idempotent, never throws.
 * Returns {ok, changed} or {ok:false, skipped:true} outside a git repository.
 */
export async function ensureExcluded({git, fs, pattern}) {
  try {
    const ignored = await git(['check-ignore', '-q', '--', `${pattern}_probe`]);
    if (ignored.exitCode === 0) return {ok: true, changed: false};
    if (ignored.exitCode !== 1) return {ok: false, skipped: true};
    const located = await git(['rev-parse', '--git-path', 'info/exclude']);
    const path = located.exitCode === 0 ? String(located.stdout).trim() : '';
    if (!path) return {ok: false};
    const current = (await fs.exists(path)) ? await fs.read(path) : '';
    if (current.split('\n').some((line) => line.trim() === pattern)) return {ok: true, changed: false};
    const separator = current === '' || current.endsWith('\n') ? '' : '\n';
    await fs.write(path, `${current}${separator}${pattern}\n`);
    return {ok: true, changed: true};
  } catch {
    return {ok: false};
  }
}
