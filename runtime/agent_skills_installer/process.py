"""Capture native JSON while streaming stderr prompts with inherited stdin."""
from __future__ import annotations

import codecs
import os
import queue
import subprocess
import threading
import time


def run_json_command(argv, on_stderr, on_wait, *, timeout=600):
    """Wait once; never answer a prompt, retry, or terminate unrelated sessions."""
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    chunks = queue.Queue()

    def read_pipe(name, stream):
        try:
            while True:
                raw = os.read(stream.fileno(), 4096)
                if not raw:
                    break
                chunks.put((name, raw))
        except OSError:
            pass
        finally:
            chunks.put((name, None))

    threads = [threading.Thread(target=read_pipe, args=(name, stream), daemon=True)
               for name, stream in (('stdout', process.stdout), ('stderr', process.stderr))]
    for thread in threads:
        thread.start()
    output = {'stdout': [], 'stderr': []}
    decoders = {key: codecs.getincrementaldecoder('utf-8')(errors='replace') for key in output}
    pending = set(output)
    deadline = time.monotonic() + timeout
    try:
        while pending or process.poll() is None:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(argv, timeout)
            try:
                name, raw = chunks.get(timeout=min(0.1, max(0.001, deadline - time.monotonic())))
            except queue.Empty:
                on_wait()
                continue
            text = decoders[name].decode(raw or b'', final=raw is None)
            output[name].append(text)
            if name == 'stderr' and text:
                on_stderr(text)
            if raw is None:
                pending.discard(name)
            on_wait()
        return subprocess.CompletedProcess(argv, process.returncode,
                                           ''.join(output['stdout']), ''.join(output['stderr']))
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        for stream in (process.stdout, process.stderr):
            stream.close()
        for thread in threads:
            thread.join(timeout=0.2)
