"""Topology graph representation"""

import networkx as nx
from typing import Dict, List, Optional
from app.models.track import Path
from app.models.topology import Junction


class PathNode:
    """Represents a node in the topology graph."""

    def __init__(self, path_id: str, length: float):
        self.path_id = path_id
        self.length = length
        self.incoming_junctions: List[str] = []
        self.outgoing_junctions: List[str] = []


class TopologyGraph:
    """Directed graph representation of track network."""

    def __init__(self):
        self._graph: nx.DiGraph = nx.DiGraph()
        self.paths: Dict[str, PathNode] = {}
        self.junctions: Dict[str, Junction] = {}

    def build(self, paths: List[Path], junctions: List[Junction]) -> None:
        """Build topology graph from paths and junctions."""
        self._graph.clear()
        self.paths.clear()
        self.junctions.clear()

        for path in paths:
            length = path.length_m if path.length_m is not None else 0.0
            node = PathNode(path_id=path.id, length=length)
            self.paths[path.id] = node
            self._graph.add_node(path.id)

        for junction in junctions:
            self.junctions[junction.id] = junction

            if junction.incoming_path_id not in self.paths:
                continue

            for outgoing_id in junction.outgoing_path_ids:
                if outgoing_id in self.paths:
                    self._graph.add_edge(
                        junction.incoming_path_id,
                        outgoing_id,
                        junction_id=junction.id
                    )
                    self.paths[junction.incoming_path_id].outgoing_junctions.append(junction.id)
                    self.paths[outgoing_id].incoming_junctions.append(junction.id)

    def get_outgoing_paths(self, path_id: str) -> List[str]:
        """Get list of paths reachable from this path."""
        return list(self._graph.successors(path_id))

    def get_incoming_paths(self, path_id: str) -> List[str]:
        """Get list of paths that can reach this path."""
        return list(self._graph.predecessors(path_id))

    def get_junction_for_edge(self, from_path: str, to_path: str) -> Optional[str]:
        """Get junction ID connecting two paths."""
        edge_data = self._graph.get_edge_data(from_path, to_path)
        return edge_data.get('junction_id') if edge_data else None

    def is_connected(self) -> bool:
        """Check if graph is weakly connected."""
        return nx.is_weakly_connected(self._graph) if self._graph.number_of_nodes() > 0 else True

    def get_orphan_paths(self) -> List[str]:
        """Get paths with no connections."""
        return [pid for pid, node in self.paths.items()
                if not node.incoming_junctions and not node.outgoing_junctions]

    def get_all_path_ids(self) -> List[str]:
        """Get all path IDs."""
        return list(self.paths.keys())

    def get_path_length(self, path_id: str) -> float:
        """Get path length."""
        return self.paths[path_id].length if path_id in self.paths else 0.0