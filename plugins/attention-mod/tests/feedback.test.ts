import {test,expect} from 'claude-code/testing';
import {parseFeedback,parseRecipient,buildTeamsLink,LINK_LIMIT} from '../hooks/feedback.js';

const TO='colleague@example.com';

test('blank feedback or a missing recipient produces no link',()=>{
  expect(buildTeamsLink('',TO)).toBeNull();
  expect(buildTeamsLink('  \n\t ',TO)).toBeNull();
  expect(buildTeamsLink('bug:   ',TO)).toBeNull();
  expect(buildTeamsLink('bug: x',undefined)).toBeNull();
  expect(buildTeamsLink('bug: x','')).toBeNull();
  expect(buildTeamsLink('bug: x','not-an-email')).toBeNull();
});

test('recipient must look like one email address and nothing that could add parameters',()=>{
  expect(parseRecipient(' a.b@corp.example ')).toBe('a.b@corp.example');
  for(const bad of ['a@b','a@b.c,d@e.f','a@b.c&message=x','a b@c.d','a@b.c?x=1','@b.c',undefined,null,42]) expect(parseRecipient(bad)).toBeNull();
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

test('link opens a Teams chat with the recipient and carries only the typed text',()=>{
  const result=buildTeamsLink('bug: 外部輸入不更新\n第二行細節',TO);
  const parsed=new URL(result.url);
  expect(parsed.origin+parsed.pathname).toBe('https://teams.microsoft.com/l/chat/0/0');
  expect(parsed.searchParams.get('users')).toBe(TO);
  expect(parsed.searchParams.get('message')).toBe('[attention-mod 問題] 外部輸入不更新\n第二行細節');
  expect(result.message).toBe('[attention-mod 問題] 外部輸入不更新\n第二行細節');
  expect(result.kind).toBe('bug');
  expect(result.truncated).toBe(false);
  // Nothing from the session may ride along: no ids, paths or tool text.
  expect([...parsed.searchParams.keys()].sort()).toEqual(['message','users']);
});

test('oversized feedback is truncated in the link, flagged, and the copy text stays whole',()=>{
  const typed='很長的回饋😀'.repeat(2000);
  const result=buildTeamsLink('bug: '+typed,TO);
  expect(result.url.length).toBeLessThanOrEqual(LINK_LIMIT);
  expect(result.truncated).toBe(true);
  const message=new URL(result.url).searchParams.get('message');
  expect(message).toContain('[truncated]');
  expect(message).not.toMatch(/[\uD800-\uDBFF](?![\uDC00-\uDFFF])/);
  expect(result.message).toBe('[attention-mod 問題] '+typed);
});

test('a lone surrogate is replaced instead of making encoding throw',()=>{
  // encodeURIComponent throws URIError on an unpaired surrogate, e.g. from a pasted half emoji.
  for(const raw of ['bug: abc\uD83D def','\uDE00','idea: tail\uD83D']){
    const result=buildTeamsLink(raw,TO);
    expect(result).not.toBeNull();
    expect(new URL(result.url).searchParams.get('message')).not.toMatch(/[\uD800-\uDFFF]/);
    expect(result.message).not.toMatch(/[\uD800-\uDFFF]/);
  }
  expect(parseFeedback('bug: a\uD83Db')).toEqual({kind:'bug',text:'a\uFFFDb'});
  // A real pair survives untouched.
  expect(parseFeedback('bug: 😀')).toEqual({kind:'bug',text:'😀'});
});

test('the README capacity holds for a single line: about 200 CJK or 1,800 ASCII characters fit',()=>{
  // TO is 21 characters; a longer recipient leaves less room, as the README says.
  expect(buildTeamsLink('idea: '+'中'.repeat(200),TO).truncated).toBe(false);
  expect(buildTeamsLink('idea: '+'中'.repeat(220),TO).truncated).toBe(true);
  expect(buildTeamsLink('idea: '+'a'.repeat(1800),TO).truncated).toBe(false);
  expect(buildTeamsLink('idea: '+'a'.repeat(1950),TO).truncated).toBe(true);
});
