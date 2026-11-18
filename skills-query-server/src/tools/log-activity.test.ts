import { describe, it, expect } from 'vitest';
import { activitySessionId } from './log-activity.js';

const NOW = new Date('2026-11-18T03:22:05.123Z');

describe('activitySessionId', () => {
  it('prefers an explicit CLAUDE_SESSION_ID', () => {
    const env = { CLAUDE_SESSION_ID: 'chosen', CLAUDE_CODE_SESSION_ID: 'claude', CODEX_THREAD_ID: 'codex' };
    expect(activitySessionId(env, NOW)).toBe('chosen');
  });

  it('uses the Claude Code session that started the server', () => {
    expect(activitySessionId({ CLAUDE_CODE_SESSION_ID: 'claude-uuid', CODEX_THREAD_ID: 'codex' }, NOW))
      .toBe('claude-uuid');
  });

  it('uses a Codex thread id when one is passed', () => {
    expect(activitySessionId({ CODEX_THREAD_ID: 'codex-thread' }, NOW)).toBe('codex-thread');
  });

  it('ignores empty values', () => {
    expect(activitySessionId({ CLAUDE_SESSION_ID: '', CLAUDE_CODE_SESSION_ID: 'claude-uuid' }, NOW))
      .toBe('claude-uuid');
  });

  it('falls back to the mcp_ id of this record without a host session', () => {
    expect(activitySessionId({}, NOW)).toBe('mcp_20261118T032205');
  });
});
