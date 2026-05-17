"""
CSIF-Sync Consensus Gate — engine/consensus_gate.py

Implements the multi-agent consensus protocol from CSIF Engine Specification V1, Section 8.
When three or more independent agents report a phase value for the same edge within a tight
spread (< pi/4), the edge is crystallized and propagated as frozen across the local cluster.

Gate outcomes:
  PASS      — three+ independent sources agree; edge crystallized
  DEFERRED  — fewer than three independent sources; proposal queued
  CONTESTED — sources present but disagree beyond spread tolerance; route to adjudication
"""
import math
from datetime import datetime
from core.math import circular_mean, wrap_pi

# Maximum allowed spread across source proposals to pass the gate.
CONSENSUS_SPREAD_LIMIT = math.pi / 4

# Minimum independent sources required to crystallize.
MIN_SOURCES = 3


class PhaseProposal:
    """A single agent's phase proposal for one edge."""
    def __init__(self, agent_id, edge_id, proposed_phase, proposed_sigma,
                 source_document, timestamp=None):
        self.agent_id = agent_id
        self.edge_id = edge_id
        self.proposed_phase = proposed_phase
        self.proposed_sigma = proposed_sigma
        self.source_document = source_document
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "edge_id": self.edge_id,
            "proposed_phase": self.proposed_phase,
            "proposed_sigma": self.proposed_sigma,
            "source_document": self.source_document,
            "timestamp": self.timestamp,
        }


class GateResult:
    """Outcome of a consensus gate evaluation."""
    PASS = "PASS"
    DEFERRED = "DEFERRED"
    CONTESTED = "CONTESTED"

    def __init__(self, outcome, edge_id, consensus_phase=None, consensus_sigma=None,
                 spread=None, source_count=None, reason=None):
        self.outcome = outcome
        self.edge_id = edge_id
        self.consensus_phase = consensus_phase
        self.consensus_sigma = consensus_sigma
        self.spread = spread
        self.source_count = source_count
        self.reason = reason

    def to_dict(self):
        return {
            "outcome": self.outcome,
            "edge_id": self.edge_id,
            "consensus_phase": self.consensus_phase,
            "consensus_sigma": self.consensus_sigma,
            "spread": self.spread,
            "source_count": self.source_count,
            "reason": self.reason,
        }

    def __repr__(self):
        return f"GateResult({self.outcome}, edge={self.edge_id}, spread={self.spread:.4f if self.spread is not None else None})"


class ConsensusGate:
    """
    Manages incoming phase proposals from multiple agents and evaluates
    crystallization readiness per edge.

    Usage:
        gate = ConsensusGate()
        gate.submit(proposal)
        result = gate.evaluate(edge_id)
    """

    def __init__(self):
        # dict[edge_id -> list[PhaseProposal]]
        self._proposals: dict = {}

    def submit(self, proposal: PhaseProposal):
        """Accept a phase proposal from one agent for one edge."""
        self._proposals.setdefault(proposal.edge_id, []).append(proposal)

    def evaluate(self, edge_id: str) -> GateResult:
        """
        Evaluate consensus readiness for a given edge.

        Returns a GateResult with outcome PASS, DEFERRED, or CONTESTED.
        """
        proposals = self._proposals.get(edge_id, [])

        # Require independent sources: no two proposals may share the same source_document.
        seen_docs = set()
        independent = []
        for p in proposals:
            if p.source_document not in seen_docs:
                seen_docs.add(p.source_document)
                independent.append(p)

        if len(independent) < MIN_SOURCES:
            return GateResult(
                GateResult.DEFERRED, edge_id,
                source_count=len(independent),
                spread=None,
                reason=f"Only {len(independent)} independent source(s); need {MIN_SOURCES}.",
            )

        phases = [p.proposed_phase for p in independent]
        spread = max(phases) - min(phases)

        if spread > CONSENSUS_SPREAD_LIMIT:
            return GateResult(
                GateResult.CONTESTED, edge_id,
                source_count=len(independent),
                spread=spread,
                reason=f"Phase spread {spread:.4f} rad exceeds limit {CONSENSUS_SPREAD_LIMIT:.4f} rad.",
            )

        consensus_phase = circular_mean(phases)
        consensus_sigma = min(p.proposed_sigma for p in independent) * 0.5  # tighten on consensus
        return GateResult(
            GateResult.PASS, edge_id,
            consensus_phase=consensus_phase,
            consensus_sigma=consensus_sigma,
            spread=spread,
            source_count=len(independent),
            reason="Consensus reached; edge ready for crystallization.",
        )

    def evaluate_all(self) -> list:
        """Evaluate all pending edges and return list of GateResult."""
        return [self.evaluate(edge_id) for edge_id in self._proposals]

    def clear(self, edge_id: str):
        """Remove all proposals for an edge after crystallization."""
        self._proposals.pop(edge_id, None)

    def pending_edges(self) -> list:
        return list(self._proposals.keys())
