"""Dependency-free terminal checkbox selection for package and skill names."""
from __future__ import annotations

from contextlib import contextmanager
import os
import sys
import textwrap


class SelectionCancelled(Exception):
    pass


def package_lines(specs, selected, *, focus=None, width=80):
    """Format names only, qualifying packages when multiple hosts are shown."""
    multiple_hosts = len({spec.host for spec in specs}) > 1
    lines, spans = [], []
    for index, spec in enumerate(specs):
        start = len(lines)
        name = f'{spec.host} / {spec.name}' if multiple_hosts else spec.name
        if spec.name == 'superpowers':
            name += ' (strongly recommended)'
        marker = '>' if index == focus else ' '
        label = f'{marker} [{"x" if index in selected else " "}] {name}'
        lines.extend(textwrap.wrap(label, max(12, width), subsequent_indent='      ',
                                   break_long_words=True, break_on_hyphens=False))
        names = ', '.join(skill.name for skill in spec.skills)
        if names:
            lines.extend(textwrap.wrap(names, max(12, width - 5), initial_indent='    ',
                                       subsequent_indent='    ', break_long_words=True,
                                       break_on_hyphens=False))
        if spec.name == 'work-journal':
            lines.extend(textwrap.wrap('Records: ~/.agent-skills/activities (default); notes optional',
                                       max(12, width - 5), initial_indent='    ',
                                       subsequent_indent='    ', break_long_words=True,
                                       break_on_hyphens=False))
        spans.append((start, len(lines)))
    return lines, spans


@contextmanager
def _keys(stream, output):
    if not stream.isatty() or not output.isatty():
        raise OSError('Package selection requires an interactive terminal.')
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        import msvcrt
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetConsoleMode.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        handle = msvcrt.get_osfhandle(output.fileno())
        saved = wintypes.DWORD()
        if not kernel.GetConsoleMode(handle, ctypes.byref(saved)):
            raise OSError('Use an interactive Windows Terminal console for package selection.')
        if not kernel.SetConsoleMode(handle, saved.value | 0x0004):
            raise OSError('Unable to enable terminal rendering; no package selection confirmed.')
        def read():
            key = msvcrt.getwch()
            if key in ('\x00', '\xe0'):
                return {'H': 'up', 'P': 'down'}.get(msvcrt.getwch(), 'ignore')
            return key
        try:
            yield read
        finally:
            kernel.SetConsoleMode(handle, saved.value)
    else:
        import select
        import termios
        import tty
        fd = stream.fileno()
        saved = termios.tcgetattr(fd)
        def read():
            key = os.read(fd, 1)
            if key == b'\x1b':
                sequence = key
                while len(sequence) < 16 and select.select([fd], [], [], .06)[0]:
                    sequence += os.read(fd, 1)
                    if sequence[-1:] in (b'A', b'B'):
                        return 'up' if sequence[-1:] == b'A' else 'down'
                    if len(sequence) > 2 and sequence[-1:] not in b'0123456789;':
                        break
                return 'ignore'
            return key.decode('ascii', errors='ignore') if key else '\x04'
        try:
            tty.setraw(fd)
            yield read
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def select_packages(specs, defaults, output, *, input_stream=None):
    """Return confirmed checks; cancellation always restores terminal state."""
    stream = input_stream if input_stream is not None else sys.stdin
    selected, focus, offset = set(defaults), 0, 0
    if not specs:
        return frozenset()
    with _keys(stream, output) as read:
        try:
            output.write('\x1b[?1049h\x1b[?25l')
            while True:
                width, height = os.get_terminal_size(output.fileno())
                if width < 24 or height < 8:
                    raise OSError('Resize the terminal to at least 24 columns and 8 rows.')
                width -= 1
                lines, spans = package_lines(specs, selected, focus=focus, width=width)
                footer = textwrap.wrap('Up/Down move | Space toggle | Enter confirm | q cancel', width)
                available = height - len(footer) - 3
                start, end = spans[focus]
                if start < offset:
                    offset = start
                elif end > offset + available:
                    offset = min(start, end - available)
                frame = [f'Packages ({len(selected)}/{len(specs)} selected)', '']
                frame.extend(lines[offset:offset + available])
                frame.extend(['', *footer])
                output.write('\x1b[H\x1b[J' + '\r\n'.join(frame))
                output.flush()
                key = read()
                if key == 'up':
                    focus = max(0, focus - 1)
                elif key == 'down':
                    focus = min(len(specs) - 1, focus + 1)
                elif key == ' ':
                    selected.symmetric_difference_update((focus,))
                elif key in ('\r', '\n'):
                    return frozenset(selected)
                elif key in ('q', 'Q', '\x03', '\x04'):
                    raise SelectionCancelled()
        finally:
            output.write('\x1b[?25h\x1b[?1049l')
            output.flush()
