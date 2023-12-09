"""A library for creating state machines"""

from threading import RLock
from typing import Callable, TypeVar
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

        Event.all_events_globally.append(self)

    def __repr__(self):
        return "<Event: " + self._name + ">"

    def on_before(self):
        """Run before a transition triggered by this event happens"""
        logger.warning("Before transition: %s", self)

    def on_between(self):
        logger.warning("Between states on transition: %s", self)

    def on_after(self):
        logger.warning("After transition: %s", self)


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

        self._on_entry_function: Callable = lambda: print(
            "Entering " + str(self)
        )

        self._on_exit_function: Callable = lambda: print(
            "Exiting " + str(self)
        )

        self._enforce_function: Callable = lambda: print(
            "Exiting " + str(self)
        )

        self.on_entry = lambda: print("Entering " + str(self))
        self.on_exit = lambda: print("Exiting " + str(self))
        self.enforce = lambda: print(
            "Nothing to enforce on " + str(self)
        )

        self.function_correlation = {
            "on_entry": [
                self._default_on_entry,
                self._on_entry_function,
            ],
            "on_exit": [
                self._default_on_entry,
                self._on_entry_function,
            ],
        }

        State.all_states_globally.append(self)

    def __repr__(self):
        return "<State: " + self.name + ">"

    def _default_on_entry(self):
        """Run when the state is entered into"""
        self._on_entry_function()

    def _default_on_exit(self):
        """Run when the state is exited out of"""
        self._on_exit_function()

    def _default_enforce(self):
        """Run when the state is exited out of"""
        self._enforce_function()

    # TODO Refactor this, since we'll be doing it often.
    def set_on_entry_function(self, function: Callable[[], None]):
        """Changes the function that is run on entry into a state"""
        self.on_entry = self._default_on_entry
        self._on_entry_function = function


class StateMachine:
    """Stores current state, and changes it based on events"""

    def __init__(self, starting_state: State):
        self._starting_state = starting_state
        self._current_state = self._starting_state
        self.enforce = self._default_enforce
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
                    raise Exception(
                        "Pickles TK"
                    )  # pylint: disable=broad-exception-raised
            destination_state: "State" = handling_state.transitions[
                event
            ]

            # ! Use the origin state and destination state to find the shared
            # !  parent.
            origin_ancestry: list["State"] = _get_ancestry_list(
                self._current_state
            )
            destination_ancestry: list["State"] = _get_ancestry_list(
                destination_state
            )

            common_parent_state: "State" | None = _get_common_parent(
                origin_ancestry, destination_ancestry
            )

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
            event.on_between()

            # ! Run on_entry() for the first child of the shared parent state
            # !  down to the destination state.
            if common_parent_state is None:
                uncommon_destination_ancestors = origin_ancestry[:]
            else:
                uncommon_destination_ancestors = origin_ancestry[
                    : origin_ancestry.index(common_parent_state)
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

    def _default_enforce(self):
        logger.warning("Enforcing state machine")


cycle = Event()
print(cycle)
my_state = State()
print(my_state.name)
print(State.all_states_globally)
print(my_state.all_states_globally)

my_state.on_entry()
my_state.on_entry = lambda: print("cowabunga")
my_state.on_entry()
my_state.set_on_entry_function(lambda: print("tubular??"))
my_state.on_entry()

# print(my_state.on_entry == State.on_entry)
