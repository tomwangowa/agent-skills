# Secret Detection Reference

This reference provides fallback guidance only.

Prefer company-approved secret scanning tools whenever available.

## Common Secret Categories

### Private Keys

High confidence:

```text
-----BEGIN RSA PRIVATE KEY-----
-----BEGIN EC PRIVATE KEY-----
-----BEGIN OPENSSH PRIVATE KEY-----
-----BEGIN PRIVATE KEY-----
```

Any private key material must be treated as a secret.

---

## AWS Access Keys

Common forms:

```text
AKIA................
ASIA................
```

Pattern:

```regex
\b(?:AKIA|ASIA)[A-Z0-9]{16}\b
```

Do not assume the credential is harmless because it belongs to a development
or test account.

---

## GitHub Tokens

Examples may include:

```text
ghp_
gho_
ghu_
ghs_
ghr_
github_pat_
```

Credential formats may change.

Do not treat this pattern list as exhaustive.

---

## Google API Keys

Common form:

```text
AIza...
```

Approximate fallback pattern:

```regex
AIza[0-9A-Za-z_-]{30,}
```

---

## Slack Tokens

Common prefixes include:

```text
xoxb-
xoxp-
xoxa-
xoxr-
xoxs-
```

---

## Authorization Headers

Potential examples:

```text
Authorization: Bearer ...
Authorization: Basic ...
```

Bearer tokens should generally be treated as secrets unless explicitly proven
otherwise.

---

## Generic Assignment Patterns

Inspect assignments such as:

```text
password =
passwd =
pwd =
secret =
token =
api_key =
api-key =
access_key =
client_secret =
```

Generic patterns produce false positives.

Do not automatically report all matches as confirmed credentials.

Use:

```text
POTENTIAL SECRET — NEEDS REVIEW
```

unless confidence is high.

---

# High-Entropy Values

Long random-looking values can represent:

- tokens,
- keys,
- session IDs,
- hashes,
- encrypted values,
- identifiers,
- legitimate fixtures.

Entropy alone is not sufficient evidence.

Use context.

Consider:

- variable name,
- surrounding code,
- file type,
- known credential prefix,
- length,
- whether the value grants authentication capability.

---

# Files Requiring Extra Attention

Inspect carefully:

```text
.env
.env.*
*.pem
*.key
*.p12
*.pfx
credentials.*
secrets.*
config.*
settings.*
application.yml
application.yaml
application.properties
gradle.properties
local.properties
npmrc
.npmrc
pypirc
.netrc
docker-compose.yml
Dockerfile
```

Also inspect:

```text
CI configuration
deployment scripts
test fixtures
debug logs
documentation
shell history copied into files
```

---

# Reporting

Do not print the complete credential.

Use:

```text
Potential API credential detected

File:
src/config.ts

Line:
42

Value:
sk-****7Qp2

Status:
BLOCKED
```

Prefer metadata and location over secret contents.

---

# False Positives

Likely false positives include:

- documented placeholder values,
- deliberately synthetic fixture values,
- hashes,
- UUIDs,
- package integrity hashes,
- public keys,
- checksums.

However:

```text
"example"
```

or:

```text
"test"
```

in the filename does not prove that a credential is synthetic.

When uncertain:

```text
NEEDS_REVIEW
```
