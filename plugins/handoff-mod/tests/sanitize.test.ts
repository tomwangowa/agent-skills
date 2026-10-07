import {test, expect} from 'claude-code/testing';
import {stripControl, truncateCodePoints, redactSecrets, cleanForNote} from '../hooks/sanitize.js';

// Secret-shaped test values are assembled at run time so this file never contains a literal that a scanner would flag.
const j = (...parts: string[]) => parts.join('');
const CASES: Array<[string, string, string]> = [
  ['bearer header', 'curl -H "Authorization: Bearer abcdef0123456789abcdef"', 'abcdef0123456789abcdef'],
  ['basic header', 'Authorization: Basic dXNlcjpwYXNzd29yZA==', 'dXNlcjpwYXNzd29yZA'],
  ['password assignment', 'password = hunter2hunter2', 'hunter2hunter2'],
  ['api key with colon and quotes', 'api_key: "k9f3-secret-value"', 'k9f3-secret-value'],
  ['token assignment', 'GITHUB_TOKEN=abc123def456', 'abc123def456'],
  ['aws access key', `aws key ${j('AKIA', 'IOSFODNN7EXAMPLE')}`, j('AKIA', 'IOSFODNN7EXAMPLE')],
  ['github token', `token ${j('ghp', '_', 'x'.repeat(36))} end`, 'x'.repeat(36)],
  ['github fine-grained token', j('github', '_pat_', 'y'.repeat(30)), 'y'.repeat(30)],
  ['slack token', j('xox', 'b-', '1234567890', '-', 'abcdefghij'), '1234567890-abcdefghij'],
  ['sk- key', j('sk', '-', 'z'.repeat(32)), 'z'.repeat(32)],
  ['private key block', j('-----BEGIN ', 'PRIVATE KEY-----\nMIIBabc\nmore\n-----END ', 'PRIVATE KEY-----'), 'MIIBabc'],
  ['unterminated private key block', j('-----BEGIN ', 'PRIVATE KEY-----\nMIIBabc\ncut off here'), 'MIIBabc'],
  ['jwt', 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijk', 'abcdefghijk'],
  ['credentials in a url', 'git clone https://deploy:s3cr3tpass@example.com/repo.git', 's3cr3tpass'],
];

for (const [name, text, secret] of CASES) {
  test(`redacts ${name}`, () => {
    const out = redactSecrets(text);
    expect(out).not.toContain(secret);
    expect(out).toContain('[redacted]');
  });
}
test('the host of a credentialed url survives', () => {
  expect(redactSecrets('https://deploy:s3cr3tpass@example.com/repo.git')).toContain('example.com/repo.git');
});
test('ordinary words about tokens and passwords are left alone', () => {
  const text = 'The token count is 5 and the password policy changed; see the secret santa list.';
  expect(redactSecrets(text)).toBe(text);
});
test('stripControl removes ANSI, OSC and control characters but keeps text, newlines and emoji', () => {
  expect(stripControl('\x1b[31mred\x1b[0m')).toBe('red');
  expect(stripControl('\x1b]0;title\x07x')).toBe('x');
  expect(stripControl('a\x00b\x7fc\x85d')).toBe('abcd');
  expect(stripControl('line1\r\nline2\t中文😀')).toBe('line1\nline2\t中文😀');
});
test('truncateCodePoints counts code points and never splits an emoji', () => {
  expect(truncateCodePoints('😀😀😀😀', 3)).toBe('😀😀…');
  expect([...truncateCodePoints('😀😀😀😀', 3)].length).toBe(3);
  expect(truncateCodePoints('abc', 3)).toBe('abc');
  expect(truncateCodePoints('abcd', 3)).toBe('ab…');
});
test('cleanForNote redacts before truncating, so a secret on the cut line leaves no fragment', () => {
  const token = j('ghp', '_', 'x'.repeat(36));
  const out = cleanForNote(`${'a'.repeat(1990)} ${token}`, 2000);
  expect(out).not.toContain('xxxx');
  expect(out).not.toContain('ghp_');
  expect([...out].length <= 2000).toBe(true);
});
test('cleanForNote strips control characters first', () => {
  expect(cleanForNote('\x1b[31mpassword=hunter2hunter2\x1b[0m', 100)).not.toContain('hunter2');
});
