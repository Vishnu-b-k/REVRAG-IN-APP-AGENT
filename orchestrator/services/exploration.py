"""Exploration state machine — stateful exploration controller.

Tracks discovered states, candidate/attempted/failed actions, manages
the frontier of unfinished states, and implements backtracking.

Phase V-2 of the execution plan.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ExplorationStatus(str, Enum):
    """Overall status of the exploration."""

    RUNNING = "running"
    COMPLETED = "completed"        # frontier empty, all states explored
    BUDGET_EXHAUSTED = "budget_exhausted"
    ERROR = "error"


@dataclass
class ActionRecord:
    """Record of one attempted action."""

    action_type: str
    target_element_id: Optional[str] = None
    value: Optional[str] = None
    succeeded: Optional[bool] = None
    failure_count: int = 0
    result_state_id: Optional[str] = None


@dataclass
class StateNode:
    """A single state in the exploration graph."""

    state_id: str
    screen_id: str
    parent_state_id: Optional[str] = None
    parent_action: Optional[dict[str, Any]] = None
    candidate_actions: list[dict[str, Any]] = field(default_factory=list)
    attempted_actions: dict[str, ActionRecord] = field(default_factory=dict)
    is_fully_explored: bool = False

    def action_key(self, action: dict[str, Any]) -> str:
        """Create a unique key for an action."""
        return f"{action.get('type', '')}:{action.get('target_element_id', '')}:{action.get('value', '')}"

    def get_unexplored_actions(self) -> list[dict[str, Any]]:
        """Return candidate actions that haven't been attempted."""
        unexplored = []
        for action in self.candidate_actions:
            key = self.action_key(action)
            if key not in self.attempted_actions:
                unexplored.append(action)
        return unexplored

    def get_non_failed_unexplored(self, max_failures: int = 2) -> list[dict[str, Any]]:
        """Return unexplored actions, excluding repeatedly failed ones."""
        result = []
        for action in self.candidate_actions:
            key = self.action_key(action)
            record = self.attempted_actions.get(key)
            if record is None:
                result.append(action)
            elif record.failure_count < max_failures and record.succeeded is None:
                # Attempted but no result yet — skip
                pass
        return result

    def mark_attempted(self, action: dict[str, Any]) -> ActionRecord:
        """Mark an action as attempted and return its record."""
        key = self.action_key(action)
        if key not in self.attempted_actions:
            self.attempted_actions[key] = ActionRecord(
                action_type=action.get("type", ""),
                target_element_id=action.get("target_element_id"),
                value=action.get("value"),
            )
        return self.attempted_actions[key]

    def mark_action_result(
        self, action: dict[str, Any], succeeded: bool, result_state_id: Optional[str] = None
    ) -> None:
        """Record the result of an action execution."""
        key = self.action_key(action)
        record = self.attempted_actions.get(key)
        if record is None:
            record = self.mark_attempted(action)
        record.succeeded = succeeded
        record.result_state_id = result_state_id
        if not succeeded:
            record.failure_count += 1

    def check_fully_explored(self) -> bool:
        """Update and return whether all candidate actions are exhausted."""
        if not self.candidate_actions:
            self.is_fully_explored = True
            return True
        unexplored = self.get_unexplored_actions()
        self.is_fully_explored = len(unexplored) == 0
        return self.is_fully_explored


