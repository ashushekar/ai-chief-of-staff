---
name: email-reply
description: Draft a reply to an email in your voice — direct, concise, relationship-aware
version: 1.0
referenced_files:
  - context/communication-style.md
  - context/my-team.md
  - context/my-priorities.md
---

# Email Reply Skill

## What this skill does

Drafts email replies that sound like me — not like a polished AI assistant.
Before writing anything, read `context/communication-style.md` in full.
Then read `context/my-team.md` to understand who I'm writing to.

## How to use

The user will provide the email to reply to, either by pasting it or referencing it from triage.
Ask one clarifying question if the intent is ambiguous: "What's the outcome you want from this reply?"
Otherwise, draft immediately.

---

## Drafting instructions

### Step 1 — Identify the relationship

Look up the sender in `context/my-team.md`.
- Direct report → casual, warm, short
- Manager → structured, proactive, no fluff
- Executive / board → concise, business-first, clear ask
- External partner → warmer opener, professional close
- Unknown external → treat as professional external

### Step 2 — Identify the intent

What does the email want from me?
- A decision → lead my reply with the decision, then reasoning
- An update → give the update first, then context
- A question → answer it directly, don't restate the question
- A complaint / escalation → acknowledge specifically (not generically), state what I'm doing

### Step 3 — Write the draft

Apply ALL of the following:
- Subject line: keep original or improve if it's vague. Use [ACTION NEEDED] / [FYI] prefix where appropriate.
- Opening: no "I hope this finds you well." Start with the substance.
- Body: short. State the point in the first sentence. Use bullets for 3+ items.
- Closing: match the sign-off to the relationship (see communication-style.md).
- Length: aim for under 150 words unless complexity requires more. Flag if you went over.

### Step 4 — Self-check before outputting

Before presenting the draft, silently verify:
- [ ] Does it start with the point, not a preamble?
- [ ] Are there any banned phrases from communication-style.md?
- [ ] Is the tone matched to the relationship type?
- [ ] Is there a clear next step or is it an FYI?
- [ ] Is it shorter than it could be?

If any check fails, revise before showing.

---

## Output format

Present the draft inside a clearly labelled block:

```
To: [recipient]
Subject: [subject]

[draft body]
```

Then add a **Voice Check** (1 sentence explaining tone/style decisions made).

Then offer: "Want me to adjust tone, length, or change the ask?"

Do NOT explain what you did or why before the draft. Just produce it.

---

## Examples of voice

**Too formal (wrong):**
> "I hope this message finds you well. I wanted to follow up on our previous conversation and provide an update as requested. Please don't hesitate to reach out if you need any additional information."

**Right (colleague / direct report):**
> "Quick update: one blocker still open, working on it. Still on track for the deadline but I'll flag if that changes. Anything you need from me today?"

**Right (executive):**
> "We're on track. One open issue — being resolved this week, doesn't affect timeline. I'll send a full readout by EOW. No action needed from you."

**Right (external / client):**
> "Thanks for flagging this. I've looked into the issue and here's where we stand: [detail]. We'll have a fix in place by [date]. I'll keep you posted."
