import {test, expect} from 'claude-code/testing';
import {freshnessFacts} from '../hooks/freshness.js';

/** A fake git: `answers` maps the joined args to a result; unknown calls fail with 128. Records every call. */
function fakeGit(answers: Record<string, any>) {
  const calls: string[][] = [];
  const git = async (args: string[]) => {
    calls.push(args);
    const answer = answers[args.join(' ')];
    if (answer instanceof Error) throw answer;
    return answer ?? {exitCode: 128, stdout: ''};
  };
  return {git, calls};
}
const meta = {repo: '/r', branch: 'feat/x', head: 'abc1234'};
const ok = (stdout = '') => ({exitCode: 0, stdout});
const base = {
  'rev-parse --verify --quiet refs/heads/feat/x': ok(),
  'rev-list --count abc1234..refs/heads/feat/x': ok('12\n'),
  'symbolic-ref --short refs/remotes/origin/HEAD': ok('origin/main\n'),
  'merge-base --is-ancestor abc1234 origin/main': {exitCode: 1, stdout: ''},
};

test('commits since the handoff are reported with their count', async () => {
  const {git} = fakeGit(base);
  expect(await freshnessFacts({meta, git})).toEqual([{kind: 'ahead', branch: 'feat/x', count: 12}]);
});
test('a branch that no longer exists is reported and nothing else is asked about it', async () => {
  const {git, calls} = fakeGit({...base, 'rev-parse --verify --quiet refs/heads/feat/x': {exitCode: 1, stdout: ''}});
  const facts = await freshnessFacts({meta, git});
  expect(facts.some((f: any) => f.kind === 'branchGone' && f.branch === 'feat/x')).toBe(true);
  expect(calls.some((c) => c[0] === 'rev-list')).toBe(false);
});
test('a head already contained in the default branch is reported', async () => {
  const {git} = fakeGit({...base, 'merge-base --is-ancestor abc1234 origin/main': ok()});
  const facts = await freshnessFacts({meta, git});
  expect(facts.some((f: any) => f.kind === 'merged' && f.base === 'origin/main')).toBe(true);
});
test('zero new commits produces no ahead fact', async () => {
  const {git} = fakeGit({...base, 'rev-list --count abc1234..refs/heads/feat/x': ok('0\n')});
  expect(await freshnessFacts({meta, git})).toEqual([]);
});
test('a failing or throwing git command only drops its own line', async () => {
  const failing = fakeGit({...base, 'rev-list --count abc1234..refs/heads/feat/x': {exitCode: 128, stdout: ''}});
  expect(await freshnessFacts({meta, git: failing.git})).toEqual([]);
  const throwing = fakeGit({...base, 'symbolic-ref --short refs/remotes/origin/HEAD': new Error('boom')});
  expect(await freshnessFacts({meta, git: throwing.git})).toEqual([{kind: 'ahead', branch: 'feat/x', count: 12}]);
});
test('no repository means unverifiable and git is never called', async () => {
  const {git, calls} = fakeGit(base);
  expect(await freshnessFacts({meta: {branch: 'feat/x', head: 'abc1234'}, git})).toEqual([{kind: 'unverifiable'}]);
  expect(calls.length).toBe(0);
});
test('a branch or head from the file that could be an option or a path trick never reaches git', async () => {
  const {git, calls} = fakeGit(base);
  const bad = [
    {repo: '/r', branch: '--upload-pack=touch /tmp/pwned', head: '-h'},
    {repo: '/r', branch: 'a b', head: 'abc1234; rm -rf /'},
    {repo: '/r', branch: '../../etc', head: 'xyz'},
    {repo: '/r', branch: 'feat/x\nrev-parse', head: 'abc1234\n'},
    {repo: '/r', branch: '-x', head: ''},
  ];
  for (const m of bad) expect(await freshnessFacts({meta: m, git})).toEqual([{kind: 'unverifiable'}]);
  expect(calls.length).toBe(0);
  expect(JSON.stringify(calls)).not.toContain('upload-pack');
});
test('a valid head with an invalid branch still checks only the head', async () => {
  const {git, calls} = fakeGit({...base, 'merge-base --is-ancestor abc1234 origin/main': ok()});
  const facts = await freshnessFacts({meta: {repo: '/r', branch: '--bad', head: 'abc1234'}, git});
  expect(facts.some((f: any) => f.kind === 'merged')).toBe(true);
  expect(JSON.stringify(calls)).not.toContain('--bad');
});
