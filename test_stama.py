from stama import Event, State, StateMachine, SuperState, STARTING_STATE, DEEP_HISTORY, SHALLOW_HISTORY
import unittest
import logging


def create_simple_traffic_light():
    go = State("go")
    stop = State("stop")
    cycle = Event("cycle")
    go.transitions[cycle] = stop
    stop.transitions[cycle] = go
    light = StateMachine(go)
    return go, stop, cycle, light


def create_hierarchical_machine():
    a = SuperState("a")
    b = State("b")

    aa = SuperState("aa")
    aa.add_to_super_state(a)
    ab = SuperState("ab")
    ab.add_to_super_state(a)
    # ba = SuperState('ba')
    # ba.add_to_super_state(b)
    # bb = SuperState('bb')
    # bb.add_to_super_state(b)

    aaa = State("aaa")
    aaa.add_to_super_state(aa)
    aab = State("aab")
    aab.add_to_super_state(aa)
    aba = State("aba")
    aba.add_to_super_state(ab)
    abb = State("abb")
    abb.add_to_super_state(ab)

    # baa = State('baa')
    # baa.add_to_super_state(ba)
    # bab = State('bab')
    # bab.add_to_super_state(ba)
    # bba = State('bba')
    # bba.add_to_super_state(bb)
    # bbb = State('bbb')
    # bbb.add_to_super_state(bb)

    ev = Event("ev")

    abb.transitions[ev] = b
    b.transitions[ev] = a

    hsm = StateMachine(abb, "hsm")

    return a, b, aa, ab, aaa, aab, aba, abb, ev, hsm


class TestStama(unittest.TestCase):
    def test_processes_events(self):
        go, stop, cycle, light = create_simple_traffic_light()

        self.assertEqual(light.current_state, go)

        light.process_event(cycle)
        self.assertEqual(light.current_state, stop)

        light.process_event(cycle)
        self.assertEqual(light.current_state, go)

    def test_runs_state_on_entry_actions(self):
        go, stop, cycle, light = create_simple_traffic_light()

        global tmp
        tmp = "Move fast"

        def temp_func():
            global tmp
            tmp = "Don't move"

        stop.on_entry = temp_func

        light.process_event(cycle)

        self.assertEqual(light.current_state, stop)
        self.assertEqual(tmp, "Don't move")

    def test_runs_state_on_exit_actions(self):
        go, stop, cycle, light = create_simple_traffic_light()

        global tmp
        tmp = "Move fast"

        def temp_func():
            global tmp
            tmp = "Don't move"

        go.on_exit = temp_func

        light.process_event(cycle)

        self.assertEqual(light.current_state, stop)
        self.assertEqual(tmp, "Don't move")

    def test_runs_event_on_before_actions(self):
        go, stop, cycle, light = create_simple_traffic_light()

        global tmp
        tmp = "Nothing"

        def temp_exit():
            global tmp
            self.assertEqual(tmp, "Something")

        go.on_exit = temp_exit

        def temp_entry():
            global tmp
            self.assertEqual(tmp, "Something")

        stop.on_entry = temp_entry

        def temp_before():
            global tmp
            tmp = "Something"

        cycle.on_before_transition = temp_before

        self.assertEqual(tmp, "Nothing")
        light.process_event(cycle)

    def test_runs_event_on_during_actions(self):
        go, stop, cycle, light = create_simple_traffic_light()

        global tmp
        tmp = "Nothing"

        def temp_exit():
            global tmp
            self.assertEqual(tmp, "Nothing")

        go.on_exit = temp_exit

        def temp_entry():
            global tmp
            self.assertEqual(tmp, "Something")

        stop.on_entry = temp_entry

        def temp_during():
            global tmp
            tmp = "Something"

        cycle.on_during_transition = temp_during

        self.assertEqual(tmp, "Nothing")
        light.process_event(cycle)

    def test_runs_event_on_after_actions(self):
        go, stop, cycle, light = create_simple_traffic_light()

        global tmp
        tmp = "Nothing"

        def temp_exit():
            global tmp
            self.assertEqual(tmp, "Nothing")

        go.on_exit = temp_exit

        def temp_entry():
            global tmp
            self.assertEqual(tmp, "Nothing")

        stop.on_entry = temp_entry

        def temp_after():
            global tmp
            tmp = "Something"

        cycle.on_after_transition = temp_after

        self.assertEqual(tmp, "Nothing")
        light.process_event(cycle)
        self.assertEqual(tmp, "Something")


class TestHierarchicalStateMachine(unittest.TestCase):
    def test_goes_to_the_starting_state(self):
        a, b, aa, ab, aaa, aab, aba, abb, ev, hsm = create_hierarchical_machine()

        self.assertEqual(hsm.current_state, abb)

        hsm.process_event(ev)
        self.assertEqual(hsm.current_state, b)

        hsm.process_event(ev)
        self.assertEqual(hsm.current_state, aaa)

    def test_goes_to_deep_history(self):
        a, b, aa, ab, aaa, aab, aba, abb, ev, hsm = create_hierarchical_machine()

        a._preferred_entry = DEEP_HISTORY

        self.assertEqual(hsm.current_state, abb)

        hsm.process_event(ev)
        self.assertEqual(hsm.current_state, b)

        hsm.process_event(ev)
        self.assertEqual(hsm.current_state, abb)

    def test_goes_to_shallow_history(self):
        a, b, aa, ab, aaa, aab, aba, abb, ev, hsm = create_hierarchical_machine()

        a._preferred_entry = SHALLOW_HISTORY

        self.assertEqual(hsm.current_state, abb)

        hsm.process_event(ev)
        self.assertEqual(hsm.current_state, b)

        hsm.process_event(ev)
        self.assertEqual(hsm.current_state, aba)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    unittest.main()
