from dataclasses import dataclass
from random import Random

import numpy as np


EMPTY = 0
WALL = 1
ENERGY = 2
FIRST_AGENT_ID = 100


@dataclass(frozen=True)
class Position:
    x: int
    y: int


@dataclass
class AgentState:
    agent_id: int
    position: Position
    energy: int = 0
    facing: str = "up"


@dataclass(frozen=True)
class AgentAction:
    agent_id: int
    action: str
    direction: str | None = None


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str
    agent_state: AgentState
    vision: list["VisionCell"]


@dataclass(frozen=True)
class VisionCell:
    x: int
    y: int
    dx: int
    dy: int
    value: int


class World:
    """A simple 2D grid world containing walls and energy deposits."""

    def __init__(
        self,
        width: int = 100,
        height: int = 100,
        wall_count: int = 250,
        energy_count: int = 100,
        seed: int | None = None,
        border_walls: bool = True,
        wall_seed_chance: float = 0.35,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("World dimensions must be positive.")

        self.width = width
        self.height = height
        self.random = Random(seed)
        self.grid = np.full((height, width), EMPTY, dtype=np.int32)
        self.agents: dict[int, AgentState] = {}
        self.next_agent_id = FIRST_AGENT_ID

        if border_walls:
            self._add_border_walls()

        self.add_random_walls(wall_count, seed_chance=wall_seed_chance)
        self.add_random_energy(energy_count)

    def _add_border_walls(self) -> None:
        self.grid[0, :] = WALL
        self.grid[-1, :] = WALL
        self.grid[:, 0] = WALL
        self.grid[:, -1] = WALL

    def add_wall(self, x: int, y: int) -> None:
        self._validate_position(x, y)
        if self._is_agent_id(self.grid[y, x]):
            raise ValueError("Cannot place a wall on an agent.")
        self.grid[y, x] = WALL

    def add_energy(self, x: int, y: int) -> None:
        self._validate_position(x, y)
        if self.grid[y, x] == WALL:
            raise ValueError("Cannot place energy on a wall.")
        if self._is_agent_id(self.grid[y, x]):
            raise ValueError("Cannot place energy on an agent.")
        self.grid[y, x] = ENERGY

    def add_agent(self, x: int | None = None, y: int | None = None) -> AgentState:
        if x is None or y is None:
            if x is not None or y is not None:
                raise ValueError("Both x and y are required when placing an agent manually.")

            position = self._random_empty_positions(1)[0]
        else:
            self._validate_position(x, y)
            position = Position(x=x, y=y)
            if self.grid[y, x] != EMPTY:
                raise ValueError("Agents can only be placed on empty cells.")

        agent_id = self.next_agent_id
        self.next_agent_id += 1

        agent_state = AgentState(agent_id=agent_id, position=position)
        self.agents[agent_id] = agent_state
        self.grid[position.y, position.x] = agent_id
        return agent_state

    def add_random_agents(self, count: int) -> list[AgentState]:
        if count < 0:
            raise ValueError("Count cannot be negative.")

        return [self.add_agent() for _ in range(count)]

    def apply_agent_action(self, request: AgentAction | dict) -> ActionResult:
        action = self._parse_agent_action(request)
        agent_state = self._get_agent_state(action.agent_id)

        if action.action == "move":
            return self._move_agent(agent_state, action.direction)

        raise ValueError(f"Unknown agent action: {action.action}")

    def add_random_walls(self, count: int, seed_chance: float = 0.35) -> None:
        self.add_connected_walls(count, seed_chance=seed_chance)

    def add_connected_walls(
        self,
        count: int,
        min_segment_length: int = 4,
        max_segment_length: int = 14,
        turn_chance: float = 0.25,
        seed_chance: float = 0.35,
    ) -> None:
        """Grow connected wall segments instead of placing isolated wall dots."""
        if count < 0:
            raise ValueError("Count cannot be negative.")
        if min_segment_length <= 0 or max_segment_length < min_segment_length:
            raise ValueError("Wall segment lengths must be positive and ordered.")
        if not 0 <= turn_chance <= 1:
            raise ValueError("Turn chance must be between 0 and 1.")
        if not 0 <= seed_chance <= 1:
            raise ValueError("Seed chance must be between 0 and 1.")

        empty_cells = np.argwhere(self.grid == EMPTY)
        if count > len(empty_cells):
            raise ValueError("Not enough empty cells available.")

        placed = 0
        attempts = 0
        max_attempts = max(count * 20, 100)
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while placed < count and attempts < max_attempts:
            attempts += 1
            start_new_cluster = placed == 0 or self.random.random() < seed_chance
            current = self._wall_growth_start(start_new_cluster=start_new_cluster)
            if current is None:
                break

            dx, dy = self.random.choice(directions)
            segment_length = self.random.randint(min_segment_length, max_segment_length)

            for _ in range(segment_length):
                if placed >= count:
                    break
                if self.grid[current.y, current.x] != EMPTY:
                    break

                self.grid[current.y, current.x] = WALL
                placed += 1

                if self.random.random() < turn_chance:
                    dx, dy = self.random.choice(directions)

                next_position = self._next_wall_position(current, dx, dy)
                if next_position is None:
                    break
                current = next_position

        if placed < count:
            raise ValueError("Could not place all connected walls.")

    def add_random_energy(self, count: int) -> None:
        for position in self._random_empty_positions(count):
            self.grid[position.y, position.x] = ENERGY

    def is_wall(self, x: int, y: int) -> bool:
        self._validate_position(x, y)
        return self.grid[y, x] == WALL

    def has_energy(self, x: int, y: int) -> bool:
        self._validate_position(x, y)
        return self.grid[y, x] == ENERGY

    def collect_energy(self, x: int, y: int) -> bool:
        self._validate_position(x, y)
        if self.grid[y, x] != ENERGY:
            return False

        self.grid[y, x] = EMPTY
        return True

    def visualize(self, show: bool = True, ax=None):
        """Draw the world grid with matplotlib and return the figure and axes."""
        if not show and ax is None:
            import matplotlib

            matplotlib.use("Agg", force=True)

        import matplotlib.pyplot as plt
        from matplotlib.colors import BoundaryNorm, ListedColormap
        from matplotlib.patches import Patch

        if ax is None:
            figure, ax = plt.subplots()
        else:
            figure = ax.figure

        display_grid = self.grid.copy()
        display_grid[display_grid >= FIRST_AGENT_ID] = 3

        cmap = ListedColormap(["white", "black", "limegreen", "dodgerblue"])
        norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)

        ax.imshow(display_grid, cmap=cmap, norm=norm, origin="upper")
        ax.set_title("World")
        ax.set_aspect("equal")
        ax.set_xticks(np.arange(-0.5, self.width, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, self.height, 1), minor=True)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(which="minor", color="lightgray", linewidth=0.5)
        ax.tick_params(which="minor", bottom=False, left=False)

        legend_items = [
            Patch(facecolor="white", edgecolor="black", label="Empty"),
            Patch(facecolor="black", edgecolor="black", label="Wall"),
            Patch(facecolor="limegreen", edgecolor="black", label="Energy"),
            Patch(facecolor="dodgerblue", edgecolor="black", label="Agent"),
        ]
        ax.legend(handles=legend_items, loc="upper right", bbox_to_anchor=(1.25, 1.0))

        for agent in self.agents.values():
            ax.text(
                agent.position.x,
                agent.position.y,
                str(agent.agent_id),
                color="white",
                ha="center",
                va="center",
                fontsize=7,
            )

        if show:
            plt.show()

        return figure, ax

    def _parse_agent_action(self, request: AgentAction | dict) -> AgentAction:
        if isinstance(request, AgentAction):
            return request

        try:
            return AgentAction(
                agent_id=int(request["agent_id"]),
                action=str(request["action"]).lower(),
                direction=request.get("direction"),
            )
        except KeyError as exc:
            raise ValueError(f"Agent action request missing {exc.args[0]}.") from exc

    def _get_agent_state(self, agent_id: int) -> AgentState:
        try:
            return self.agents[agent_id]
        except KeyError as exc:
            raise ValueError(f"Unknown agent id: {agent_id}") from exc

    def _move_agent(self, agent_state: AgentState, direction: str | None) -> ActionResult:
        dx, dy = self._direction_delta(direction)
        agent_state.facing = direction.lower()
        target = Position(agent_state.position.x + dx, agent_state.position.y + dy)

        if not self._is_inside(target):
            return self._action_result(False, "Move blocked by world boundary.", agent_state)

        target_value = self.grid[target.y, target.x]
        if target_value == WALL:
            return self._action_result(False, "Move blocked by wall.", agent_state)
        if self._is_agent_id(target_value):
            return self._action_result(False, "Move blocked by another agent.", agent_state)

        collected_energy = target_value == ENERGY
        self.grid[agent_state.position.y, agent_state.position.x] = EMPTY
        self.grid[target.y, target.x] = agent_state.agent_id
        agent_state.position = target

        if collected_energy:
            agent_state.energy += 1
            return self._action_result(True, "Moved and collected energy.", agent_state)

        return self._action_result(True, "Moved.", agent_state)

    def _action_result(
        self,
        success: bool,
        message: str,
        agent_state: AgentState,
    ) -> ActionResult:
        return ActionResult(
            success=success,
            message=message,
            agent_state=agent_state,
            vision=self.agent_vision(agent_state.agent_id),
        )

    def agent_vision(self, agent_id: int, radius: int = 5) -> list[VisionCell]:
        if radius <= 0:
            raise ValueError("Vision radius must be a positive number.")

        agent_state = self._get_agent_state(agent_id)
        facing_dx, facing_dy = self._direction_delta(agent_state.facing)
        visible_cells = []

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                if dx * dx + dy * dy > radius * radius:
                    continue
                if dx * facing_dx + dy * facing_dy <= 0:
                    continue

                position = Position(
                    x=agent_state.position.x + dx,
                    y=agent_state.position.y + dy,
                )
                if not self._is_inside(position):
                    continue

                visible_cells.append(
                    VisionCell(
                        x=position.x,
                        y=position.y,
                        dx=dx,
                        dy=dy,
                        value=int(self.grid[position.y, position.x]),
                    )
                )

        return visible_cells

    def _direction_delta(self, direction: str | None) -> tuple[int, int]:
        if direction is None:
            raise ValueError("Direction is required for this action.")

        directions = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }
        try:
            return directions[direction.lower()]
        except KeyError as exc:
            raise ValueError(f"Unknown direction: {direction}") from exc

    def _random_empty_positions(self, count: int) -> list[Position]:
        if count < 0:
            raise ValueError("Count cannot be negative.")

        empty_cells = np.argwhere(self.grid == EMPTY)
        if count > len(empty_cells):
            raise ValueError("Not enough empty cells available.")

        choices = self.random.sample(range(len(empty_cells)), count)
        return [Position(x=int(empty_cells[i][1]), y=int(empty_cells[i][0])) for i in choices]

    def _wall_growth_start(self, start_new_cluster: bool) -> Position | None:
        if start_new_cluster:
            return self._random_interior_empty_position()

        wall_cells = self._interior_wall_positions()
        self.random.shuffle(wall_cells)

        for position in wall_cells:
            neighbors = self._empty_neighbors(position)
            if neighbors:
                return self.random.choice(neighbors)

        return self._random_interior_empty_position()

    def _interior_wall_positions(self) -> list[Position]:
        wall_cells = np.argwhere(self.grid == WALL)
        return [
            Position(x=int(x), y=int(y))
            for y, x in wall_cells
            if not self._is_border_position(int(x), int(y))
        ]

    def _random_interior_empty_position(self) -> Position | None:
        interior_empty_cells = [
            Position(x=int(x), y=int(y))
            for y, x in np.argwhere(self.grid == EMPTY)
            if not self._is_border_position(int(x), int(y))
        ]
        if interior_empty_cells:
            return self.random.choice(interior_empty_cells)

        empty_cells = np.argwhere(self.grid == EMPTY)
        if len(empty_cells) == 0:
            return None

        y, x = self.random.choice(empty_cells)
        return Position(x=int(x), y=int(y))

    def _is_border_position(self, x: int, y: int) -> bool:
        return x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1

    def _next_wall_position(self, current: Position, dx: int, dy: int) -> Position | None:
        next_position = Position(x=current.x + dx, y=current.y + dy)
        if self._is_empty(next_position):
            return next_position

        neighbors = self._empty_neighbors(current)
        if not neighbors:
            return None

        return self.random.choice(neighbors)

    def _empty_neighbors(self, position: Position) -> list[Position]:
        neighbors = [
            Position(position.x + 1, position.y),
            Position(position.x - 1, position.y),
            Position(position.x, position.y + 1),
            Position(position.x, position.y - 1),
        ]
        return [neighbor for neighbor in neighbors if self._is_empty(neighbor)]

    def _is_empty(self, position: Position) -> bool:
        return (
            self._is_inside(position)
            and self.grid[position.y, position.x] == EMPTY
        )

    def _is_inside(self, position: Position) -> bool:
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    def _is_agent_id(self, value: int) -> bool:
        return value >= FIRST_AGENT_ID

    def _validate_position(self, x: int, y: int) -> None:
        if not 0 <= x < self.width or not 0 <= y < self.height:
            raise ValueError(f"Position ({x}, {y}) is outside the world.")


if __name__ == "__main__":
    world = World(seed=42)
    world.visualize()