class ExplorationController:
    """Stateful exploration controller implementing BFS/DFS with backtracking.

    Manages:
    - State graph (discovered states + transitions)
    - Frontier (states with unexplored actions)
    - Backtracking (return to nearest state with unexplored work)
    - Step budget enforcement
    - Failed action avoidance
    """

    def __init__(self, session_id: str, max_step_budget: int = 50, max_action_failures: int = 2):
        self.session_id = session_id
        self.max_step_budget = max_step_budget
        self.max_action_failures = max_action_failures

        # State graph
        self.states: dict[str, StateNode] = {}
        self.transitions: list[dict[str, Any]] = []

        # Exploration tracking
        self.current_state_id: Optional[str] = None
        self.step_count: int = 0
        self.status: ExplorationStatus = ExplorationStatus.RUNNING

        # Frontier — states with unexplored actions (stack = DFS)
        self._frontier: list[str] = []

        # History for backtracking path reconstruction
        self._state_history: list[str] = []

        # Event log
        self.events: list[dict[str, Any]] = []

    # ── Core API ─────────────────────────────────────────────────────

    def register_state(
        self,
        state_id: str,
        screen_id: str,
        candidate_actions: list[dict[str, Any]],
        parent_state_id: Optional[str] = None,
        parent_action: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, StateNode]:
        """Register a newly observed state. Returns (is_new, state_node)."""

        if state_id in self.states:
            # Already known — update current pointer but don't re-add
            existing = self.states[state_id]
            self.current_state_id = state_id
            return False, existing

        node = StateNode(
            state_id=state_id,
            screen_id=screen_id,
            parent_state_id=parent_state_id,
            parent_action=parent_action,
            candidate_actions=candidate_actions,
        )
        self.states[state_id] = node
        self.current_state_id = state_id
        self._state_history.append(state_id)

        # Add to frontier if there are unexplored actions
        if candidate_actions:
            self._add_to_frontier(state_id)

        # Record transition
        if parent_state_id and parent_action:
            self.transitions.append({
                "from": parent_state_id,
                "to": state_id,
                "action": parent_action,
                "step": self.step_count,
            })

        self._log_event("state_registered", {
            "state_id": state_id,
            "screen_id": screen_id,
            "candidate_actions": len(candidate_actions),
            "is_new": True,
        })

        return True, node

    def get_next_action(self) -> Optional[dict[str, Any]]:
        """Decide the next action to execute.

        Returns None when exploration should stop (completed or budget exhausted).

        Strategy:
        1. If current state has unexplored actions → pick the first one.
        2. If current state is exhausted → backtrack to nearest frontier state.
        3. If no frontier states remain → exploration complete.
        4. If step budget exhausted → stop.
        """

        # Check budget
        if self.step_count >= self.max_step_budget:
            self.status = ExplorationStatus.BUDGET_EXHAUSTED
            self._log_event("budget_exhausted", {"steps": self.step_count})
            return None

        # Check if we have a current state
        if self.current_state_id is None:
            self.status = ExplorationStatus.COMPLETED
            return None

        current = self.states.get(self.current_state_id)
        if current is None:
            self.status = ExplorationStatus.ERROR
            return None

        # Try unexplored actions on current state
        unexplored = current.get_non_failed_unexplored(self.max_action_failures)
        if unexplored:
            action = unexplored[0]
            current.mark_attempted(action)
            self.step_count += 1
            self._log_event("action_selected", {
                "state_id": self.current_state_id,
                "action": action,
                "step": self.step_count,
            })
            return action

        # Current state is exhausted — mark it and try backtracking
        current.check_fully_explored()
        self._remove_from_frontier(self.current_state_id)

        backtrack_action = self._backtrack()
        if backtrack_action is not None:
            self.step_count += 1
            return backtrack_action

        # No frontier left
        self.status = ExplorationStatus.COMPLETED
        self._log_event("exploration_completed", {
            "total_steps": self.step_count,
            "states_discovered": len(self.states),
            "transitions": len(self.transitions),
        })
        return None

    def report_action_result(
        self,
        action: dict[str, Any],
        succeeded: bool,
        new_state_id: Optional[str] = None,
    ) -> None:
        """Report the outcome of an executed action."""
        if self.current_state_id and self.current_state_id in self.states:
            node = self.states[self.current_state_id]
            node.mark_action_result(action, succeeded, new_state_id)

            if not succeeded:
                self._log_event("action_failed", {
                    "state_id": self.current_state_id,
                    "action": action,
                })

    # ── Backtracking ─────────────────────────────────────────────────

    def _backtrack(self) -> Optional[dict[str, Any]]:
        """Find the nearest frontier state and return a 'back' action to reach it.

        Uses the frontier stack to find states with unexplored work, then
        issues 'back' actions to navigate there.
        """

        while self._frontier:
            target_id = self._frontier[-1]
            target = self.states.get(target_id)

            if target is None or target.check_fully_explored():
                self._frontier.pop()
                continue

            # Found a state with work — issue backtrack
            self._log_event("backtrack", {
                "from": self.current_state_id,
                "to": target_id,
            })

            # Return a back action to navigate toward the target
            return {
                "type": "back",
                "reason": f"Backtracking to state {target_id} with unexplored actions",
                "confidence": 1.0,
                "_backtrack_target": target_id,
            }

        return None

    # ── Frontier management ──────────────────────────────────────────

    def _add_to_frontier(self, state_id: str) -> None:
        """Add a state to the frontier if not already present."""
        if state_id not in self._frontier:
            self._frontier.append(state_id)

    def _remove_from_frontier(self, state_id: str) -> None:
        """Remove a state from the frontier."""
        if state_id in self._frontier:
            self._frontier.remove(state_id)

    # ── Query methods ────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Return exploration statistics."""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "step_count": self.step_count,
            "states_discovered": len(self.states),
            "transitions": len(self.transitions),
            "frontier_size": len(self._frontier),
            "fully_explored_states": sum(
                1 for s in self.states.values() if s.is_fully_explored
            ),
        }

    def get_frontier_states(self) -> list[str]:
        """Return current frontier state IDs."""
        return list(self._frontier)

    def is_running(self) -> bool:
        """Check if exploration is still active."""
        return self.status == ExplorationStatus.RUNNING

    # ── Event log ────────────────────────────────────────────────────

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record an internal exploration event."""
        self.events.append({
            "type": event_type,
            "step": self.step_count,
            "data": data,
        })
        logger.debug("Exploration event [%s]: %s", event_type, data)
