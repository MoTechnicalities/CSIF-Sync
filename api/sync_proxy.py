"""
CSIF-Sync Phase Broadcast Proxy — api/sync_proxy.py

Lightweight UDP broadcast mechanism for local-network phase-geometry synchronization.
Agents on the same LAN exchange crystal deltas (edge_id, phase, sigma, timestamp)
as compact JSON payloads. No external dependencies; Python standard library only.

Architecture:
  SyncProxy.broadcast_delta()  — send a CrystalDelta to the local subnet
  SyncProxy.listen()           — blocking receive loop (run in a thread)
  SyncProxy.evaluate_delta()   — resonance-check an incoming delta in-process

Delta verdict codes:
  SKIP      — resonance near 0.0; knowledge is identical, no action needed
  NUDGE     — slight phase drift detected; apply deterministic phase nudge
  REJECT    — multi-path conflict residual near pi; state rejected, alert raised
"""
import json
import math
import socket
import threading
from datetime import datetime
from core.math import normalized_resonance, nudge_phase, contradiction_threshold

# Default UDP broadcast port for CSIF-Sync nodes on a local network.
DEFAULT_PORT = 52833
DEFAULT_BROADCAST = "255.255.255.255"

# Resonance thresholds
SKIP_THRESHOLD = 0.05      # normalized_resonance < 0.05 → identical, skip
NUDGE_THRESHOLD = 0.5      # normalized_resonance < 0.5  → minor drift, nudge
# Above NUDGE_THRESHOLD and exceeding contradiction_threshold → reject


class CrystalDelta:
    """
    Minimal wire payload exchanged between CSIF-Sync agents.
    Contains a list of EdgeUpdate entries — each is one edge's current phase state.
    """
    def __init__(self, agent_id, crystal_id, crystal_label, lobe, edge_updates, timestamp=None):
        self.agent_id = agent_id
        self.crystal_id = crystal_id
        self.crystal_label = crystal_label
        self.lobe = lobe
        self.edge_updates = edge_updates  # list[EdgeUpdate]
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "crystal_id": self.crystal_id,
            "crystal_label": self.crystal_label,
            "lobe": self.lobe,
            "edge_updates": [e.to_dict() for e in self.edge_updates],
            "timestamp": self.timestamp,
        }

    def to_bytes(self):
        return json.dumps(self.to_dict()).encode("utf-8")

    @staticmethod
    def from_bytes(data: bytes):
        d = json.loads(data.decode("utf-8"))
        updates = [EdgeUpdate.from_dict(u) for u in d["edge_updates"]]
        return CrystalDelta(
            d["agent_id"], d["crystal_id"], d["crystal_label"],
            d["lobe"], updates, d["timestamp"]
        )


class EdgeUpdate:
    """Wire representation of one edge's current phase state."""
    def __init__(self, edge_id, source_label, relation, target_label,
                 phase, sigma, event_type, source_document):
        self.edge_id = edge_id
        self.source_label = source_label
        self.relation = relation
        self.target_label = target_label
        self.phase = phase
        self.sigma = sigma
        self.event_type = event_type
        self.source_document = source_document

    def to_dict(self):
        return {
            "edge_id": self.edge_id,
            "source_label": self.source_label,
            "relation": self.relation,
            "target_label": self.target_label,
            "phase": self.phase,
            "sigma": self.sigma,
            "event_type": self.event_type,
            "source_document": self.source_document,
        }

    @staticmethod
    def from_dict(d):
        return EdgeUpdate(
            d["edge_id"], d["source_label"], d["relation"], d["target_label"],
            d["phase"], d["sigma"], d["event_type"], d["source_document"]
        )


class DeltaVerdict:
    """Result of evaluating an incoming CrystalDelta against local knowledge."""
    SKIP = "SKIP"
    NUDGE = "NUDGE"
    REJECT = "REJECT"

    def __init__(self, verdict, edge_id, incoming_phase, local_phase,
                 resonance, nudged_phase=None, reason=""):
        self.verdict = verdict
        self.edge_id = edge_id
        self.incoming_phase = incoming_phase
        self.local_phase = local_phase
        self.resonance = resonance
        self.nudged_phase = nudged_phase
        self.reason = reason

    def to_dict(self):
        return {
            "verdict": self.verdict,
            "edge_id": self.edge_id,
            "incoming_phase": self.incoming_phase,
            "local_phase": self.local_phase,
            "resonance": self.resonance,
            "nudged_phase": self.nudged_phase,
            "reason": self.reason,
        }

    def __repr__(self):
        return (f"DeltaVerdict({self.verdict}, edge={self.edge_id}, "
                f"R_N={self.resonance:.4f})")


