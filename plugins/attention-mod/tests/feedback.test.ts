import {test,expect} from 'claude-code/testing';
import {parseFeedback,buildIssueUrl,ISSUE_URL_LIMIT} from '../hooks/feedback.js';

test('blank feedback produces no link',()=>{
  expect(buildIssueUrl('')).toBeNull();
  expect(buildIssueUrl('  \n\t ')).toBeNull();
  expect(buildIssueUrl('bug:   ')).toBeNull();
});

test('prefix classifies the report and is removed from the text',()=>{
  expect(parseFeedback('bug: 面板不會更新')).toEqual({kind:'bug',text:'面板不會更新'});
  expect(parseFeedback('Idea：想要深色模式')).toEqual({kind:'idea',text:'想要深色模式'});
  expect(parseFeedback('問題:閃爍')).toEqual({kind:'bug',text:'閃爍'});
  expect(parseFeedback('建議: 加快捷鍵')).toEqual({kind:'idea',text:'加快捷鍵'});
  expect(parseFeedback('隨便說說')).toEqual({kind:'other',text:'隨便說說'});
  // A colon later in the sentence is not a category.
  expect(parseFeedback('我覺得 bug: 很多')).toEqual({kind:'other',text:'我覺得 bug: 很多'});
});

test('link targets this repository and carries only the typed text',()=>{
  const {url,kind,truncated}=buildIssueUrl('bug: 外部輸入不更新\n第二行細節');
  const parsed=new URL(url);
  expect(parsed.origin+parsed.pathname).toBe('https://github.com/tomwangowa/agent-skills/issues/new');
  expect(kind).toBe('bug');
  expect(truncated).toBe(false);
  expect(parsed.searchParams.get('title')).toBe('[attention-mod] 問題：外部輸入不更新');
  const body=parsed.searchParams.get('body');
  expect(body).toContain('外部輸入不更新\n第二行細節');
  // Nothing from the session may ride along: no ids, paths or tool text.
  expect([...parsed.searchParams.keys()].sort()).toEqual(['body','title']);
});

test('long titles are cut by code point without splitting a surrogate pair',()=>{
  const {url}=buildIssueUrl('idea: '+'😀'.repeat(200));
  const title=new URL(url).searchParams.get('title');
  expect(Array.from(title).length).toBeLessThanOrEqual(90);
  expect(title).not.toMatch(/[\uD800-\uDBFF](?![\uDC00-\uDFFF])/);
});

test('oversized feedback is truncated, flagged, and still fits the link limit',()=>{
  const result=buildIssueUrl('bug: '+'很長的回饋😀'.repeat(2000));
  expect(result.url.length).toBeLessThanOrEqual(ISSUE_URL_LIMIT);
  expect(result.truncated).toBe(true);
  const body=new URL(result.url).searchParams.get('body');
  expect(body).toContain('[truncated]');
  expect(body).not.toMatch(/[\uD800-\uDBFF](?![\uDC00-\uDFFF])/);
});
