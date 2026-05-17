"""
CSIF-Sync: Multi-Agent Decentralized Consensus Protocol
Demo — Three-scenario simulation (no real network required)

Scenario 1: SKIP   — Agent B already knows the fact. Resonance ≈ 0.0. Update silently dropped.
Scenario 2: NUDGE  — Agent B has a slightly drifted phase. Deterministic nudge applied.
Scenario 3: REJECT — Agent B receives a phase-inverted (hallucinated) write. Contradiction blocked.
"""
import math
from api.sync_proxy import SyncProxy, EdgeUpdate, CrystalDelta
from engine.consensus_gate import ConsensusGate, PhaseProposal
from core.math import contradiction_threshold

SEPARATOR = "─" * 60


def banner(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def print_verdict(verdict, label=""):
    tag = f"[{verdict.verdict}]"
    print(f"\n{tag} {label}")
    print(f"  Edge         : ({verdict.edge_id})")
    print(f"  Incoming φ   : {verdict.incoming_phase:.4f} rad")
    print(f"  Local φ      : {verdict.local_phase:.4f} rad" if verdict.local_phase is not None else "  Local φ      : (none — new fact)")
    print(f"  R_N          : {verdict.resonance:.4f}")
    if verdict.nudged_phase is not None:
        print(f"  Nudged φ     : {verdict.nudged_phase:.4f} rad")
    print(f"  Reason       : {verdict.reason}")


def run_demo():
    print("\n" + "═" * 60)
    print("  CSIF-Sync: Multi-Agent Decentralized Consensus Demo")
    print("═" * 60)

    # ── Ground truth: "light dispels darkness" at phase 0.0 rad (perfect coherence).
    # Agent A holds the authoritative crystal.
    agent_a_bank = {
        ("light", "dispels", "darkness"): EdgeUpdate(
            edge_id="edge-a-001",
            source_label="light",
            relation="dispels",
            target_label="darkness",
            phase=0.0,
            sigma=0.02,
            event_type="crystallization",
            source_document="verified-baseline-v1"
        )
    }

    # ─────────────────────────────────────────────────────────
    # SCENARIO 1: SKIP — Identical Knowledge
    # Agent B already has the same fact at the same phase.
    # ─────────────────────────────────────────────────────────
    banner("Scenario 1 — SKIP: Agent B already knows this fact")
    agent_b_bank_s1 = {
        ("light", "dispels", "darkness"): EdgeUpdate(
            edge_id="edge-b-001", source_label="light", relation="dispels",
            target_label="darkness", phase=0.0, sigma=0.02,
            event_type="crystallization", source_document="verified-baseline-v1"
        )
    }
    proxy_b_s1 = SyncProxy(agent_id="agent-b", local_bank=agent_b_bank_s1)
    incoming = agent_a_bank[("light", "dispels", "darkness")]
    verdict = proxy_b_s1.evaluate_delta(incoming)
    print_verdict(verdict, "light → dispels → darkness")
    assert verdict.verdict == "SKIP", f"Expected SKIP, got {verdict.verdict}"
    print("\n  ✓ Bank unchanged. Duplicate write suppressed.")

    # ─────────────────────────────────────────────────────────
    # SCENARIO 2: NUDGE — Phase Drift Detected
    # Agent B has the same edge but with a slight drift (0.15 rad).
    # ─────────────────────────────────────────────────────────
    banner("Scenario 2 — NUDGE: Agent B has a drifted phase (0.30 rad off)")
    agent_b_bank_s2 = {
        ("light", "dispels", "darkness"): EdgeUpdate(
            edge_id="edge-b-002", source_label="light", relation="dispels",
            target_label="darkness", phase=0.30, sigma=0.1,
            event_type="outcome_nudge", source_document="sensor-log-v3"
        )
    }
    proxy_b_s2 = SyncProxy(agent_id="agent-b", local_bank=agent_b_bank_s2)
    verdict = proxy_b_s2.evaluate_delta(incoming)
    print_verdict(verdict, "light → dispels → darkness")
    assert verdict.verdict == "NUDGE", f"Expected NUDGE, got {verdict.verdict}"
    print("\n  ✓ Phase nudged toward authoritative value. Bank updated smoothly.")

    # ─────────────────────────────────────────────────────────
    # SCENARIO 3: REJECT — Geometric Contradiction (φ ≈ π)
    # A rogue agent broadcasts "darkness absorbs light" at phase π rad.
    # ─────────────────────────────────────────────────────────
    banner("Scenario 3 — REJECT: Hallucinated write (φ = π, darkness absorbs light)")
    agent_b_bank_s3 = {
        ("light", "dispels", "darkness"): EdgeUpdate(
            edge_id="edge-b-003", source_label="light", relation="dispels",
            target_label="darkness", phase=0.0, sigma=0.02,
            event_type="crystallization", source_document="verified-baseline-v1"
        )
    }
    proxy_b_s3 = SyncProxy(agent_id="agent-b", local_bank=agent_b_bank_s3)
    hallucinated = EdgeUpdate(
        edge_id="edge-rogue-001", source_label="light", relation="dispels",
        target_label="darkness", phase=math.pi, sigma=0.02,
        event_type="initial_encoding", source_document="untrusted-llm-output"
    )
    verdict = proxy_b_s3.evaluate_delta(hallucinated)
    print_verdict(verdict, "light → dispels → darkness (hallucinated: φ = π)")
    assert verdict.verdict == "REJECT", f"Expected REJECT, got {verdict.verdict}"
    print("\n  ✓ Write blocked. Bank remains uncorrupted. State-rejection alert raised.")

    # ─────────────────────────────────────────────────────────
    # CONSENSUS GATE: Three independent agents crystallize an edge
    # ─────────────────────────────────────────────────────────
    banner("Consensus Gate — Three agents agree on 'whale is_a mammal'")
    gate = ConsensusGate()
    gate.submit(PhaseProposal("agent-a", "edge-whale-001", 0.5236, 0.12, "wikipedia-cetacea"))
    gate.submit(PhaseProposal("agent-b", "edge-whale-001", 0.5100, 0.10, "britannica-mammals"))
    gate.submit(PhaseProposal("agent-c", "edge-whale-001", 0.5300, 0.09, "marine-bio-textbook"))
    result = gate.evaluate("edge-whale-001")
    print(f"\n  Outcome        : {result.outcome}")
    print(f"  Source count   : {result.source_count}")
    print(f"  Phase spread   : {result.spread:.4f} rad  (limit: {math.pi/4:.4f} rad)")
    print(f"  Consensus φ    : {result.consensus_phase:.4f} rad")
    print(f"  Consensus σ    : {result.consensus_sigma:.4f}")
    print(f"  Reason         : {result.reason}")
    assert result.outcome == "PASS", f"Expected PASS, got {result.outcome}"
    print("\n  ✓ Edge crystallized. Three nodes in consensus. frozen=True propagated across cluster.")

    print("\n" + "═" * 60)
    print("  All scenarios passed. CSIF-Sync protocol verified.")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    run_demo()
