# Race host decision (Cup window)

**Decision (2026-10-06):** Race on the **Mac** for this Cup window. Hermes copy-migrate is ready as a backup path; Cursor Cloud / Grok agents are **not** race hosts.

| Host | Role |
|------|------|
| **Mac** (primary) | Amphetamine + Docker API/Gateway/bot + LaunchAgents. Proven: R003m 48h PASS, S001 ~12h. |
| **Hermes** (backup) | Copy-migrate existing stack — see [`HERMES_COPY_MIGRATE.md`](HERMES_COPY_MIGRATE.md). No Condor on DO for now. |
| **Cursor Cloud / Grok agent** | **Rejected** as live race host — see below. |

## Rejected: Cursor Cloud / Grok as race host

Cursor Cloud Agents and “run it on Grok” are **coding environments**, not 48h trading hosts:

- Ephemeral VM / session lifecycle — not an unattended VPS.
- Billed as **model tokens**, not cheap always-on compute; keeping a chat alive for 48h is expensive and still unreliable.
- Putting the Solana signing wallet in Cloud Secrets for live LP is the wrong trust model.
- A Grok **model** choice does not add a host.

Allowed use of Cloud Agents: optional short help *installing* Hermes (SSH docs, compose debugging). Never deploy the race bot or import the wallet into a Cloud Agent VM.

## Cup open

- Mac: [`RACE_START_MAC.md`](RACE_START_MAC.md) — Botcamp window **2026-10-07T02:00Z → 2026-10-09T02:00Z**; LaunchAgent `com.hummingbot.cup-race-autotimer` auto-starts/flattens.
- Hermes (only if you cut over): [`HERMES_COPY_MIGRATE.md`](HERMES_COPY_MIGRATE.md)

## Ops pointers

- [`MAINNET_OPS.md`](MAINNET_OPS.md) — status / hard-restart / LaunchAgents
- [`future-plans/HERMES_WATCHDOG_PORT.md`](future-plans/HERMES_WATCHDOG_PORT.md) — older full rebuild plan (superseded for Cup by copy-migrate)
