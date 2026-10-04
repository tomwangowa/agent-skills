import {test, expect} from 'claude-code/testing';
import {parseSummary, summarySystemPrompt, unwrapSummaryJson} from '../hooks/summary.js';
const snap={sourceIds:['goal','approach','result','input'],sourceRoles:{goal:'user',approach:'assistant',result:'tool-error',input:'tool-input'}};
const valid={goal:{text:'修正登入',sources:['goal']},context:null,evidence:{text:'測試失敗',sources:['result']}};
test('supported source-backed fields and unsupported null are accepted', () => {
  expect(parseSummary(JSON.stringify(valid),snap)).toEqual(valid);
  expect(summarySystemPrompt()).toContain('untrusted');
});
test('invalid JSON, unknown references, duplicate references and extra fields reject the whole response', () => {
  for(const raw of ['```json\n{}\n```','{}',JSON.stringify({...valid,action:'done'}),JSON.stringify({...valid,goal:{text:'x',sources:['missing']}}),JSON.stringify({...valid,goal:{text:'x',sources:['goal','goal']}}),JSON.stringify({...valid,context:{text:'x',sources:[]}}),JSON.stringify({...valid,evidence:{text:'x',sources:['result'],completed:true}})]) expect(parseSummary(raw,snap)).toBe(null);
});
test('Unicode field boundary is 160 points, and empty text is rejected', () => {
  expect(parseSummary(JSON.stringify({...valid,context:{text:'😀'.repeat(160),sources:['approach']}}),snap)?.context?.text).toBe('😀'.repeat(160));
  expect(parseSummary(JSON.stringify({...valid,context:{text:'😀'.repeat(161),sources:['approach']}}),snap)).toBe(null);
  expect(parseSummary(JSON.stringify({...valid,context:{text:' ',sources:['goal']}}),snap)).toBe(null);
});

test('approach must cite assistant statements and evidence must cite actual tool results',()=>{
  expect(parseSummary(JSON.stringify({...valid,context:{text:'Claude 懷疑過期',sources:['goal']}}),snap)).toBe(null);
  expect(parseSummary(JSON.stringify({...valid,evidence:{text:'測試失敗',sources:['input']}}),snap)).toBe(null);
  expect(parseSummary(JSON.stringify({...valid,evidence:{text:'測試失敗',sources:['approach']}}),snap)).toBe(null);
  expect(parseSummary(JSON.stringify({...valid,context:{text:'Claude 懷疑過期',sources:['approach']}}),snap)?.context?.sources).toEqual(['approach']);
});

test('optional whole JSON block adapter preserves validation and rejects surrounding prose',()=>{
  const json=JSON.stringify(valid);
  const fenced='```json\n'+json+'\n```';
  expect(parseSummary(fenced,snap)).toBe(null);
  expect(parseSummary(unwrapSummaryJson(fenced),snap)).toEqual(valid);
  expect(parseSummary(unwrapSummaryJson('Explanation\n'+fenced),snap)).toBe(null);
  expect(parseSummary(unwrapSummaryJson(fenced+'\nExplanation'),snap)).toBe(null);
  expect(parseSummary(unwrapSummaryJson(fenced+'\n'+fenced),snap)).toBe(null);
  expect(parseSummary(unwrapSummaryJson('```json\n'+JSON.stringify({...valid,goal:{text:'x',sources:['missing']}})+'\n```'),snap)).toBe(null);
});
