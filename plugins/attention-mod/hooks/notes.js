/**
 * Quick Notes as pure transitions: no `$` here, so the save rules are tested without the host. While the panel runs,
 * the text in memory is the truth; the store is only where it lasts across restarts.
 */
export const NOTE_LIMIT = 32768;
/** Saves wait this long after the last edit, so a burst of typing is one write. */
export const IDLE_MS = 1000;
/** A failed write waits this long before the next try, so a broken store is not hammered every second. */
export const RETRY_MS = 5000;

export function createNotes() {
  return {status: 'idle', key: null, text: '', dirty: false, lastEditAt: 0, saving: false, saveError: null, retryAt: 0};
}

/** The store key: one note per git common dir, so every worktree of a repository shares it. */
export function keyFor(read) {
  if (!read) return null;
  return read.commonDir ? `notes:${read.commonDir}` : `notes-cwd:${read.cwd}`;
}

export function beginRead(notes, key) {
  return {...createNotes(), status: 'reading', key};
}

/** A result for a key other than the one being read is stale, so it changes nothing. */
export function loaded(notes, key, value) {
  if (key !== notes.key) return notes;
  // An unset key is an empty note. Anything else that is not text means the store cannot be trusted, so nothing is written over it.
  if (value === undefined) return {...notes, status: 'ready', text: '', dirty: false};
  if (typeof value === 'string') return {...notes, status: 'ready', text: value, dirty: false};
  return {...notes, status: 'read-failed'};
}

export function loadFailed(notes, key) {
  return key === notes.key ? {...notes, status: 'read-failed'} : notes;
}

export function edit(notes, text, now) {
  // The flag is set here, not only at save time, so the panel can say why the note is not kept.
  const tooLong = [...text].length > NOTE_LIMIT;
  return {...notes, text, dirty: true, lastEditAt: now, saveError: tooLong ? 'too-long' : null};
}

/** What the next save should do. `force` (Enter, a page switch) skips the idle and retry waits. */
export function nextSave(notes, now, force) {
  if (notes.status !== 'ready' || !notes.dirty || notes.saving) return {action: 'none'};
  if (!force && now - notes.lastEditAt < IDLE_MS) return {action: 'none'};
  if (!force && notes.saveError === 'failed' && now < notes.retryAt) return {action: 'none'};
  if ([...notes.text].length > NOTE_LIMIT) return {action: 'refuse'};
  if (notes.text === '') return {action: 'delete'};
  return {action: 'save', value: notes.text};
}

export function saveStarted(notes) {
  return {...notes, saving: true};
}

export function saveSettled(notes, sentText, ok, now) {
  // An over-limit note keeps its notice: the text is still too long whatever the write did.
  if (!ok) return {...notes, saving: false, saveError: notes.saveError === 'too-long' ? 'too-long' : 'failed', retryAt: now + RETRY_MS};
  // Text typed while the write was in flight is not saved yet, so the note stays dirty for the next save.
  // A too-long flag survives a successful write of an earlier, shorter text.
  return {...notes, saving: false, dirty: notes.text !== sentText, saveError: notes.saveError === 'too-long' ? 'too-long' : null};
}

/** Moves to another key. The old note is flushed first only when it still holds unsaved text. */
export function switchKey(notes, nextKey) {
  const flush = notes.dirty && notes.key !== null ? {key: notes.key, text: notes.text} : null;
  return {flush, notes: {...createNotes(), key: nextKey}};
}
