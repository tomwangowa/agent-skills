# How tech-feasibility Was Born: A Story That Started with an Amazon Scraper

---

On an ordinary Wednesday afternoon, an engineer stared at his screen, a question circling in his head:

> "Can residential proxies actually let me scrape Amazon reviews without getting caught?"

He had 10 Amazon accounts, a headless Chrome setup, and the nodriver package. The plan looked perfect — account rotation, IP masking, automated browsing — it sounded like something out of a spy movie.

But he didn't rush to write code.

He asked a more fundamental question: **"How do I *systematically* figure out if this road leads anywhere?"**

---

## A Wilderness of Methodologies

He surveyed the existing frameworks. NASA's TRL? Way too heavy — that's for rockets. Jump straight to a PoC? If the direction itself is a dead end, all that time is wasted. Decision Matrix? That assumes you already have multiple options to compare.

He already had a useful tool — **critical-research**, a falsification-first research skill. But critical-research is designed to judge whether "a claim is true or false," and what he needed was "whether a technology fits my specific situation."

A subtle but crucial difference.

"I don't need a general truth-or-false verdict," he thought. "I need a **fit analysis** — how much overlap is there between what the tech offers and what I actually need?"

---

## An Unguided Improvisation

So he took the Amazon scraper scenario and let an AI agent run it "naked" — no methodology, no guardrails, just see what it does on its own.

The result came back. A 1,500-word essay that looked professional, but on closer inspection:

- All analysis was a single undifferentiated blob — no decomposition
- Pro and con evidence interleaved randomly — you still couldn't tell if it was a go or not
- The conclusion was "6/10" and "HIGH risk" — is that a Go or a No-Go?
- Alternatives were tacked on at the end, like an afterthought
- The most fatal flaw: **no definition of when to walk away**

"If even an AI makes these mistakes," he laughed, "humans are definitely worse."

He catalogued all 10 deficiencies. This was his **RED test** — what goes wrong when there's no methodology in place.

---

## A Methodology Grown from Defects

He started designing a workflow, each step targeting a specific deficiency:

**No decomposition?** → Step 1: Break the big question into 4-8 independently testable sub-hypotheses.

**No predefined exit conditions?** → Step 2: Define Kill Criteria before starting research. This step is critical — it blocks humanity's favorite psychological trap: the sunk cost fallacy. "I've already spent so much time researching, might as well keep going." No. You should know when to cut your losses before the research even begins.

**Pro and con evidence jumbled together?** → Steps 3-4: Borrow the falsification-first principle from critical-research. For each sub-hypothesis, search for counter-evidence first, then supporting evidence.

**No way to tell if tech matches requirements?** → Step 5: A Fit Analysis table — one column for "what you need," one for "what the tech provides," and a final column with only three options: Y / N / ?.

That `?` is particularly important. It means "can't determine from desk research alone — needs a PoC."

**Vague conclusion?** → Step 7: Force a four-way choice — Go / Conditional-Go / Pivot / No-Go. "It depends" is not allowed.

He named the framework **TFAR** — Technology Feasibility Assessment & Research. Sounds very official. It's really just a fancy name for "think before you build."

---

## Round Two: Amazon with a Methodology

He had the same AI agent run the same Amazon scenario, this time armed with the new methodology.

The result was dramatically different.

The agent decomposed the problem into 8 sub-hypotheses: Can residential proxies bypass IP blocking? Can nodriver fool browser fingerprinting? Are 10 accounts enough? Is the cost manageable? Is it legal? Is there a simpler alternative?

Then it defined Kill Criteria: "If industry consensus says using logged-in accounts for scraping leads to bans = abandon immediately."

Then it started gathering evidence. Counter-evidence first.

The result: at H2 (account safety), a Kill Criterion was triggered — industry best practice **explicitly forbids** using logged-in accounts for scraping. Not "we suggest avoiding it," but "**absolutely prohibit**." The Klarna cautionary tale was right there too: laid off 700 people and replaced them with AI, customer satisfaction tanked, had to rehire humans.

Final verdict: **No-Go**. Not because residential proxies don't work (they actually work great, 97-99% success rate), but because the account pool strategy itself is a dead end.

Even more valuable: the report simultaneously recommended a Pivot — drop the account login entirely and scrape as a guest, or just use a managed service like Scrapingdog ($15-75/month, cheaper than doing it yourself).

The baseline's 10 deficiencies? **All fixed.**

---

## The Final Gate: Quality Audit

He ran skill-auditor. First score: 40 — missing Error Handling, Security Considerations, and Examples.

"Can't even pass my own audit tool. Embarrassing."

He added the missing sections, ran it again: 78/100, 0 critical issues, production-ready.

Done. Commit, push, call it a day.

---

## Epilogue

tech-feasibility wasn't born from a flash of genius. It started from a concrete problem ("will residential proxies work?"), went through one failed baseline test, and was reverse-engineered from 10 specific deficiencies.

Its most important design decision might be its least flashy one: **Kill Criteria up front.**

Because in the real world, what leads people to terrible technology decisions isn't usually a lack of information — it's the refusal to admit they've taken a wrong turn, right at the moment they should be walking away.
