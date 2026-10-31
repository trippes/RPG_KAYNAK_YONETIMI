"""Deterministic location graph and neighbor-based path finding."""

from collections import deque

from .location import Location


class WorldMap:
    def __init__(self, world_id: str):
        if not isinstance(world_id, str) or not world_id.strip():
            raise ValueError("world_id must be a non-empty string.")
        self.world_id = world_id
        self._locations: dict[str, Location] = {}
        self._neighbors: dict[str, set[str]] = {}

    def add_location(self, location: Location) -> Location:
        if not isinstance(location, Location):
            raise TypeError("location must be Location.")
        if location.location_id in self._locations:
            raise ValueError(f"Duplicate location ID: {location.location_id}")
        self._locations[location.location_id] = location
        self._neighbors[location.location_id] = set()
        return location

    def get(self, location_id: str) -> Location | None:
        return self._locations.get(location_id)

    def locations(self) -> tuple[Location, ...]:
        return tuple(self._locations[key] for key in sorted(self._locations))

    def connect(self, first_id: str, second_id: str) -> None:
        self._require(first_id)
        self._require(second_id)
        if first_id == second_id:
            raise ValueError("A location cannot connect to itself.")
        self._neighbors[first_id].add(second_id)
        self._neighbors[second_id].add(first_id)

    def neighbors(self, location_id: str) -> tuple[Location, ...]:
        self._require(location_id)
        return tuple(self._locations[key] for key in sorted(self._neighbors[location_id]))

    def find_path(self, start_id: str, target_id: str) -> tuple[str, ...]:
        self._require(start_id)
        self._require(target_id)
        if start_id == target_id:
            return (start_id,)
        queue = deque([start_id])
        previous = {start_id: None}
        while queue:
            current = queue.popleft()
            for neighbor in sorted(self._neighbors[current]):
                if neighbor in previous:
                    continue
                previous[neighbor] = current
                if neighbor == target_id:
                    path = [target_id]
                    while path[-1] != start_id:
                        path.append(previous[path[-1]])
                    return tuple(reversed(path))
                queue.append(neighbor)
        raise ValueError(f"No route from {start_id} to {target_id}.")

    def _require(self, location_id: str) -> Location:
        location = self.get(location_id)
        if location is None:
            raise KeyError(f"Location not found: {location_id}")
        return location

