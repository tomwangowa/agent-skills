"""Per-package phase bars, with immediate native prompts and separated results."""
from __future__ import annotations

import shutil
import time


class PackageProgress:
    """Present checked phases rather than invented download percentages."""

    def __init__(self, output):
        self.output = output
        try:
            self.dynamic = output.isatty() and output.fileno() >= 0
        except (AttributeError, OSError, ValueError):
            self.dynamic = False
        self.active = None
        self.stage = 'checking'
        self.line_width = 0
        self.message_open = False
        self.last_pulse = 0
        self.tick = 0
        self.escape = ''

    def _clear(self):
        if self.line_width:
            self.output.write('\r' + ' ' * self.line_width + '\r')
            self.line_width = 0

    def _close_message(self):
        if self.message_open:
            self.output.write('\n')
            self.message_open = False

    def _draw(self, finished=None):
        if not self.active or self.message_open:
            return
        label = self.active.target.split('@', 1)[0]
        if self.active.kind not in ('install', 'update', 'remove'):
            label = ('Tool / ' if self.active.kind == 'dependency' else 'Source / ') + label
        completed = {'checking': 0, 'running': 4, 'verifying': 8}[self.stage]
        if finished and finished.status in ('installed', 'updated', 'removed'):
            completed = 12
        bar = '#' * completed + '.' * (12 - completed)
        text = f'{label} [{bar}] '
        text += f'{finished.status}: {finished.detail}' if finished else self.stage
        if self.dynamic:
            self._clear()
            if not finished:
                text += ' ' + '|/-\\'[self.tick % 4]
            width = max(20, shutil.get_terminal_size((80, 24)).columns - 1)
            # Completion details get their own line so they remain readable in
            # narrow terminals rather than disappearing at a truncation boundary.
            if finished:
                text = f'{label} [{bar}] {finished.status}:'
            text = text[:width]
            self.output.write(text)
            self.line_width = len(text)
            if finished:
                self.output.write('\n  ' + finished.detail + '\n')
                self.line_width = 0
        else:
            self.output.write(text + '\n')
        if finished:
            if finished.receipt:
                self.output.write('  Installed root: ' + finished.receipt.root + '\n')
            self.output.write('\n')
        self.output.flush()

    def event(self, stage, action, outcome=None):
        """Receive execution boundaries without changing approval or results."""
        self._close_message()
        self.active = action
        if stage == 'finished':
            self._draw(outcome)
            self.active = None
        else:
            self.stage = stage
            self._draw()

    def retained(self, outcome):
        """Give a selected package kept without commands its own completed row."""
        if outcome.detail == 'Not selected.':
            return
        name = outcome.action_id.rsplit('/', 1)[-1]
        bar = '############' if outcome.status == 'preserved' else '............'
        self.output.write(f'{name} [{bar}] {outcome.status}:\n  {outcome.detail}\n\n')
        self.output.flush()

    def pulse(self):
        """Keep a waiting native action visibly alive without advancing its bar."""
        now = time.monotonic()
        if self.dynamic and not self.message_open and now - self.last_pulse >= 0.2:
            self.last_pulse = now
            self.tick += 1
            self._draw()

    def native_message(self, chunk):
        """Forward stderr prompts immediately, even when no newline is present."""
        # Native color/cursor sequences can arrive split across reads. Keep
        # their parser state while retaining printable prompts and line breaks.
        visible = []
        for char in chunk:
            if self.escape:
                self.escape += char
                if self.escape == '\x1b[' or self.escape == '\x1b]':
                    continue
                if self.escape.startswith('\x1b['):
                    if '@' <= char <= '~' or len(self.escape) > 256:
                        self.escape = ''
                elif self.escape.startswith('\x1b]'):
                    if char == '\x07' or self.escape.endswith('\x1b\\') or len(self.escape) > 4096:
                        self.escape = ''
                else:
                    self.escape = ''
            elif char == '\x1b':
                self.escape = char
            elif char in '\n\t' or char.isprintable():
                visible.append(char)
            elif char == '\r':
                visible.append('\n')
        text = ''.join(visible)
        if text:
            self._clear()
            self.output.write(text)
            self.output.flush()
            self.message_open = not text.endswith('\n')
