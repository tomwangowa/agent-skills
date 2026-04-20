# Language-Specific Review Checklists

Reference for Step 3.4 of `code-review-claude/SKILL.md`. Each checklist encodes **Claude-native-unique findings** from the 2026-04 6-language benchmark (HTTP retry clients in Java, Python, JS/Node, TypeScript, PHP, Shell). Every bullet comes from a real finding that the external reviewer missed — use these as prompts for "did I cover X?" during review.

Not exhaustive. Skip items that clearly don't apply. If a project's context (framework, runtime version) changes applicability, say so and move on.

---

## Python

Apply to `.py` files.

- **Body-type dispatch silently drops `bytes`** — `requests`-style wrappers that check `isinstance(body, dict)` / `isinstance(body, str)` but no `bytes` branch. A `bytes` body (protobuf, binary upload) falls through to `json=None, data=None` — request sent with empty body, no exception.
- **`except` too wide swallows unrecoverable errors** — `except (RequestException, HTTPError)` over a retry loop will also catch `InvalidURL`, `MissingSchema`, `SSLError` — user sees "3 retries failed" instead of "URL typo".
- **Missing `raise ... from last_error`** — re-raising inside retry loops without `from` loses the original traceback; debugging becomes guesswork.
- **Retry-After header ignored** — code uses exponential backoff for 429 responses while the server explicitly provided `Retry-After`. Honor the header.
- **`sleep()` doesn't support sub-second in some environments** — `time.sleep(0.5)` works, but `sleep` from C shell / POSIX utilities doesn't. Watch for integer-only assumptions in shell-like code.
- **`max_retries=-1` / `max_retries < 0`** — for-loop doesn't run, `last_error` stays `None`, final raise prints `"Failed after 0 attempts. Last error: None"`.
- **Mutable-default / mutable parameter passthrough** — `headers=opts.headers` passes a caller's dict that a library may mutate in place.
- **`response` not closed** — returning `requests.Response` without `with`/`.close()` leaks the TCP connection.
- **`dataclass` / type-hint gotchas** — Python version mismatch between `from __future__ import annotations` and `dict[str, str]` subscripting.
- **`@dataclass` / regex / character-class visual noise** — **MANDATORY**: re-run `python3 -c "import ast; ast.parse(open(FILE).read())"` before claiming any indentation / syntax error. See SKILL.md Step 3.3.

---

## JavaScript / Node

Apply to `.js`, `.mjs`, `.cjs`.

- **Socket-idle timeout ≠ overall request timeout (slowloris)** — `req.setTimeout(ms)` fires only after `ms` of *no* I/O. A server replying 1 byte/sec keeps the timer alive forever. Use `AbortController` + `AbortSignal.timeout()` for an overall cap.
- **`body += chunk` without `maxBodySize`** — unlimited accumulation is an OOM / DoS vector on adversarial or large responses.
- **Multi-byte characters split across chunks** — default `chunk` is a `Buffer`; implicit string concat corrupts UTF-8 at chunk boundaries (`\uFFFD`). Use `res.setEncoding('utf8')` or collect Buffers and decode once.
- **`Math.pow(2, attempt)` backoff uncapped** — high `attempt` → astronomical delay. Use `Math.min(MAX_DELAY, base * 2^attempt) + jitter`.
- **`lastError` possibly null** — `{ maxRetries: -1 }` leaves `lastError` null; `lastError.message` throws TypeError.
- **Doesn't follow redirects** — Node's `http.get` returns `statusCode:301, body:''`. Caller's `statusCode < 400` check passes; result is treated as success.
- **`fetchWithRetry(url)` only supports GET** — named like a general client, no method / body / headers options.
- **Input params not validated** — `maxRetries: NaN` makes `attempt <= NaN` permanently false; `timeout: "10000"` confuses timers.
- **URL parsed twice** — `new URL(url)` then `client.get(url, ...)` — prefer passing the parsed URL object.
- **No AbortController / cannot cancel retry** — long retry loops hold resources; caller has no cancellation primitive.

---

## TypeScript / React (TSX)

Apply to `.ts`, `.tsx`.

- **`dangerouslySetInnerHTML` XSS in error-message strings** — the riskiest pattern: error strings that embed user input (e.g., `"\`${email}\` is not a valid address"`) rendered with `dangerouslySetInnerHTML` → script executes on validation failure.
- **`dangerouslySetInnerHTML` XSS in "welcome" templates** — `Welcome, ${name}` templated into innerHTML is a reliable payload for cookie theft.
- **`fetch` without `response.ok` check** — `setSubmitted(true)` runs on server 500 — user thinks the save succeeded.
- **No `try/catch` around `fetch`** — DNS failure, network drop, or abort throws and kills the component.
- **CSRF / `credentials` not explicit** — cookie-based auth needs `credentials: 'include'`; missing CSRF token header when back-end requires it.
- **No loading / disable state → double-submit** — multi-click sends multiple POSTs.
- **Trim applied to validation but not to stored value** — `"  Alice  "` passes length validation but reaches the API with padding.
- **Untrimmed length check** — `name.length > 100` on `"Alice" + " ".repeat(96)` flags a 5-char name.
- **`submitted` state never resets** — success page is terminal; no "add another" escape.
- **Validation only on submit** — `onBlur` validation is much friendlier.
- **JSX input `name` drifts from the state schema** — adding `<input name="foo" />` silently adds `foo` to `formData`; TypeScript doesn't catch it.
- **Regex / character-class visual noise** — **MANDATORY**: before claiming a regex has an unintended space, run it through `python3 -c "import re; print(re.match(r'PATTERN', 'TEST'))"` or a Node `new RegExp(...)`. See SKILL.md Step 3.3.

