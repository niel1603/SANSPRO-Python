
from typing import Tuple
from SANSPRO.object.node import Node


def node_key(n: Node, ndigits: int = 6) -> tuple[float, float, float]:
    return (round(n.x, ndigits), round(n.y, ndigits), round(n.z, ndigits))


def is_ccw(nodes: Tuple[Node, Node, Node, Node]) -> bool:
    """Return True if polygon is counter-clockwise."""
    area = 0.0
    for i in range(4):
        x1, y1 = nodes[i].x, nodes[i].y
        x2, y2 = nodes[(i + 1) % 4].x, nodes[(i + 1) % 4].y
        area += (x2 - x1) * (y2 + y1)
    return area < 0


def ensure_ccw(nodes: Tuple[Node, Node, Node, Node]):
    """Ensure CCW orientation."""
    return nodes if is_ccw(nodes) else (nodes[0], nodes[3], nodes[2], nodes[1])


def canonicalize_edges(nodes: Tuple[Node, Node, Node, Node]):
    """
    Stable, orientation-independent, rotation-independent normalization.

    - Ensure CCW
    - Rotate so the lexicographically smallest corner is index 0
    """
    nodes = ensure_ccw(nodes)
    keys = [node_key(n) for n in nodes]
    start = min(range(4), key=lambda i: keys[i])
    return tuple(nodes[(start + k) % 4] for k in range(4))