class SyncProxy:
    """
    UDP broadcast proxy for CSIF-Sync phase-geometry synchronization.

    Broadcast a CrystalDelta to all agents on the local subnet, or receive
    incoming deltas and evaluate them against the local crystal bank.

    Network-free simulation:
        Use evaluate_delta() directly without calling broadcast() or listen()
        to run the full resonance logic in-process, as demonstrated in demo_sync.py.
    """

    def __init__(self, agent_id, local_bank=None,
                 port=DEFAULT_PORT, broadcast_addr=DEFAULT_BROADCAST):
        self.agent_id = agent_id
        self.local_bank = local_bank        # dict[edge_key -> EdgeUpdate]
        self.port = port
        self.broadcast_addr = broadcast_addr
        self._sock = None
        self._running = False
        self._on_verdict = None             # optional callback(DeltaVerdict)

    # ------------------------------------------------------------------
    # Network operations (real UDP; use in production)
    # ------------------------------------------------------------------

    def broadcast_delta(self, delta: CrystalDelta):
        """Broadcast a CrystalDelta to all agents on the local subnet via UDP."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            payload = delta.to_bytes()
            sock.sendto(payload, (self.broadcast_addr, self.port))

    def listen(self, on_verdict=None, buffer_size=65535):
        """
        Blocking UDP receive loop. Run this in a daemon thread.

        on_verdict: optional callable(DeltaVerdict) invoked for each incoming delta.
        """
        self._on_verdict = on_verdict
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("", self.port))
        while self._running:
            try:
                data, addr = self._sock.recvfrom(buffer_size)
                delta = CrystalDelta.from_bytes(data)
                if delta.agent_id == self.agent_id:
                    continue  # ignore own broadcasts
                for update in delta.edge_updates:
                    verdict = self.evaluate_delta(update)
                    if self._on_verdict:
                        self._on_verdict(verdict)
            except OSError:
                break

    def stop(self):
        self._running = False
        if self._sock:
            self._sock.close()

    # ------------------------------------------------------------------
    # Resonance evaluation (pure geometry; no network required)
    # ------------------------------------------------------------------

    def evaluate_delta(self, update: EdgeUpdate) -> DeltaVerdict:
        """
        Evaluate one incoming EdgeUpdate against the local bank.

        Returns a DeltaVerdict with one of three outcomes:
          SKIP   — resonance < SKIP_THRESHOLD; knowledge identical
          NUDGE  — slight drift; deterministic phase nudge applied
          REJECT — geometric contradiction; write blocked
        """
        edge_key = (update.source_label, update.relation, update.target_label)
        local = self.local_bank.get(edge_key) if self.local_bank else None

        if local is None:
            # No local knowledge; accept the incoming phase as new fact.
            if self.local_bank is not None:
                self.local_bank[edge_key] = update
            return DeltaVerdict(
                DeltaVerdict.NUDGE, update.edge_id,
                update.phase, None, 0.0,
                nudged_phase=update.phase,
                reason="No local knowledge for this edge; accepted as new fact."
            )

        R_N = normalized_resonance(local.phase, update.phase)
        sigma = max(local.sigma, update.sigma)
        threshold = contradiction_threshold(sigma)

        if R_N < SKIP_THRESHOLD:
            return DeltaVerdict(
                DeltaVerdict.SKIP, update.edge_id,
                update.phase, local.phase, R_N,
                reason="Knowledge identical; update silently skipped."
            )

        phase_diff = abs(local.phase - update.phase)
        if phase_diff > threshold:
            return DeltaVerdict(
                DeltaVerdict.REJECT, update.edge_id,
                update.phase, local.phase, R_N,
                reason=(f"Geometric contradiction: residual {phase_diff:.4f} rad "
                        f"exceeds threshold {threshold:.4f} rad. Write blocked.")
            )

        # Apply a deterministic nudge to align toward the incoming phase.
        error_signal = update.phase - local.phase
        nudged = nudge_phase(local.phase, error_signal, 1.0 - update.sigma / math.pi)
        local.phase = nudged
        return DeltaVerdict(
            DeltaVerdict.NUDGE, update.edge_id,
            update.phase, local.phase, R_N,
            nudged_phase=nudged,
            reason=f"Phase drift {R_N:.4f}; deterministic nudge applied → {nudged:.4f} rad."
        )
