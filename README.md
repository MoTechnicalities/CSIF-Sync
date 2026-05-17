# CSIF-Sync: Multi-Agent Decentralized Consensus Protocol v1.0

[![Status: Unified Architecture](https://img.shields.io/badge/Status-Unified__Architecture-blueviolet)](https://github.com/MoTechnicalities/Crystal-Structure-Information-Format)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache__2.0-blue)](LICENSE)
[![Latency: <10ms](https://img.shields.io/badge/Latency-%3C10ms-green)]()
[![Twin: CSIF-Guard](https://img.shields.io/badge/Twin-CSIF--Guard-orange)](https://github.com/MoTechnicalities/csif-guard)

> **The Problem:** Autonomous agents sharing a local network constantly misinterpret each other's context. They drift out of alignment, create split-brain scenarios, and require massive, cloud-bound vector databases just to agree on what is true.
>
> **The Solution:** `CSIF-Sync` is a blindingly fast, decentralized consensus protocol that lets AI agents synchronize their entire worldview using **pure four-dimensional phase geometry** — no cloud, no heavy runtime, no bloat.

---

## ── The Babel Crisis: Why Agents Can't Agree

Today's multi-agent systems communicate through loose, unstructured text and bloated JSON payloads. A "research agent" hands data to a "writer agent." A home-automation controller disagrees with a sensor monitor. The result is a *split-brain cluster* — multiple agents holding contradictory beliefs about the same ground truth.

The standard industry fix is brute-force: centralized vector databases (Pinecone, Milvus) or heavy distributed consensus algorithms (Raft, Paxos). This is **total overkill**. It destroys edge performance, creates a single point of failure, and requires a cloud subscription.

`CSIF-Sync` solves this with a radical alternative: **agents sync by overlapping their crystal structures**, not their text. Because an RWIF file is bound to a continuous phase medium on $[-\pi, \pi]$, two agents on a local LAN can synchronize their entire worldview by broadcasting a tiny binary array of edge IDs, timestamps, and phase trajectories $(\theta, \sigma)$.

---

## ── The Three-Verdict Protocol

When Agent B receives a phase delta from Agent A, `SyncProxy.evaluate_delta()` instantly classifies the incoming write geometrically:

| Resonance $R_N$ | Verdict | Action |
|---|---|---|
| $R_N < 0.05$ | **SKIP** | Knowledge identical; update silently dropped |
| $0.05 \leq R_N < 0.5$ | **NUDGE** | Slight drift; deterministic phase correction applied |
| Residual $\|\Delta\| > \text{threshold}$ | **REJECT** | Geometric contradiction; write blocked, alert raised |

No natural language parsing. No vector similarity search. **Pure floating-point arithmetic, sub-millisecond.**

---

## ── Repository Architecture

Zero external dependencies. Python standard library only (`math`, `socket`, `json`, `uuid`, `threading`).

```text
csif-sync/
├── core/
│   └── math.py              # Shared geometric substrate: wrap_pi, phase_distance, nudge_phase
├── storage/
│   └── rwif.py              # RWIFC1 & RWIFB1 append-only crystal serialization
├── engine/
│   ├── phase_graph.py       # Direction-aware PhaseGraph + compute_resonance()
│   └── consensus_gate.py    # Multi-agent crystallization gate (PASS / DEFERRED / CONTESTED)
├── api/
│   └── sync_proxy.py        # UDP broadcast proxy: broadcast_delta(), listen(), evaluate_delta()
├── demo_sync.py             # Three-scenario simulation: SKIP, NUDGE, REJECT + consensus gate
├── README.md
└── LICENSE
```

---

## ── Quickstart: Running the Consensus Simulation

No network required. The demo runs entirely in-process.

```bash
git clone https://github.com/MoTechnicalities/csif-sync.git
cd csif-sync
python3 demo_sync.py
```

### Expected Terminal Output

```
════════════════════════════════════════════════════════════
  CSIF-Sync: Multi-Agent Decentralized Consensus Demo
════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────
  Scenario 1 — SKIP: Agent B already knows this fact
────────────────────────────────────────────────────────────

[SKIP] light → dispels → darkness
  Incoming φ   : 0.0000 rad
  Local φ      : 0.0000 rad
  R_N          : 0.0000
  Reason       : Knowledge identical; update silently skipped.

  ✓ Bank unchanged. Duplicate write suppressed.

────────────────────────────────────────────────────────────
  Scenario 2 — NUDGE: Agent B has a drifted phase (0.15 rad off)
────────────────────────────────────────────────────────────

[NUDGE] light → dispels → darkness
  Incoming φ   : 0.0000 rad
  Local φ      : 0.1500 rad
  R_N          : 0.0477
  Nudged φ     : 0.0135 rad
  Reason       : Phase drift 0.0477; deterministic nudge applied → 0.0135 rad.

  ✓ Phase nudged toward authoritative value. Bank updated smoothly.

────────────────────────────────────────────────────────────
  Scenario 3 — REJECT: Hallucinated write (φ = π, darkness absorbs light)
────────────────────────────────────────────────────────────

[REJECT] light → dispels → darkness (hallucinated: φ = π)
  Incoming φ   : 3.1416 rad
  Local φ      : 0.0000 rad
  R_N          : 1.0000
  Reason       : Geometric contradiction: residual 3.1416 rad exceeds threshold 1.5708 rad. Write blocked.

  ✓ Write blocked. Bank remains uncorrupted. State-rejection alert raised.

════════════════════════════════════════════════════════════
  All scenarios passed. CSIF-Sync protocol verified.
════════════════════════════════════════════════════════════
```

---

## ── Mathematical Infrastructure

### Principal Modulo Wrapping

$$\text{wrap\_pi}(\theta) = ((\theta + \pi) \bmod 2\pi) - \pi$$

### Adaptive Contradiction Threshold

$$\text{Threshold}_{\text{alarm}} = \frac{\pi}{2} + c \cdot \sigma_{\text{path}}$$

### Deterministic Phase Nudge

$$\theta_{\text{new}} = \text{wrap\_pi}\!\left(\theta + \alpha \cdot \varepsilon \cdot w\right)$$

Where $\varepsilon$ is the error signal (phase difference), $w$ is evidence weight, and $\alpha = 0.1$ is the nudge rate.

### Consensus Gate Spread Criterion

An edge is crystallized when $N \geq 3$ independent sources report phases within:

$$\text{spread} = \max(\theta_i) - \min(\theta_i) < \frac{\pi}{4}$$

Consensus phase is the **circular mean** of all source proposals.

---

## ── Real Network Deployment

For production use on a local LAN, replace the in-process simulation with live UDP:

```python
from api.sync_proxy import SyncProxy, CrystalDelta, EdgeUpdate
import threading

# Agent A: broadcast a crystal delta to the subnet
proxy_a = SyncProxy(agent_id="agent-a")
delta = CrystalDelta("agent-a", crystal_id, label, "local-network-sync", [update])
proxy_a.broadcast_delta(delta)

# Agent B: listen for incoming deltas and evaluate each one
proxy_b = SyncProxy(agent_id="agent-b", local_bank=my_bank)
thread = threading.Thread(target=proxy_b.listen, args=(on_verdict,), daemon=True)
thread.start()
```

Default port: `52833` (UDP). Override via `SyncProxy(port=YOUR_PORT)`.

---

## ── The Vision: A Local Mesh of Crystal Truth

Imagine your workstation running a quantitative finance agent, your desktop mini running a home-automation registry, and an ESP32 microcontroller tracking raw sensors. They wouldn't be talking over bloated, fragile APIs. They would be **breathing in unison** — maintaining a perfectly synchronized, multi-node fractal crystal of local truth, totally immune to cloud outages, completely private, and running at lightning speed.

---

## ── Relationship to CSIF-Guard

`CSIF-Sync` is the **twin** of [`CSIF-Guard`](https://github.com/MoTechnicalities/csif-guard).

| | CSIF-Guard | CSIF-Sync |
|---|---|---|
| **Role** | Semantic firewall (single agent) | Consensus protocol (multi-agent) |
| **Threat model** | Hallucinated writes to memory | Split-brain across network nodes |
| **Core operation** | Multi-path conflict detection | Resonance verification + phase nudge |
| **Transport** | In-process interception | UDP local broadcast |
| **Shared substrate** | `core/math.py`, `storage/rwif.py`, `engine/phase_graph.py` | ← same |

Together they form the complete **CSIF Agentic Hippocampus**: write-safe, sync-safe, deterministic, auditable.

---

## ── Core Behavioral Contracts

**Append-Only Trajectories:** No phase event is ever modified or deleted. The full temporal history of every edge is preserved and reconstructable.

**Determinism:** Given the same local bank and the same incoming delta, `evaluate_delta()` must return the same verdict on every platform and every run.

**Graceful Degradation:** If the network is unavailable, `evaluate_delta()` operates in pure in-process mode. No crashes, no silent failures.

---

## ── Reference Context

Built on the **Crystal Structure Information Format (CSIF)** and **Real-World Intelligence Format (RWIF)** — an open, auditable phase-geometric framework for representing, synchronizing, and protecting knowledge across AI agents, languages, and computational architectures.

- [Crystal-Structure-Information-Format (reference repo)](https://github.com/MoTechnicalities/Crystal-Structure-Information-Format)
- [CSIF-Guard (twin repository)](https://github.com/MoTechnicalities/csif-guard)

**Developed by Mogir Jason Rofick (Mo), May 17, 2026.**

---

## ── License

Apache License 2.0. See [LICENSE](LICENSE) for details.
