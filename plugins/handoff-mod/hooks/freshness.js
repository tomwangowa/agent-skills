const HEAD_RE = /^[0-9a-f]{4,40}$/;
const BRANCH_RE = /^[A-Za-z0-9._][A-Za-z0-9._/-]*$/;

/** A branch name that cannot be read as an option or a path trick. Values from a handoff file are untrusted. */
const validBranch = (name) => typeof name === 'string' && BRANCH_RE.test(name) && !name.includes('..') && !name.endsWith('/') && !name.endsWith('.lock');
const validHead = (head) => typeof head === 'string' && HEAD_RE.test(head);

/**
 * Facts about how the repository moved since a handoff was written. `git(args)` is injected and resolves to {exitCode, stdout}.
 * The result is a list of facts, never a verdict; any git command that fails only drops its own line.
 */
export async function freshnessFacts({meta, git}) {
  const branch = validBranch(meta.branch) ? meta.branch : null;
  const head = validHead(meta.head) ? meta.head : null;
  if (!meta.repo || (!branch && !head)) return [{kind: 'unverifiable'}];

  const run = async (args) => {
    try {
      const result = await git(args);
      return result && typeof result.exitCode === 'number' ? result : null;
    } catch {
      return null;
    }
  };
  const facts = [];
  let branchExists = false;
  if (branch) {
    const found = await run(['rev-parse', '--verify', '--quiet', `refs/heads/${branch}`]);
    if (found && found.exitCode !== 0) facts.push({kind: 'branchGone', branch});
    else if (found) branchExists = true;
  }
  if (branch && head && branchExists) {
    const counted = await run(['rev-list', '--count', `${head}..refs/heads/${branch}`]);
    const count = counted && counted.exitCode === 0 ? Number.parseInt(String(counted.stdout).trim(), 10) : NaN;
    if (Number.isFinite(count) && count > 0) facts.push({kind: 'ahead', branch, count});
  }
  if (head) {
    const named = await run(['symbolic-ref', '--short', 'refs/remotes/origin/HEAD']);
    const base = named && named.exitCode === 0 ? String(named.stdout).trim() : '';
    if (validBranch(base)) {
      const contained = await run(['merge-base', '--is-ancestor', head, base]);
      if (contained && contained.exitCode === 0) facts.push({kind: 'merged', base});
    }
  }
  return facts;
}
