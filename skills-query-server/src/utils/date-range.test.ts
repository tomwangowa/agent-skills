import { describe, it, expect, vi, afterEach } from 'vitest';
import { parseDateRange } from './date-range.js';

describe('parseDateRange', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('parses "today"', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-18T15:00:00Z'));
    const { since, until } = parseDateRange('today');
    // parseDateRange uses local time; check via local date parts
    expect(since.getHours()).toBe(0);
    expect(since.getMinutes()).toBe(0);
    expect(until.getTime()).toBeGreaterThan(since.getTime());
    // since and until should be on the same local date
    expect(since.getDate()).toBe(until.getDate());
  });

  it('parses "this-week"', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-18T15:00:00Z')); // Wednesday
    const { since } = parseDateRange('this-week');
    // Monday of this week
    expect(since.getDay()).toBe(1);
  });

  it('parses "this-month"', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-18T15:00:00Z'));
    const { since } = parseDateRange('this-month');
    expect(since.getDate()).toBe(1);
    expect(since.getMonth()).toBe(1); // Feb = 1
  });

  it('parses "all" as very wide range', () => {
    const { since } = parseDateRange('all');
    expect(since.getFullYear()).toBeLessThan(2000);
  });

  it('throws on unknown range', () => {
    expect(() => parseDateRange('invalid')).toThrow();
  });
});
