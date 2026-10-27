/**
 * The one read-only git call the panel makes. The three lines it prints are the git dir, the common dir and the
 * branch, in that order; --no-optional-locks keeps the read from taking index locks. --path-format=absolute makes both
 * directories absolute: from a subdirectory git prints the common dir relative (../.git), and that cannot be compared.
 */
export const GIT_ARGS = Object.freeze(['git', '--no-optional-locks', 'rev-parse', '--path-format=absolute', '--git-dir', '--git-common-dir', '--abbrev-ref', 'HEAD']);

/** Long enough for a healthy repository, short enough that a slow git cannot hold up the timer. */
export const GIT_TIMEOUT_MS = 2000;

/** A read that could not finish: the row stays and says so, rather than disappearing. */
export const FAILED_READ = Object.freeze({state: 'unreadable', branch: null, detached: false});

/**
 * Turns git's output into a read. A linked worktree has its own git dir, which differs from the common dir; the main
 * checkout's two are the same. Exit 128 is git's "not a repository", which hides the row instead of failing it.
 */
export function parseWorktree(stdout, exitCode) {
  if (exitCode === 128) return {state: 'not-git', branch: null, detached: false};
  if (exitCode !== 0) return FAILED_READ;
  // Only the first three lines are read, so a trailing newline or extra output changes nothing.
  const [gitDir, commonDir, branch] = String(stdout).split('\n');
  // A relative directory means git did not apply --path-format=absolute. Reading it as a path would mislabel the
  // checkout, so the row says unreadable instead.
  if (!gitDir?.startsWith('/') || !commonDir?.startsWith('/') || !branch) return FAILED_READ;
  const detached = branch === 'HEAD';
  return {state: gitDir === commonDir ? 'main' : 'linked', branch: detached ? null : branch, detached};
}

/**
 * The 工作樹 row for the current directory, or null to hide it. A read taken in another directory says nothing about
 * this one, so it shows the waiting label instead of the old branch.
 */
export function worktreeView(read, currentCwd) {
  if (!read || !currentCwd) return null;
  if (read.cwd !== currentCwd) return {path: currentCwd, branch: '待下一回合更新'};
  if (read.state === 'unreadable') return {path: currentCwd, branch: '無法讀取'};
  if (read.state !== 'linked') return null;
  return {path: currentCwd, branch: read.detached ? '分離 HEAD' : read.branch};
}
