"""A library for creating state machines"""

import logging
from typing import (
    List,
    Optional,
    Callable,
)
from threading import RLock


logger = logging.getLogger(__name__)


class SMEventNotHandledException(Exception):
    """The current State does not have a transition defined for this Event
    (nor do any of it's SuperStates)
    """


class Event:  # pylint: disable=too-few-public-methods
    """An event which is passed to a state machine"""

    all_events_globally: List["Event"] = []

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        if self.name is None:
            self.name = "E" + str(len(State.all_states_globally))

        self._description = description

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
        return "<Event: " + self.name + ">"


class State:
    """One of the many states that a state machine can be in"""

    # pylint: disable=too-many-instance-attributes

    all_states_globally: List["State"] = []

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent: Optional["SuperState"] = None,
    ):
        self.name = name
        if self.name is None:
            self.name = "S" + str(len(State.all_states_globally))

        self.description = description

        if parent is not None:
            self.add_to_super_state(parent)
        self._parent = parent

        self.transitions: dict[Event, "State"] = {}

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
    def make_super_state(self, starting_state: "State") -> None:
        """Make this state into a SuperState"""
        self.__class__ = SuperState
        # pylint: disable=no-member
        self._init_super_state(starting_state)  # type: ignore

    def add_to_super_state(self, parent: "SuperState") -> None:
        """Add this state as a sub-state to a super-state"""
        if not isinstance(parent, SuperState):
            logger.warning(
                "Automatically converting %s to a SuperState.  This is mostly for playing around and you shouldn't use it in production code."
            )
            parent.make_super_state()
        if parent.starting_state is None:
            parent.starting_state = self
        self._parent = parent


STARTING_STATE = "starting state"
SHALLOW_HISTORY = "shallow history"
DEEP_HISTORY = "deep history"


class SuperState(State):
    """A state which can contain other states as sub-states"""

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent: Optional["SuperState"] = None,
        starting_state: Optional[State] = None,
    ):
        super().__init__(name, description, parent)
        self._init_super_state(starting_state)

    def _init_super_state(self, starting_state):
        self.starting_state = starting_state
        self._shallow_history = None
        self._deep_history = None
        self._preferred_entry = STARTING_STATE
        self._child_states = []
        if starting_state is not None:
            self._child_states.append(starting_state)


class StateMachine:
    """Stores current state, and changes it based on events"""

    all_machines_globally: List["StateMachine"] = []

    def __init__(
        self,
        starting_state: State,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        if self.name is None:
            self.name = "M" + str(
                len(StateMachine.all_machines_globally)
            )

        self.description = description

        self._starting_state = starting_state
        self._current_state = self._starting_state

        self.enforce: Callable = lambda: logger.debug(
            "Nothing to enforce on %s.", self
        )

        self._lock = RLock()

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
            proxy_destination = handling_state.transitions[event]

            if proxy_destination is None:
                logger.debug(
                    "%s handles %s internally, so no transition is done, and no actions are run.",
                    self.current_state,
                    event,
                )
                return

            # TODO I think this would work better refactored into a function.
            true_destination = proxy_destination
            while isinstance(true_destination, SuperState):
                logger.info(
                    "%s is a SuperState, redirecting to the proper sub-state",
                    true_destination,
                )
                # pylint: disable=protected-access
                if true_destination._preferred_entry == STARTING_STATE:
                    true_destination = true_destination.starting_state
                elif true_destination._preferred_entry == DEEP_HISTORY:
                    true_destination = true_destination._deep_history
                elif (
                    true_destination._preferred_entry == SHALLOW_HISTORY
                ):
                    true_destination = true_destination._shallow_history
                logger.info(
                    "%s is the new true_destination", true_destination
                )

            logger.debug(
                "%s: Transition start: %s --> %s --> %s",
                self,
                self._current_state,
                event,
                true_destination,
            )

            origin_ancestry = _get_ancestors(self._current_state)
            logger.debug("origin_ancestry: %s", origin_ancestry)

            destination_ancestry = _get_ancestors(true_destination)
            logger.debug(
                "destination_ancestry: %s", destination_ancestry
            )

            common_ancestor = _get_common_ancestor(
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

            origin_state = self._current_state

            self._current_state.on_exit()

            # Process uncommon ancestors
            child_state = self._current_state
            for state in uncommon_origin_ancestors:
                state.on_exit()
                # pylint: disable=protected-access
                state._deep_history = origin_state
                state._shallow_history = child_state
                child_state = state

            event.on_during_transition()

            self._current_state = true_destination

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


def _get_ancestors(state):
    ancestry_list = []
    while state.parent is not None:
        ancestry_list.append(state.parent)
        state = state.parent  # type: ignore
    return ancestry_list


def _get_common_ancestor(x, y):
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
