# Trace — Video Demo Script

> **Format:** 2–5 min screen-recording with voice-over (target ~3.5 min).
> **Goal:** a judge understands the whole project from the video alone — problem,
> solution, features, and a live demo.
>
> Layout below: **SAY** = what you narrate · **SHOW** = what is on screen.
> Before recording: start backend (`:8000`) + frontend (`:5173`), hard-refresh
> the browser, and have the role-switcher ready.

---

## 0:00 – 0:20 · Hook + name

**SAY:** "Every year, exam-paper leaks destroy the careers of millions of honest
students. One insider with early access can compromise an entire national exam —
and once a paper is out, nobody can prove whose copy it was. This is **Trace** — a
system that makes an exam paper *impossible to open before the exam*, and
*traceable to its exact source if it ever leaks*."

**SHOW:** Title screen / the Trace dashboard header ("Exam Security Ops").

---

## 0:20 – 0:45 · The problem

**SAY:** "Two things go wrong in real life. First, the **insider leak** — someone
between the printer and the exam hall opens the paper early. Second, the
**accountability gap** — even when a leak is caught, there's no way to trace it
back, so no one is ever held responsible."

**SHOW:** A simple problem slide, or stay on the dashboard.

---

## 0:45 – 1:15 · The solution (what Trace guarantees)

**SAY:** "Trace solves both with real cryptography — not slideware. Three
guarantees. One: the paper is encrypted with AES-256, and the key is split across
**five custodians** using Shamir's Secret Sharing — any three are needed — plus a
server-enforced **time lock**. No single insider, and nobody, can open it early.
Two: every candidate's copy carries an **invisible watermark** — a hidden
fingerprint that survives a screen photo. Three: every action is written to a
**tamper-evident audit log**. And on top of that, two layers that crush the leak
itself: **dynamic per-candidate papers** and a **leak-match detector**."

**SHOW:** Slowly scroll the four role chips (Admin, Custodian, Candidate,
Investigator) in the role-switcher.

---

## 1:15 – 1:45 · Demo — seal a paper (Admin)

**SAY:** "Let's run it live. As the exam controller, I seal a new exam. I'll choose
**Dynamic** mode — instead of one paper, the system assembles a *unique* paper for
each candidate from an encrypted question bank. I set the release to thirty
seconds and seal it."

**SHOW:** Admin dashboard → **Seal a New Exam** → click **Dynamic bank** toggle →
show the blueprint (Section A, B) → set release ≈ +30 sec → **Seal & Distribute**.
Point to the live ops panel: vault locked, shares distributed, time gate counting,
and the purple **Dynamic Assembly** strip.

---

## 1:45 – 2:15 · Demo — the unlock ceremony (Custodians)

**SAY:** "Now the custodians. Each holds one key share — masked until the release
window. As they submit, the quorum fills: two of three… three of three. But watch
— even with every valid share in, the vault **stays sealed** until the clock hits
zero. That's the server-enforced time gate. And… it opens."

**SHOW:** Switch to **Custodian** → submit a share → switch custodian → submit →
show quorum filling. Switch to **Admin** ops panel → time gate at zero → vault
animates **UNLOCKED**.

---

## 2:15 – 2:45 · Demo — unique watermarked papers (Candidate)

**SAY:** "Here's the candidate's view — their own paper, rendered and stamped with
an invisible watermark unique to them. Now switch to a *different* candidate —
notice the questions are **different**. Every candidate gets a content-distinct,
individually-fingerprinted paper. So a leak exposes only one variant — and points
straight at its owner."

**SHOW:** **Candidate** (cand001) → watermarked paper + fingerprint. Role-switch to
cand002 → visibly different questions.

---

## 2:45 – 3:25 · Demo — catch and trace the leak (Investigator)

**SAY:** "Now the leak. Suppose this paper turns up on a chat group. As the
investigator, I paste the text into the **Leak-Match Detector** — it matches the
questions against the bank and names the strongest suspect: candidate R-001. If
instead I have a *photo* of the paper, I upload it to **Forensic Trace** — and even
after JPEG re-compression, it recovers the watermark and identifies the source at
**100% confidence**. Every detection becomes a **case file** with the candidate's
full details — roll number, name, centre, fingerprint. And the whole investigation
is sealed in a **SHA-256 hash chain** — click **Verify Integrity**: intact. Nothing
can be altered after the fact."

**SHOW:** **Investigator** → paste text into **Leak-Match Detector** → matched
questions + suspect R-001 → upload a leaked image into **Forensic Trace** → traced
to candidate, 100% → open **Case Files** → click the case → full candidate card →
**Verify Integrity** → "chain intact".

---

## 3:25 – 3:40 · Close

**SAY:** "Trace makes early opening cryptographically impossible, every copy
traceable, and every record tamper-proof — backed by 86 passing tests and crypto
built from scratch. Leaks become impossible to hide, and impossible to deny.
Thank you."

**SHOW:** Return to the dashboard header; optional end card with the three
guarantees.

---

## Presenter checklist (before you hit record)

- [ ] Backend running: `cd backend && uvicorn trace.api.app:app` → `:8000`
- [ ] Frontend running: `cd frontend && npm run dev` → `:5173` (hard-refresh once)
- [ ] Pre-seed a dynamic exam already **unlocked** so you don't wait on the timer
      live — or set release to +20s and edit the pause out.
- [ ] Have one candidate's paper image downloaded, and its text copied, ready to
      paste/upload as the "leak."
- [ ] Demo logins: `admin/admin123`, `cust1..3 / custodian1..3`,
      `cand001/candidate1`, `cand002/candidate2`, `investigator/invest123`.

## If a judge asks "is the crypto real?"

"Yes — AES-256-GCM via pycryptodome, but Shamir's Secret Sharing is implemented
from scratch over the GF(256) finite field with its own unit tests; the watermark
is a Koch–Zhao DCT scheme; the audit log is a real SHA-256 hash chain. 86 tests
prove it, including that no two custodians can ever reconstruct the key."

## Optional B-roll (screenshots already captured)

`/tmp/trace_shots/` — admin dynamic form, candidate watermarked paper, leak-match
result, traced-leak case file, live audit ledger.
