"""Tests for the exploration state machine / controller.

Covers all required scenarios from V-2:
- Linear path
- Branching path
- Backtracking
- Repeated state (duplicate detection)
- Empty frontier
- Step budget termination
"""

import pytest

from orchestrator.services.exploration import (
    ExplorationController,
    ExplorationStatus,
    StateNode,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _make_actions(*names: str) -> list[dict]:
    """Create simple candidate action dicts for testing."""
    actions = []
    for name in names:
        parts = name.split(":")
        action_type = parts[0]
        target = parts[1] if len(parts) > 1 else f"el_{name}"
        actions.append({
            "type": action_type,
            "target_element_id": target,
            "value": None,
            "reason": f"Test action {name}",
            "confidence": 0.9,
        })
    return actions


# ── Test: Linear Path ────────────────────────────────────────────────

class TestLinearPath:
    """Exploration through a straight sequence of states with one action each."""

    def test_linear_three_states(self):
        """A → B → C → done."""
        ctrl = ExplorationController("session-linear", max_step_budget=20)

        # State A: one action leads to B
        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_next"))
        action = ctrl.get_next_action()
        assert action is not None
        assert action["type"] == "tap"
        ctrl.report_action_result(action, succeeded=True, new_state_id="B")

        # State B: one action leads to C
        ctrl.register_state("B", "scr_B", _make_actions("tap:btn_continue"),
                           parent_state_id="A", parent_action=action)
        action = ctrl.get_next_action()
        assert action is not None
        ctrl.report_action_result(action, succeeded=True, new_state_id="C")

        # State C: no actions (terminal)
        ctrl.register_state("C", "scr_C", [],
                           parent_state_id="B", parent_action=action)
        action = ctrl.get_next_action()
        # C has no actions, A and B are exhausted → done
        assert action is None
        assert ctrl.status == ExplorationStatus.COMPLETED

    def test_linear_records_transitions(self):
        """Transitions should be recorded between states."""
        ctrl = ExplorationController("session-transitions", max_step_budget=20)

        ctrl.register_state("A", "scr_A", _make_actions("tap:btn1"))
        action = ctrl.get_next_action()
        ctrl.report_action_result(action, succeeded=True, new_state_id="B")

        ctrl.register_state("B", "scr_B", [],
                           parent_state_id="A", parent_action=action)

        assert len(ctrl.transitions) == 1
        assert ctrl.transitions[0]["from"] == "A"
        assert ctrl.transitions[0]["to"] == "B"


# ── Test: Branching Path ─────────────────────────────────────────────

class TestBranchingPath:
    """State with multiple actions — each leading to a different branch."""

    def test_two_branches(self):
        """A has 2 actions → explores both branches."""
        ctrl = ExplorationController("session-branch", max_step_budget=20)

        # State A: two actions
        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_feed", "tap:btn_profile"))

        # First action: go to Feed
        action1 = ctrl.get_next_action()
        assert action1 is not None
        assert action1["target_element_id"] == "btn_feed"
        ctrl.report_action_result(action1, succeeded=True, new_state_id="Feed")

        # Register Feed as terminal
        ctrl.register_state("Feed", "scr_feed", [],
                           parent_state_id="A", parent_action=action1)

        # Next action — Feed is empty, should backtrack to A
        action2 = ctrl.get_next_action()
        assert action2 is not None
        # This should be either the second action on A or a backtrack action
        # After backtrack, we need to get the unexplored action
        if action2["type"] == "back":
            # Backtracked — now we're at A again, get the next unexplored
            ctrl.current_state_id = "A"
            action3 = ctrl.get_next_action()
            assert action3 is not None
            assert action3["target_element_id"] == "btn_profile"
        else:
            # Directly got the profile action (backtrack was implicit)
            assert action2["target_element_id"] == "btn_profile"

    def test_all_branches_explored(self):
        """After exploring all branches, controller should complete."""
        ctrl = ExplorationController("session-all-branches", max_step_budget=30)

        ctrl.register_state("root", "scr_root", _make_actions(
            "tap:btn_a", "tap:btn_b", "tap:btn_c"
        ))

        explored_targets = set()
        steps = 0
        max_steps = 20

        while steps < max_steps:
            action = ctrl.get_next_action()
            if action is None:
                break

            if action["type"] != "back":
                target = action.get("target_element_id", "")
                explored_targets.add(target)
                state_id = f"state_{target}"
                ctrl.report_action_result(action, succeeded=True, new_state_id=state_id)
                ctrl.register_state(state_id, f"scr_{target}", [],
                                   parent_state_id=ctrl.current_state_id,
                                   parent_action=action)
            else:
                # Backtrack — return to root
                ctrl.current_state_id = "root"

            steps += 1

        # All three branches should have been explored
        assert "btn_a" in explored_targets
        assert "btn_b" in explored_targets
        assert "btn_c" in explored_targets


# ── Test: Backtracking ───────────────────────────────────────────────

class TestBacktracking:
    """Verify backtracking returns to states with unexplored work."""

    def test_backtrack_after_dead_end(self):
        """A(2 actions) → B(0 actions) → backtrack → A's second action."""
        ctrl = ExplorationController("session-backtrack", max_step_budget=20)

        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1", "tap:btn_2"))

        # Take first action → B
        action1 = ctrl.get_next_action()
        assert action1["target_element_id"] == "btn_1"
        ctrl.report_action_result(action1, succeeded=True, new_state_id="B")
        ctrl.register_state("B", "scr_B", [], parent_state_id="A", parent_action=action1)

        # B is terminal — should trigger backtrack
        action2 = ctrl.get_next_action()
        assert action2 is not None
        assert action2["type"] == "back"
        assert "backtrack" in action2.get("reason", "").lower()

        # Simulate arriving back at A
        ctrl.current_state_id = "A"

        # Now should get A's second action
        action3 = ctrl.get_next_action()
        assert action3 is not None
        assert action3["target_element_id"] == "btn_2"

    def test_backtrack_event_logged(self):
        """A backtrack should produce an event in the log."""
        ctrl = ExplorationController("session-bt-event", max_step_budget=20)

        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1", "tap:btn_2"))
        action = ctrl.get_next_action()
        ctrl.report_action_result(action, succeeded=True, new_state_id="B")
        ctrl.register_state("B", "scr_B", [], parent_state_id="A", parent_action=action)

        ctrl.get_next_action()  # triggers backtrack

        backtrack_events = [e for e in ctrl.events if e["type"] == "backtrack"]
        assert len(backtrack_events) >= 1


# ── Test: Repeated State ─────────────────────────────────────────────

class TestRepeatedState:
    """Revisiting an already-known state should not duplicate it."""

    def test_duplicate_state_not_re_added(self):
        """Registering the same state_id twice returns is_new=False."""
        ctrl = ExplorationController("session-dup", max_step_budget=20)

        is_new_1, _ = ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1"))
        assert is_new_1 is True

        is_new_2, _ = ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1"))
        assert is_new_2 is False

        # Only one state in the graph
        assert len(ctrl.states) == 1

    def test_circular_navigation_terminates(self):
        """A → B → A (cycle) should not loop forever."""
        ctrl = ExplorationController("session-cycle", max_step_budget=10)

        ctrl.register_state("A", "scr_A", _make_actions("tap:go_b"))
        action1 = ctrl.get_next_action()
        ctrl.report_action_result(action1, succeeded=True, new_state_id="B")

        ctrl.register_state("B", "scr_B", _make_actions("tap:go_a"),
                           parent_state_id="A", parent_action=action1)
        action2 = ctrl.get_next_action()
        ctrl.report_action_result(action2, succeeded=True, new_state_id="A")

        # Re-register A — not new
        is_new, _ = ctrl.register_state("A", "scr_A", _make_actions("tap:go_b"))
        assert is_new is False

        # A's only action is already attempted, B's only action is already attempted
        # Should terminate
        steps = 0
        while steps < 15:
            action = ctrl.get_next_action()
            if action is None:
                break
            if action["type"] == "back":
                ctrl.current_state_id = "A"
            steps += 1

        # Must not run forever
        assert steps < 15
        assert not ctrl.is_running() or ctrl.step_count <= 10


# ── Test: Empty Frontier ─────────────────────────────────────────────

class TestEmptyFrontier:
    """Exploration with no candidate actions should complete immediately."""

    def test_single_terminal_state(self):
        """A state with no actions → exploration complete."""
        ctrl = ExplorationController("session-empty", max_step_budget=20)

        ctrl.register_state("A", "scr_A", [])  # no actions

        action = ctrl.get_next_action()
        assert action is None
        assert ctrl.status == ExplorationStatus.COMPLETED

    def test_frontier_empty_after_exhaustion(self):
        """After all states are explored, frontier should be empty."""
        ctrl = ExplorationController("session-exhaust", max_step_budget=20)

        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1"))
        action = ctrl.get_next_action()
        ctrl.report_action_result(action, succeeded=True, new_state_id="B")
        ctrl.register_state("B", "scr_B", [], parent_state_id="A", parent_action=action)

        # Exhaust
        final = ctrl.get_next_action()
        assert final is None or final["type"] == "back"

        # If backtrack happened, simulate return
        if final is not None:
            ctrl.current_state_id = "A"
            final2 = ctrl.get_next_action()
            assert final2 is None

        assert ctrl.get_frontier_states() == [] or ctrl.status != ExplorationStatus.RUNNING


# ── Test: Step Budget Termination ────────────────────────────────────

class TestStepBudget:
    """Exploration must stop when step budget is exhausted."""

    def test_budget_of_3(self):
        """With budget=3, only 3 actions should execute."""
        ctrl = ExplorationController("session-budget", max_step_budget=3)

        # Create a state with many actions
        ctrl.register_state("A", "scr_A", _make_actions(
            "tap:btn_1", "tap:btn_2", "tap:btn_3", "tap:btn_4", "tap:btn_5"
        ))

        executed = 0
        while True:
            action = ctrl.get_next_action()
            if action is None:
                break
            executed += 1
            ctrl.report_action_result(action, succeeded=True, new_state_id=f"S{executed}")
            ctrl.register_state(f"S{executed}", f"scr_{executed}", [],
                               parent_state_id="A", parent_action=action)

        assert ctrl.step_count <= 3
        assert ctrl.status == ExplorationStatus.BUDGET_EXHAUSTED

    def test_budget_zero_means_no_actions(self):
        """Budget of 0 should prevent any action."""
        ctrl = ExplorationController("session-zero", max_step_budget=0)
        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1"))

        action = ctrl.get_next_action()
        assert action is None
        assert ctrl.status == ExplorationStatus.BUDGET_EXHAUSTED


# ── Test: Failed Actions ─────────────────────────────────────────────

class TestFailedActions:
    """Actions that fail repeatedly should be skipped."""

    def test_failed_action_retried_once(self):
        """A failed action's failure count increases."""
        ctrl = ExplorationController("session-fail", max_step_budget=20)
        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1", "tap:btn_2"))

        action1 = ctrl.get_next_action()
        assert action1["target_element_id"] == "btn_1"
        ctrl.report_action_result(action1, succeeded=False)

        # The failure is recorded
        node = ctrl.states["A"]
        key = node.action_key(action1)
        assert node.attempted_actions[key].failure_count == 1

    def test_skips_to_next_after_exhausted_failures(self):
        """After max failures, controller should move to next action."""
        ctrl = ExplorationController("session-skip-fail", max_step_budget=20, max_action_failures=1)
        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_bad", "tap:btn_good"))

        # First action (btn_bad)
        action1 = ctrl.get_next_action()
        ctrl.report_action_result(action1, succeeded=False)

        # btn_bad has 1 failure (>= max_action_failures=1) but was already attempted
        # Next should be btn_good
        action2 = ctrl.get_next_action()
        assert action2 is not None
        assert action2["target_element_id"] == "btn_good"


# ── Test: Stats ──────────────────────────────────────────────────────

class TestExplorationStats:
    """Verify stats reporting."""

    def test_stats_after_exploration(self):
        """Stats should reflect the exploration state."""
        ctrl = ExplorationController("session-stats", max_step_budget=20)

        ctrl.register_state("A", "scr_A", _make_actions("tap:btn_1"))
        action = ctrl.get_next_action()
        ctrl.report_action_result(action, succeeded=True, new_state_id="B")
        ctrl.register_state("B", "scr_B", [], parent_state_id="A", parent_action=action)

        stats = ctrl.get_stats()
        assert stats["session_id"] == "session-stats"
        assert stats["states_discovered"] == 2
        assert stats["transitions"] == 1
        assert stats["step_count"] == 1
