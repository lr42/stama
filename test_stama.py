import unittest
import logging
from stama import (
    Event,
    Guard,
    State,
    StateMachine,
    SuperState,
    ConditionalJunction,
    STARTING_STATE,
    DEEP_HISTORY,
    SHALLOW_HISTORY,
)


# TODO Test for thread safety


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

    def test_handles_true_guard_conditions(self):
        self.tmp = 101

        self.go.transitions[self.cycle] = Guard(
            lambda: self.tmp > 100, self.stop
        )

        self.light.process_event(self.cycle)
        self.assertEqual(self.light.current_state, self.stop)

    def test_handles_false_guard_conditions(self):
        self.tmp = 99

        self.go.transitions[self.cycle] = Guard(
            lambda: self.tmp > 100, self.stop
        )

        self.light.process_event(self.cycle)
        self.assertEqual(self.light.current_state, self.go)


class TestHierarchicalSM(unittest.TestCase):
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

    def test_runs_all_exit_actions(self):
        self.a.on_exit = lambda: self.tmp.append("a")
        self.ab.on_exit = lambda: self.tmp.append("ab")
        self.abb.on_exit = lambda: self.tmp.append("abb")
        self.b.on_exit = lambda: self.tmp.append("b")

        self.tmp = []
        self.hsm.process_event(self.ev)
        self.assertEqual(self.tmp, ["abb", "ab", "a"])

        self.tmp = []
        self.hsm.process_event(self.ev)
        self.assertEqual(self.tmp, ["b"])

        # Test transitions within the same branch

        self.assertEqual(self.hsm.current_state, self.aaa)
        ev2 = Event()
        self.aaa.transitions[ev2] = self.aba
        self.aa.on_exit = lambda: self.tmp.append("aa")
        self.aaa.on_exit = lambda: self.tmp.append("aaa")

        self.tmp = []
        self.hsm.process_event(ev2)
        self.assertEqual(self.tmp, ["aaa", "aa"])

    def test_runs_all_entry_actions(self):
        self.a.on_entry = lambda: self.tmp.append("a")
        self.aa.on_entry = lambda: self.tmp.append("aa")
        self.aaa.on_entry = lambda: self.tmp.append("aaa")
        self.b.on_entry = lambda: self.tmp.append("b")

        self.tmp = []
        self.hsm.process_event(self.ev)
        self.assertEqual(self.tmp, ["b"])

        self.tmp = []
        self.hsm.process_event(self.ev)
        self.assertEqual(self.tmp, ["a", "aa", "aaa"])

        # Test transitions within the same branch

        self.assertEqual(self.hsm.current_state, self.aaa)
        ev2 = Event()
        self.aaa.transitions[ev2] = self.aba
        self.ab.on_entry = lambda: self.tmp.append("ab")
        self.aba.on_entry = lambda: self.tmp.append("aba")

        self.tmp = []
        self.hsm.process_event(ev2)
        self.assertEqual(self.tmp, ["ab", "aba"])

    def test_runs_enforce_actions(self):
        self.a.enforce = lambda: self.tmp.append("a")
        self.aa.enforce = lambda: self.tmp.append("aa")
        self.aaa.enforce = lambda: self.tmp.append("aaa")
        self.b.enforce = lambda: self.tmp.append("b")
        self.hsm.enforce = lambda: self.tmp.append("hsm")

        self.tmp = []
        self.hsm.process_event(self.ev)
        self.assertEqual(self.tmp, ["b", "hsm"])

        self.tmp = []
        self.hsm.process_event(self.ev)
        self.assertEqual(self.tmp, ["aaa", "aa", "a", "hsm"])

        self.assertEqual(self.hsm.current_state, self.aaa)
        ev2 = Event()
        self.aaa.transitions[ev2] = self.aba
        self.ab.enforce = lambda: self.tmp.append("ab")
        self.aba.enforce = lambda: self.tmp.append("aba")

        self.tmp = []
        self.hsm.process_event(ev2)
        self.assertEqual(self.tmp, ["aba", "ab", "a", "hsm"])

    def test_can_upgrade_state_to_superstate(self):
        with self.assertLogs(level=logging.WARNING):
            self.b.make_super_state()

        self.assertIsInstance(self.b, SuperState)

    def test_auto_upgrades_state_to_superstate(self):
        ba = State("ba")
        with self.assertLogs(level=logging.WARNING):
            ba.add_to_super_state(self.b)

        self.assertIsInstance(self.b, SuperState)


class TestConditionalJunctions(unittest.TestCase):
    def setUp(self):
        self.cooking = State("cooking")
        self.rare = State("rare")
        self.medium = State("medium")
        self.well_done = State("well done")
        self.temperature_check = ConditionalJunction(self.cooking)
        self.temperature_check.add_condition(
            lambda: self.temperature > 160, self.well_done
        )
        self.temperature_check.add_condition(
            lambda: self.temperature > 140, self.medium
        )
        self.temperature_check.add_condition(
            lambda: self.temperature > 120, self.rare
        )
        self.timer = Event("timer")
        self.cooking.transitions[self.timer] = self.temperature_check
        self.kitchen = StateMachine(self.cooking)

    def test_checks_conditions(self):
        # TODO Do this for everything:
        logging.debug("******************** Conditional Junction: Does it check conditions?")

        self.temperature = 100
        logging.debug("temperature: %s", self.temperature)
        self.kitchen.process_event(self.timer)

        self.assertEqual(self.kitchen.current_state, self.cooking)

        self.temperature = 150
        logging.debug("temperature: %s", self.temperature)
        self.kitchen.process_event(self.timer)

        self.assertEqual(self.kitchen.current_state, self.medium)

        logging.info("Done: Conditional Junction: Does it check conditions?")


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    unittest.main()