---

## Shell / Bash

Apply to `.sh`, `.bash`.

- **`&& true` after command substitution masks failures** — `response=$(curl ...) && true` avoids `set -e` abort but swallows every curl exit code including binary-not-found and TLS errors.
- **`2>&1` inside `$(...)` pollutes captured output** — DNS error text gets piped into response parsing; `tail -n1` picks up human-readable English.
- **`2>/dev/null` on `[ -ge ... ]`** — suppresses the type error you should have prevented; the comparison silently evaluates false, retry loop continues with nonsense state.
- **`$(())` fails on non-integers and aborts under `set -e`** — `retry_delay="1.5"` → arithmetic error → whole script dies.
- **`sleep` integer-only (POSIX)** — loses sub-second precision; some coreutils accept floats but don't assume it.
- **Missing `--connect-timeout`** — `--max-time` is overall; DNS/TCP handshake can still hang.
- **`echo "$response" | tail/sed` with special chars** — `echo` handles `-n`, `-e`, `\t` inconsistently across shells. Use `printf '%s\n' "$response"`.
- **`tail -n1` captures a numeric body line as the status code** — if the body's last line is a plain number and no trailing newline, parsing breaks.
- **Missing `-sS`** — `--silent` hides progress AND errors; `-sS` keeps errors on stderr.
- **`max_retries=-1` / negative numeric params** — loop skipped, `last_error` stays empty → `"Failed after 0 attempts. Last error: "`.
- **`set -euo pipefail` + complex pipelines** — `pipefail` surprises on `curl | tail` when tail exits before curl.
- **`"$@"` / `"$*"` / regex character-class visual noise** — **MANDATORY**: run `bash -n FILE` and/or `grep -n` the exact bytes before claiming spaces or syntax errors. See SKILL.md Step 3.3.

---

## PHP

Apply to `.php`.

- **No `try/finally` around `curl_close`** — early exception leaks the cURL handle.
- **GET + body** — `CURLOPT_CUSTOMREQUEST => "GET"` with `CURLOPT_POSTFIELDS` set confuses cURL and proxies; also semantically wrong.
- **`catch (RuntimeException)` too narrow** — PHP 8's `ValueError` and `TypeError` don't inherit from `RuntimeException`; bad URL throws `ValueError` and escapes.
- **`curl_init` failure** — PHP 7 can return `false`, PHP 8 throws `ValueError` on invalid URL; check return and version-specific behavior.
- **Missing `CURLOPT_CONNECTTIMEOUT`** — only `CURLOPT_TIMEOUT` is set; DNS/TCP handshake uncovered.
- **SSL verification not explicit** — the default is `true`, but explicit `CURLOPT_SSL_VERIFYPEER` / `CURLOPT_SSL_VERIFYHOST` is safer when libraries override defaults.
- **`$headers` format undocumented** — cURL wants list format `['Header: value']`; developers pass assoc array and get broken requests.
- **`sleep()` integer-only** — use `usleep($delay * 1_000_000)` for sub-second.
- **Default doesn't follow redirects** — `CURLOPT_FOLLOWLOCATION => false` by default; 3xx passes `< 400` check with empty body.
- **Exception chain lost** — final `new RuntimeException("...")` without previous throwable argument drops the stack trace.
- **Function in global scope** — no namespace / class static; name collisions likely.

---

## Java

Apply to `.java`.

- **`HttpURLConnection` / reader close not in try-with-resources** — early throw leaks `BufferedReader`; error branch's `getErrorStream()` also needs to be drained.
- **`catch (Exception e)` swallows `InterruptedException`** — `Thread.sleep` interrupt clears the flag; retry loop continues running after user asked for cancellation.
- **`retryDelayMs * (long) Math.pow(2, attempt)`** — `Math.pow` on integer exponents is imprecise; use `1L << attempt`. Also uncapped.
- **`InputStreamReader` without charset** — platform default causes cross-env differences.
- **`readLine()` changes newlines** — `\r\n` → `\n`; last line gets a trailing `\n` appended. Kills signature validation / raw-body use cases.
- **`throws Exception` / `catch (Exception)`** — too generic; tighten to `IOException, InterruptedException`.
- **`new URL(String)`** — deprecated in Java 20+; prefer `URI.create(url).toURL()`.
- **No logging around retries** — failures are silent.
- **No Retry-After handling for 429** — same pattern as Python.
- **No jitter on backoff** — thundering herd in distributed systems.

---

## Cross-language patterns (always check)

Regardless of language, for HTTP client / retry / validation code:

- [ ] 4xx (except 429) retried — always a suppression pattern.
- [ ] Backoff is exponential without cap AND without jitter.
- [ ] `Retry-After` header ignored.
- [ ] `max_retries` / `maxRetries` negative not guarded.
- [ ] Exception chain lost when re-wrapping errors.
- [ ] Input validation missing for `url`, `method`, numeric params.
- [ ] No timeout at all, or timeout is socket-idle not overall.
- [ ] Body silently dropped for unexpected types.
- [ ] URL is interpolated from untrusted input without SSRF guard.
- [ ] Response body accumulation has no max size.
- [ ] Response body character encoding assumed without declaration.

---

## Provenance

Each bullet above is sourced from the finding tables in `demos/Demo-1/review-results/code-review-*.md` (2026-04 benchmark). If you find a recurring class of issue not represented here, add a bullet and a short reproduction note.
