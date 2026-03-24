"""Route finding with Dijkstra's algorithm"""

import heapq
from typing import Dict, List, Optional, Set, Tuple
from .graph import TopologyGraph
from .types import Route, RouteStep, ConflictWarning, RouteConflict


class RouteFinder:
    """Find valid routes through track network."""

    def __init__(self, graph: TopologyGraph):
        self.graph = graph

    def find_route(
        self,
        start_path: str,
        start_s: float,
        end_path: str,
        end_s: float,
        switch_states: Optional[Dict[str, str]] = None
    ) -> Optional[Route]:
        """Find shortest valid route between positions."""
        if start_path not in self.graph.paths or end_path not in self.graph.paths:
            return None

        if start_path == end_path:
            if start_s <= end_s:
                return Route(steps=[RouteStep(path_id=start_path, entry_s=start_s, exit_s=end_s)])
            return None

        initial_route = [RouteStep(path_id=start_path, entry_s=start_s, exit_s=0.0)]
        heap = [(0.0, start_path, initial_route, {})]
        visited: Set[str] = set()

        while heap:
            dist, current_path, route, switch_reqs = heapq.heappop(heap)

            if current_path in visited:
                continue
            visited.add(current_path)

            for next_path in self.graph.get_outgoing_paths(current_path):
                junction_id = self.graph.get_junction_for_edge(current_path, next_path)

                if junction_id and switch_states:
                    if switch_states.get(junction_id) != next_path:
                        continue

                current_node = self.graph.paths.get(current_path)
                next_node = self.graph.paths.get(next_path)

                if not current_node or not next_node:
                    continue

                updated_route = route[:-1] + [
                    RouteStep(path_id=current_path, entry_s=route[-1].entry_s, exit_s=current_node.length)
                ]

                if next_path == end_path:
                    updated_route.append(RouteStep(path_id=next_path, entry_s=0.0, exit_s=end_s))
                    new_switch_reqs = switch_reqs.copy()
                    if junction_id:
                        new_switch_reqs[junction_id] = next_path
                    return Route(steps=updated_route, switch_requirements=new_switch_reqs)

                updated_route.append(RouteStep(path_id=next_path, entry_s=0.0, exit_s=next_node.length))
                new_dist = dist + next_node.length
                new_switch_reqs = switch_reqs.copy()
                if junction_id:
                    new_switch_reqs[junction_id] = next_path
                heapq.heappush(heap, (new_dist, next_path, updated_route, new_switch_reqs))

        return None

    def find_all_routes(self, start_path: str, end_path: str, max_routes: int = 10) -> List[Route]:
        """Find all valid routes (up to max)."""
        if start_path not in self.graph.paths or end_path not in self.graph.paths:
            return []

        all_routes: List[Route] = []

        def dfs(current: str, visited: Set[str], route: List[RouteStep], switch_reqs: Dict[str, str]):
            if len(all_routes) >= max_routes:
                return
            if current == end_path:
                all_routes.append(Route(steps=route.copy(), switch_requirements=switch_reqs.copy()))
                return

            visited.add(current)
            for next_path in self.graph.get_outgoing_paths(current):
                if next_path in visited:
                    continue
                junction_id = self.graph.get_junction_for_edge(current, next_path)
                current_node = self.graph.paths.get(current)
                next_node = self.graph.paths.get(next_path)
                if not current_node or not next_node:
                    continue

                if len(route) == 0:
                    route.append(RouteStep(path_id=current, entry_s=0.0, exit_s=current_node.length))
                route.append(RouteStep(path_id=next_path, entry_s=0.0, exit_s=next_node.length))
                new_switch_reqs = switch_reqs.copy()
                if junction_id:
                    new_switch_reqs[junction_id] = next_path

                dfs(next_path, visited.copy(), route, new_switch_reqs)
                route.pop()

        dfs(start_path, set(), [], {})
        all_routes.sort(key=lambda r: r.total_length)
        return all_routes


def check_route_conflicts(
    routes: Dict[str, Route],
    train_positions: Dict[str, Tuple[str, float]]
) -> List[ConflictWarning]:
    """Check for route conflicts between trains."""
    warnings: List[ConflictWarning] = []
    train_ids = list(routes.keys())

    for i, train_a in enumerate(train_ids):
        for train_b in train_ids[i + 1:]:
            route_a = routes[train_a]
            route_b = routes[train_b]

            paths_a = set(route_a.get_path_sequence())
            paths_b = set(route_b.get_path_sequence())

            for path_id in paths_a.intersection(paths_b):
                pos_a = train_positions.get(train_a, (path_id, 0.0))
                pos_b = train_positions.get(train_b, (path_id, 0.0))

                if pos_a[0] == path_id and pos_b[0] == path_id:
                    separation = abs(pos_a[1] - pos_b[1])
                    if separation < 10.0:
                        warnings.append(ConflictWarning(
                            train_id=train_a,
                            conflicting_train_id=train_b,
                            path_id=path_id,
                            position_s=min(pos_a[1], pos_b[1]),
                            message=f"Trains within {separation:.1f}m on {path_id}"
                        ))

            for switch_id in set(route_a.switch_requirements.keys()).intersection(route_b.switch_requirements.keys()):
                if route_a.switch_requirements[switch_id] != route_b.switch_requirements[switch_id]:
                    warnings.append(ConflictWarning(
                        train_id=train_a,
                        conflicting_train_id=train_b,
                        path_id="",
                        position_s=0.0,
                        message=f"Switch {switch_id} conflict"
                    ))

    return warnings


def detect_route_conflicts(routes: Dict[str, Route]) -> List[RouteConflict]:
    """Detect hard conflicts (switch alignment)."""
    conflicts: List[RouteConflict] = []
    train_ids = list(routes.keys())

    for i, train_a in enumerate(train_ids):
        for train_b in train_ids[i + 1:]:
            shared_switches = set(routes[train_a].switch_requirements.keys()).intersection(
                routes[train_b].switch_requirements.keys()
            )
            for switch_id in shared_switches:
                if routes[train_a].switch_requirements[switch_id] != routes[train_b].switch_requirements[switch_id]:
                    conflicts.append(RouteConflict(
                        conflict_type="switch_conflict",
                        train_ids=[train_a, train_b],
                        path_id="",
                        details=f"Switch {switch_id} cannot be aligned to both paths"
                    ))

    return conflicts