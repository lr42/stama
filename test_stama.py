import unittest
import logging
from stama import (
    Event,
    State,
    StateMachine,
    SuperState,
    STARTING_STATE,
    DEEP_HISTORY,
    SHALLOW_HISTORY,
)


# TODO Enforce actions
# TODO Ensure all exit and entry actions are done on a HSM

# TODO Guards


class TestStama(unittest.TestCase):
    def setUp(self):
        self.go = State("go")
        self.stop = State("stop")
        self.cycle = Event("cycle")
        self.go.transitions[self.cycle] = self.stop
        self.stop.transitions[self.cycle] = self.go
        self.light = StateMachine(self.go)

    def test_processes_events(self):
        self.assertEqual(self.light.current_state, self.go)

        self.light.process_event(self.cycle)
        self.assertEqual(self.light.current_state, self.stop)

        self.light.process_event(self.cycle)
        self.assertEqual(self.light.current_state, self.go)

    def test_runs_state_on_entry_actions(self):
        self.tmp = "Move fast"

        def temp_func():
            self.tmp = "Don't move"

        self.stop.on_entry = temp_func

        self.light.process_event(self.cycle)

        self.assertEqual(self.light.current_state, self.stop)
        self.assertEqual(self.tmp, "Don't move")

    def test_runs_state_on_exit_actions(self):
        self.tmp = "Move fast"

        def temp_func():
            self.tmp = "Don't move"

        self.go.on_exit = temp_func

        self.light.process_event(self.cycle)

        self.assertEqual(self.light.current_state, self.stop)
        self.assertEqual(self.tmp, "Don't move")

    def test_runs_event_on_before_actions(self):
        self.tmp = "Nothing"

        def temp_exit():
            self.assertEqual(self.tmp, "Something")

        self.go.on_exit = temp_exit

        def temp_entry():
            self.assertEqual(self.tmp, "Something")

        self.stop.on_entry = temp_entry

        def temp_before():
            self.tmp = "Something"

        self.cycle.on_before_transition = temp_before

        self.assertEqual(self.tmp, "Nothing")
        self.light.process_event(self.cycle)

    def test_runs_event_on_during_actions(self):
        self.tmp = "Nothing"

        def temp_exit():
            self.assertEqual(self.tmp, "Nothing")

        self.go.on_exit = temp_exit

        def temp_entry():
            self.assertEqual(self.tmp, "Something")

        self.stop.on_entry = temp_entry

        def temp_during():
            self.tmp = "Something"

        self.cycle.on_during_transition = temp_during

        self.assertEqual(self.tmp, "Nothing")
        self.light.process_event(self.cycle)

    def test_runs_event_on_after_actions(self):
        self.tmp = "Nothing"

        def temp_exit():
            self.assertEqual(self.tmp, "Nothing")

        self.go.on_exit = temp_exit

        def temp_entry():
            self.assertEqual(self.tmp, "Nothing")

        self.stop.on_entry = temp_entry

        def temp_after():
            self.tmp = "Something"

        self.cycle.on_after_transition = temp_after

        self.assertEqual(self.tmp, "Nothing")
        self.light.process_event(self.cycle)
        self.assertEqual(self.tmp, "Something")


class TestHierarchicalStateMachine(unittest.TestCase):
    def setUp(self):
        self.a = SuperState("a")
        self.b = State("b")

        self.aa = SuperState("aa")
        self.aa.add_to_super_state(self.a)
        self.ab = SuperState("ab")
        self.ab.add_to_super_state(self.a)

        self.aaa = State("aaa")
        self.aaa.add_to_super_state(self.aa)
        self.aab = State("aab")
        self.aab.add_to_super_state(self.aa)
        self.aba = State("aba")
        self.aba.add_to_super_state(self.ab)
        self.abb = State("abb")
        self.abb.add_to_super_state(self.ab)

        self.ev = Event("ev")

        self.abb.transitions[self.ev] = self.b
        self.b.transitions[self.ev] = self.a

        self.hsm = StateMachine(self.abb, "hsm")

    def test_goes_to_starting_state(self):
        self.assertEqual(self.hsm.current_state, self.abb)

        self.hsm.process_event(self.ev)
        self.assertEqual(self.hsm.current_state, self.b)

        self.hsm.process_event(self.ev)
        self.assertEqual(self.hsm.current_state, self.aaa)

    def test_goes_to_deep_history(self):
        self.a._preferred_entry = DEEP_HISTORY

        self.assertEqual(self.hsm.current_state, self.abb)

        self.hsm.process_event(self.ev)
        self.assertEqual(self.hsm.current_state, self.b)

        self.hsm.process_event(self.ev)
        self.assertEqual(self.hsm.current_state, self.abb)

    def test_goes_to_shallow_history(self):
        self.a._preferred_entry = SHALLOW_HISTORY

        self.assertEqual(self.hsm.current_state, self.abb)

        self.hsm.process_event(self.ev)
        self.assertEqual(self.hsm.current_state, self.b)

        self.hsm.process_event(self.ev)
        self.assertEqual(self.hsm.current_state, self.aba)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    unittest.main()
