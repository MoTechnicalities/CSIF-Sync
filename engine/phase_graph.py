"""
PhaseGraph construction and multi-path conflict detection for CSIF-Sync.
Direction-aware: reverse traversal contributes wrap_pi(-phase).
"""
from core.math import wrap_pi, phase_distance, compose_path_phase


class PhaseEdge:
    def __init__(self, source, target, phase, sigma, edge_id):
        self.source = source
        self.target = target
        self.phase = phase
        self.sigma = sigma
        self.edge_id = edge_id


class PhaseGraph:
    def __init__(self):
        self.nodes = set()
        self.edges = []

    def add_edge(self, source, target, phase, sigma, edge_id):
        self.nodes.add(source)
        self.nodes.add(target)
        self.edges.append(PhaseEdge(source, target, phase, sigma, edge_id))

    def find_edges(self, source, target):
        return [e for e in self.edges if e.source == source and e.target == target]


def build_phase_graph(crystal):
    graph = PhaseGraph()
    for edge in crystal.edges.values():
        src = crystal.nodes[edge.source_node].label
        tgt = crystal.nodes[edge.target_node].label
        graph.add_edge(src, tgt, edge.current_phase, edge.current_sigma, edge.edge_id)
    return graph


def build_merged_phase_graph(crystal_a, crystal_b):
    ga = build_phase_graph(crystal_a)
    gb = build_phase_graph(crystal_b)
    shared = ga.nodes & gb.nodes
    merged = PhaseGraph()
    merged.nodes = ga.nodes | gb.nodes
    merged.edges = ga.edges + gb.edges
    for label in shared:
        merged.add_edge(label, label, 0.0, 0.0, None)
    return merged, shared


def all_simple_paths(graph, source, target, max_depth=10):
    paths = []
    stack = [(source, [source], [])]
    while stack:
        current, node_path, step_path = stack.pop()
        if current == target and len(node_path) > 1:
            paths.append({"nodes": node_path, "steps": step_path})
        if len(node_path) >= max_depth:
            continue
        for e in graph.edges:
            next_node = direction = None
            if e.source == current:
                next_node, direction = e.target, 1
            elif e.target == current:
                next_node, direction = e.source, -1
            if next_node is not None and next_node not in node_path:
                stack.append((next_node, node_path + [next_node], step_path + [(e, direction)]))
    return paths


def path_phase(path_record):
    return compose_path_phase([
        e.phase if d == 1 else wrap_pi(-e.phase)
        for e, d in path_record["steps"]
    ])


class ConflictPathTrace:
    def __init__(self, source, target, path_a, path_b, phase_a, phase_b, residual):
        self.source = source
        self.target = target
        self.path_a = path_a
        self.path_b = path_b
        self.phase_a = phase_a
        self.phase_b = phase_b
        self.residual = residual

    def to_dict(self):
        return {"source": self.source, "target": self.target,
                "path_a": self.path_a, "path_b": self.path_b,
                "phase_a": self.phase_a, "phase_b": self.phase_b,
                "residual": self.residual}


def pairwise_conflict(graph, source, target):
    paths = all_simple_paths(graph, source, target)
    if len(paths) < 2:
        return 0.0, []
    max_residual = 0.0
    traces = []
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            pa, pb = path_phase(paths[i]), path_phase(paths[j])
            residual = phase_distance(pa, pb)
            traces.append(ConflictPathTrace(
                source, target, paths[i]["nodes"], paths[j]["nodes"], pa, pb, residual))
            if residual > max_residual:
                max_residual = residual
    return max_residual, traces


def max_multipath_phase_conflict(graph):
    global_max, all_traces = 0.0, []
    nodes = list(graph.nodes)
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i == j:
                continue
            score, traces = pairwise_conflict(graph, nodes[i], nodes[j])
            all_traces.extend(traces)
            if score > global_max:
                global_max = score
    return global_max, all_traces


def compute_resonance(crystal_a, crystal_b):
    """Edge-aligned resonance score between two crystals."""
    index_a = {
        (crystal_a.nodes[e.source_node].label, e.relation, crystal_a.nodes[e.target_node].label): e
        for e in crystal_a.edges.values()
    }
    aligned = []
    for e_b in crystal_b.edges.values():
        key = (crystal_b.nodes[e_b.source_node].label, e_b.relation,
               crystal_b.nodes[e_b.target_node].label)
        if key in index_a:
            aligned.append((index_a[key], e_b))

    if not aligned:
        return {"normalized_resonance": 1.0, "status": "divergent",
                "edge_count": 0, "phase_conflict_score": 0.0, "traces": []}

    import math
    raw = sum(phase_distance(ea.current_phase, eb.current_phase) for ea, eb in aligned)
    normalized = raw / (len(aligned) * math.pi)

    merged, _ = build_merged_phase_graph(crystal_a, crystal_b)
    conflict_score, traces = max_multipath_phase_conflict(merged)
    mean_sigma = sum(e.current_sigma for ea, eb in aligned for e in [ea, eb]) / (2 * len(aligned))

    from core.math import contradiction_threshold
    threshold = contradiction_threshold(mean_sigma)
    if conflict_score >= threshold:
        status = "contradictory"
    elif conflict_score >= threshold * 0.1:
        status = "divergent"
    else:
        status = "coherent"

    return {
        "normalized_resonance": normalized,
        "status": status,
        "edge_count": len(aligned),
        "phase_conflict_score": conflict_score,
        "traces": [t.to_dict() for t in traces[:5]],
    }
