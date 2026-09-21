# arxiv-digest → deep-reading Handoff Contract

This contract preserves the boundary between meeting-oriented digestion and self-study deep reading.

## Trigger
Invoke only after the user explicitly confirms Step 5c.

## Caller responsibilities: arxiv-digest
Provide verified values already collected:
- source URL / arXiv ID
- title
- authors
- publication/submission date
- version when known
- source status (normally preprint unless verified otherwise)

Declare completed work:
- core digest / paper purpose
- method and innovation summary
- key experimental evidence already extracted
- limitations already identified
- TrendLife connection
- community perspectives
- one-slide version

Request:
```yaml
mode: Deep
include:
  - complete mental models
  - reasoning depth
  - evidence boundaries
  - hidden assumptions
  - derived insights
  - knowledge gaps
  - knowledge stress test
  - teachable framework
  - cross-domain connections
```

## Callee responsibilities: deep-reading
- Reuse verified upstream metadata.
- Do not repeat completed digest sections unless correction or additional evidence requires it.
- Add depth intentionally omitted by the digest.
- Preserve the Document-centric → Knowledge-centric → User-centric boundary.
- Append under `## 🔬 Deep Dive — <title>` when the caller provides the existing note as destination.
- Preserve existing digest text.

## Failure behavior
If deep-reading cannot access information needed beyond the digest, it should continue from the supplied verified material, identify the missing evidence, and avoid guessing. It must not silently convert unverified upstream claims into facts.
