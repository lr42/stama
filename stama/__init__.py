"""A library for creating state machines"""

import logging
from typing import (
    Union,
    TypeVar,
    Callable,
)
from threading import RLock


logger = logging.getLogger(__name__)

T = TypeVar("T")


class SMEventNotHandledException(Exception):
    """The current State does not have a transition defined for this Event
    (nor do any of it's SuperStates)
    """


class Event:  # pylint: disable=too-few-public-methods
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

        self.on_before_transition: Callable = lambda: logger.debug(
            "No action set for before %s transition.", self
        )
        self.on_during_transition: Callable = lambda: logger.debug(
            "No action set for during %s transition.", self
        )
        self.on_after_transition: Callable = lambda: logger.debug(
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
        name: str = "",
        description: str = "",
        parent: Union["SuperState", "State", None] = None,
    ):
        self.name: str = name
        if self.name == "":
            self.name = "S" + str(len(State.all_states_globally))

        self.description: str = description

        if parent is not None:
            self.add_to_super_state(parent)
        self._parent = parent

        self.transitions: dict["Event", "State"] = {}

        self.on_entry: Callable = lambda: logger.debug(
            "No action set for entering %s.", self
        )
        self.on_exit: Callable = lambda: logger.debug(
            "No action set for exiting %s.", self
        )
        self.enforce: Callable = lambda: logger.debug(
            "Nothing to enforce on %s.", self
        )

        State.all_states_globally.append(self)

    def __repr__(self):
        return "<State: " + self.name + ">"

    @property
    def parent(self):
        """The super-state that this state belongs to"""
        return self._parent

    # Don't add type hints to this function.  The `__class__`
    #  reassignment makes type checking not work very well here.
    def make_super_state(self, starting_state=None):
        """Make this state into a SuperState"""
        self.__class__ = SuperState
        # pylint: disable=no-member
        self._init_super_state(starting_state)

    def add_to_super_state(self, parent: Union["SuperState", "State"]):
        """Add this state as a sub-state to a super-state"""
        if not isinstance(parent, SuperState):
            parent.make_super_state(starting_state=self)
        self._parent = parent


class SuperState(State):
    """A state which can contain other states as sub-states"""

    def __init__(
        self,
        name: str = "",
        description: str = "",
        parent: Union[State, None] = None,
        starting_state: Union[State, None] = None,
    ):
        super().__init__(name, description, parent)
        self._init_super_state(starting_state)

    def _init_super_state(self, starting_state: State | None = None):
        self._starting_state: State | None = starting_state
        self._shallow_history: State | None = None
        self._deep_history: State | None = None
        self._preferred_entry_state: str = "start"
        self._child_states: list[State] = []
        if starting_state is not None:
            self._child_states.append(starting_state)


class StateMachine:
    """Stores current state, and changes it based on events"""

    all_machines_globally: list["StateMachine"] = []

    def __init__(
        self,
        starting_state: State,
        name: str = "",
        description: str = "",
    ):
        self.name: str = name
        if self.name == "":
            self.name = "M" + str(
                len(StateMachine.all_machines_globally)
            )

        self.description = description

        self._starting_state: State = starting_state
        self._current_state: State = self._starting_state

        self.enforce: Callable = lambda: logger.debug(
            "Nothing to enforce on %s.", self
        )

        self._lock: RLock = RLock()

    def __repr__(self):
        return "<SMachine: " + self.name + ">"

    @property
    def current_state(self):
        """The current state the state machine is in"""
        return self._current_state

    def process_event(self, event: Event) -> None:
        """Change to the next state, based on the event passed"""
        with self._lock:
            handling_state = self._current_state
            while event not in handling_state.transitions:
                if handling_state.parent is not None:
                    handling_state = handling_state.parent  # type: ignore
                else:
                    raise SMEventNotHandledException(
                        "No transition defined for "
                        + str(event)
                        + " in "
                        + str(self._current_state)
                    )
            destination_state: State = handling_state.transitions[event]
            # TODO Add checking to see if the destination state is a
            #  super state, and if so, point to the true destination
            #  state. Maybe use `proxy_destination_state` and
            #  `true_destination_state`?

            logger.debug(
                "%s: Transition start: %s --> %s --> %s",
                self,
                self._current_state,
                event,
                destination_state,
            )

            origin_ancestry: list[SuperState] = _get_ancestors(
                self._current_state
            )
            logger.debug("origin_ancestry: %s", origin_ancestry)

            destination_ancestry: list[SuperState] = _get_ancestors(
                destination_state
            )
            logger.debug(
                "destination_ancestry: %s", destination_ancestry
            )

            common_ancestor: SuperState | None = _get_common_ancestor(
                origin_ancestry, destination_ancestry
            )
            logger.debug("common_ancestor: %s", common_ancestor)

            # TODO Check guard.

            event.on_before_transition()

            if common_ancestor is None:
                uncommon_origin_ancestors = origin_ancestry[:]
            else:
                uncommon_origin_ancestors = origin_ancestry[
                    : origin_ancestry.index(common_ancestor)
                ]

            self._current_state.on_exit()
            for state in uncommon_origin_ancestors:
                state.on_exit()

            event.on_during_transition()

            origin_state = self._current_state
            self._current_state = destination_state

            if common_ancestor is None:
                uncommon_destination_ancestors = destination_ancestry[:]
            else:
                uncommon_destination_ancestors = destination_ancestry[
                    : destination_ancestry.index(common_ancestor)
                ]
            uncommon_destination_ancestors.reverse()

            for state in uncommon_destination_ancestors:
                state.on_entry()
            self._current_state.on_entry()

            event.on_after_transition()

            for state in destination_ancestry:
                state.enforce()
            self.enforce()

            logger.info(
                "%s: Transition done: %s --> %s --> %s",
                self,
                origin_state,
                event,
                self._current_state,
            )


def _get_ancestors(state: State) -> list[SuperState]:
    ancestry_list: list[SuperState] = []
    while state.parent is not None:
        ancestry_list.append(state.parent)
        state = state.parent  # type: ignore
    return ancestry_list


def _get_common_ancestor(x: list[T], y: list[T]) -> T | None:
    for i in x:
        if i in y:
            return i
    return None


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
