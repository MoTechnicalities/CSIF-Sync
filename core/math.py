"""
Phase geometry primitives for CSIF-Sync
Shared mathematical substrate with CSIF-Guard.
IEEE 754 double precision throughout — determinism guaranteed.
"""
import math

def wrap_pi(theta):
    """Wrap angle to principal interval [-pi, pi]."""
    return ((theta + math.pi) % (2 * math.pi)) - math.pi

def phase_distance(theta_a, theta_b):
    """Angular distance between two phase values. Always non-negative."""
    return abs(wrap_pi(theta_a - theta_b))

def normalized_resonance(theta_a, theta_b):
    """0.0 = perfect coherence, 1.0 = maximum opposition."""
    return phase_distance(theta_a, theta_b) / math.pi

def contradiction_threshold(sigma, c=0.5):
    """Adaptive contradiction detection threshold."""
    return math.pi / 2 + c * sigma

def circular_mean(phases):
    """Correct circular mean of a list of angles."""
    sin_sum = sum(math.sin(p) for p in phases)
    cos_sum = sum(math.cos(p) for p in phases)
    return math.atan2(sin_sum, cos_sum)

def compose_path_phase(phases):
    """Compose phase angles along a directed path."""
    return wrap_pi(sum(phases))

def nudge_phase(theta, error_signal, evidence_weight, alpha=0.1):
    """Apply one outcome-driven phase correction."""
    return wrap_pi(theta + alpha * error_signal * evidence_weight)

def tighten_sigma(sigma, evidence_weight, rate=0.1):
    """Tighten confidence band as evidence accumulates."""
    return sigma * (1.0 - evidence_weight * rate)
