"""A library for creating state machines"""

from threading import RLock
from typing import TypeVar
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _get_ancestry_list(state: "State") -> list["State"]:
    ancestry_list: list["State"] = []
    while state.parent is not None:
        ancestry_list.append(state)
        state = state.parent  # type: ignore
    ancestry_list.append(state)
    return ancestry_list


def _get_common_parent(x: list[T], y: list[T]) -> T | None:
    for i in x:
        if i in y:
            return i
    return None


class Event:
    """An event which is passed to a state machine"""

    all_events_globally: list["Event"] = []

    def __init__(
        self,
        name: str | None = None,
        description: str = "",
    ):
        self._name: str | None = name
        if self._name is None:
            self._name = "E" + str(len(State.all_states_globally))

        self._description: str = description

        self.on_before = lambda: logger.debug(
            "No action set for before %s transition.", self
        )
        self.on_during = lambda: logger.debug(
            "No action set for during %s transition.", self
        )
        self.on_after = lambda: logger.debug(
            "No action set for after %s transition.", self
        )

        Event.all_events_globally.append(self)

    def __repr__(self):
        return "<Event: " + self._name + ">"


class State:
    """One of the many states that a state machine can be in"""

    # pylint: disable=too-many-instance-attributes

    all_states_globally: list["State"] = []

    def __init__(
        self,
        name: str | None = None,
        description: str = "",
        parent=None,
    ):
        self.name: str | None = name
        if self.name is None:
            self.name = "S" + str(len(State.all_states_globally))

        self.description: str = description
        self.parent: "State" | None = parent

        self.transitions: dict["Event", "State"] = {}

        self.on_entry = lambda: logger.debug("No action set for entering %s.", self)
        self.on_exit = lambda: logger.debug("No action set for exiting %s.", self)
        self.enforce = lambda: logger.debug(
            "Nothing to enforce on %s.", self
        )

        State.all_states_globally.append(self)

    def __repr__(self):
        return "<State: " + self.name + ">"


class StateMachine:
    """Stores current state, and changes it based on events"""

    def __init__(self, starting_state: State):
        self._starting_state = starting_state
        self._current_state = self._starting_state
        self.enforce = lambda: logger.debug(
            "Nothing to enforce on %s.", self
        )
        self._lock = RLock()

    @property
    def current_state(self):
        """The current state the state machine is in"""
        return self._current_state

    def process_event(self, event: Event):
        """Change to the next state, based on the event passed"""
        # ! Acquire an RLock.
        with self._lock:
            # ! Check to see if event is handled in the state.  If not, move
            # !  up to the next parent state.

            handling_state = self._current_state
            while event not in handling_state.transitions:
                if handling_state.parent is not None:
                    handling_state = handling_state.parent  # type: ignore
                else:
                    raise Exception(  # pylint: disable=broad-exception-raised
                        "TK"
                    )
            destination_state: "State" = handling_state.transitions[
                event
            ]
            logger.debug(
                "Transition start: %s -> %s -> %s",
                self.current_state,
                event,
                destination_state,
            )

            # ! Use the origin state and destination state to find the shared
            # !  parent.
            origin_ancestry: list["State"] = _get_ancestry_list(
                self._current_state
            )
            logger.debug("origin_ancestry: %s", origin_ancestry)
            destination_ancestry: list["State"] = _get_ancestry_list(
                destination_state
            )
            logger.debug("destination_ancestry: %s", destination_ancestry)

            common_parent_state: "State" | None = _get_common_parent(
                origin_ancestry, destination_ancestry
            )
            logger.debug("common_parent_state: %s", common_parent_state)

            # ! When you've found a state that handles the event, do the
            # !  following:
            # ! Check guard.
            # ! Run Event.on_before().
            event.on_before()

            # ! Run on_exit() for each state from the orgin upto (but not
            # !  including) the shared parent state.
            if common_parent_state is None:
                uncommon_origin_ancestors = origin_ancestry[:]
            else:
                uncommon_origin_ancestors = origin_ancestry[
                    : origin_ancestry.index(common_parent_state)
                ]
            for st in uncommon_origin_ancestors:
                st.on_exit()

            # ! Run Event.on_between().
            event.on_during()

            origin_state = self._current_state
            self._current_state = destination_state

            # ! Run on_entry() for the first child of the shared parent state
            # !  down to the destination state.
            if common_parent_state is None:
                uncommon_destination_ancestors = destination_ancestry[:]
            else:
                uncommon_destination_ancestors = destination_ancestry[
                    : destination_ancestry.index(common_parent_state)
                ]
            uncommon_destination_ancestors.reverse()
            for st in uncommon_destination_ancestors:
                st.on_entry()

            # ! Run Event.on_after().
            event.on_after()

            # ! Run State.enforce() for each state from the destination upto
            # !  the root.
            # !  - Should the state machine itself have an `enforce` method?
            for st in destination_ancestry:
                st.enforce()
            self.enforce()

            logger.info(
                "Transition done: %s -> %s -> %s",
                origin_state,
                event,
                destination_state,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    cycle = Event()
    print(cycle)
    my_state = State()
    print(my_state.name)
    print(State.all_states_globally)
    print(my_state.all_states_globally)

    my_state.on_entry()
    my_state.on_entry = lambda: print("cowabunga")
    my_state.on_entry()

    def my_new_on_entry():
        """Nonya biznis"""
        print("cows")
        print("pigs")

    my_state.on_entry = my_new_on_entry
    my_state.on_entry()

    # print(my_state.on_entry == State.on_entry)
