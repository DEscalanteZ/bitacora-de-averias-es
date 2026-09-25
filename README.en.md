# Failure log: the three ways AI automations break

> 🇪🇸 **[Versión en español → README.md](README.md)**

We keep a log of every incident in our AI-agent automations: watchdogs, data-fetching bots, dashboards, voice agents and daily reports, spread across several servers and three companies. In seven weeks (8 August to 25 September 2026) we logged **130 entries** (a few group several incidents, and several were caught before reaching production).

Almost all of the ones that carry a family label were **one of three things** wearing a different face.

## The three families

110 of the 130 entries state their family (the ones from the first weeks didn't). Of those 110, **106 are one of these three**; the other 4 were logged as a new family. Some fall into two:

| Family | What it is | Count |
|---|---|---|
| **1 · The false success** | A process finishes "fine" and did nothing | **46** |
| **2 · The unlisted piece** | Something runs without being registered, and nobody misses it when it dies | **32** |
| **3 · The unchecked conclusion** | Stating a negative ("there's no data", "it's broken") without ruling out that the fault is mine | **49** |

### 1 · The false success

It returns `OK`, exits with code 0, publishes stale files, or writes a fresh but empty result. The most dangerous one, because **it looks exactly like everything is fine**.

- **Three months without downloading a single invoice, reporting all was well.** A local variable shadowed a function; every email with an invoice crashed, an `except` swallowed it, and the bot carried on. The fix recovered 126 invoices.
- **A watchdog spent three weeks alerting through a channel that no longer delivered anything.** The messaging service returned `200 OK` even when it did **not** send; the reason was in the response body nobody read.
- **A tool returned `200` six times without a single result.** It was caught by the response **size** (266 bytes instead of 3,000+), not the status code.

**General lock:** check **what it produced**, never **that it ran**.

### 2 · The unlisted piece

- **After moving processes to a server, a lookup file wasn't copied.** The code opened it inside a silent `try/except`. For eight weeks one figure in the daily report came out 26–46% too low.
- **A connector built "just to look" on a laptop ended up feeding a forecast**, with no refresh and no watchdog. Its data had been frozen for two and a half months.

**General lock:** a **registry**. Anything that runs is registered the day it's created, and registration is closed by **proving the check fires** (hide its file, see if the watchdog complains).

### 3 · The unchecked conclusion

- **I declared 35 files lost; they were all in the cloud.** The search used a command that doesn't exist on that machine. It failed silently, and I read the silence as "nothing there".
- **A computer rebooted itself and I blamed a full disk.** It fit everything, and it was false. A cold reviewer knocked it down: the battery hit 1%, the system tried to hibernate, and the memory image didn't fit its fixed-size file.

**General lock:** before stating a negative, **rerun the test on a case you know works**. If the control fails too, the broken thing is you.

### And the one that hurts most

> **A diagnostic script that writes is not a diagnostic.**

I reran a script "to see what was happening". It fetched a half-finished download and **wrote it over** two months of good data. There was no backup anywhere.

## The lock: why a written lesson isn't enough

> **An incident isn't closed until it has a lock: something that runs and prevents it from happening again.**

A lock is a process that **refuses** to do the dangerous thing, a process that **stops** instead of carrying on silently, a watchdog that checks the **result** rather than the run, or a test that runs itself. A note in a document or "I'll be careful from now on" is **not** a lock.

## Template and tools

```markdown
## 2026-09-25 · Short title saying what happened (family: false success)
**Síntoma.** What you saw.            (Symptom)
**Causa real.** What it really was.   (Real cause)
**Cómo se comprobó.** The experiment that proved it.   (How it was verified)
**Candado.** What changed so it can't happen again, and how you proved it works.   (Lock)
```

- [`plantilla/BITACORA.md`](plantilla/BITACORA.md): an empty log ready to copy.
- [`herramientas/revisar_bitacora.py`](herramientas/revisar_bitacora.py): checks every entry (any dated heading, or any heading whose section uses the template labels) has its four sections filled in, a real lock (not empty, not "TODO") and its family; exits 1 otherwise, so it works in CI or a git pre-commit. Run `--prueba` to self-test. It expects the Spanish labels above.
- The [Spanish README](README.md#cómo-se-conecta-con-claude-code-o-con-cualquier-agente) has the `CLAUDE.md` snippet that makes Claude Code read the log before diagnosing and write it before closing.

## Related

- **[Six patterns for working with AI agents](https://github.com/DEscalanteZ/ai-agent-patterns-es)**
- **[Communication between two Claude Code agents on different computers](https://github.com/DEscalanteZ/comunicacion-entre-dos-claude-code-es)**

---

⭐ **If this helps you, star the repo**: it's the simplest way to help it reach more people.

*Author: David Escalante ([@DEscalanteZ](https://github.com/DEscalanteZ)). Text under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code in `herramientas/` is [MIT](herramientas/LICENSE).*
