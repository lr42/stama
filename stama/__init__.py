"""A library for creating state machines"""

import logging
from typing import (
    List,
    Optional,
    Callable,
    Dict,
    Union,
    Tuple,
)
from threading import RLock


# pylint: disable=line-too-long


logger = logging.getLogger(__name__)


class SMEventNotHandledException(Exception):
    """
    The current State does not have a transition defined for this Event
    (nor do any of it's SuperStates).
    """


class Event:  # pylint: disable=too-few-public-methods
    """An event which is passed to a state machine."""

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

        self.on_before_transition: Callable[
            [], None
        ] = lambda: logger.debug(
            "No action set for before %s transition.", self
        )
        self.on_during_transition: Callable[
            [], None
        ] = lambda: logger.debug(
            "No action set for during %s transition.", self
        )
        self.on_after_transition: Callable[
            [], None
        ] = lambda: logger.debug(
            "No action set for after %s transition.", self
        )

        Event.all_events_globally.append(self)

    def __repr__(self):
        return "<Event: " + self.name + ">"


class Guard:
    """A conditional guard, which can be set as a State's transition."""

    # pylint: disable=too-few-public-methods

    def __init__(self, condition: Callable[[], bool], state: "State"):
        self.condition = condition
        self.state = state

    def evaluate(self):
        """Returns the default state if the condition function evaluates to True."""
        if self.condition():
            return self.state
        return None


class Node:  # pylint: disable=too-few-public-methods
    """The base class for states (and similar nodes) that can be tranistioned to."""


class State(Node):
    """One of the many states that a state machine can be in."""

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

        self.transitions: Dict[Event, Union["State", Guard]] = {}

        State.all_states_globally.append(self)

    def __repr__(self):
        return "<State: " + self.name + ">"

    @property
    def parent(self):
        """The super-state that this state belongs to."""
        return self._parent

    def on_entry(self):
        logger.debug("No action set for entering %s.", self)

    def on_exit(self):
        logger.debug("No action set for exiting %s.", self)

    def enforce(self):
        logger.debug("Nothing to enforce on %s.", self)

    # Don't add type hints to this function.  The `__class__`
    #  reassignment makes type checking not work very well here.
    def make_super_state(
        self, starting_state: Optional["State"] = None
    ) -> None:
        """Make this state into a SuperState."""
        logger.warning(
            "Converting %s to a SuperState.  This is mostly for playing around and you shouldn't use it in production code.  (Create a SuperState object directly instead.)",
            self,
        )
        self.__class__ = SuperState
        # pylint: disable=no-member
        self._init_super_state(starting_state)  # type: ignore

    def add_to_super_state(self, parent: "SuperState") -> None:
        """Add this state as a sub-state to a super-state."""
        if not isinstance(parent, SuperState):
            parent.make_super_state(self)
        if parent.starting_state is None:
            parent.starting_state = self
        self._parent = parent


STARTING_STATE = "starting state"
SHALLOW_HISTORY = "shallow history"
DEEP_HISTORY = "deep history"


class SuperState(State):
    """A state which can contain other states as sub-states."""

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


class ConditionalJunction(Node):
    """One of the many states that a state machine can be in."""

    # pylint: disable=too-many-instance-attributes

    all_conditional_junctions_globally: List["ConditionalJunction"] = []

    def __init__(
        self,
        default_state: Node,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent: Optional["SuperState"] = None,
    ):
        # TODO A lot of this is copied directly from State.  I need to figure out where these overlap and create a shared base class that both of them use, that contains their common methods.
        self.name = name
        if self.name is None:
            self.name = "CJ" + str(
                len(
                    ConditionalJunction.all_conditional_junctions_globally
                )
            )  ## Change

        self.description = description

        if parent is not None:
            self.add_to_super_state(parent)
        self._parent = parent

        self.default_state = default_state
        self.condition_list: List[Tuple[Callable[[], bool], Node]] = []

        ## self.transitions: Dict[Event, Union["State", Guard]] = {}

        self.on_entry: Callable[[], None] = lambda: logger.debug(
            "No action set for entering %s.", self
        )
        self.on_exit: Callable[[], None] = lambda: logger.debug(
            "No action set for exiting %s.", self
        )
        self.enforce: Callable[[], None] = lambda: logger.debug(
            "Nothing to enforce on %s.", self
        )

        ConditionalJunction.all_conditional_junctions_globally.append(
            self
        )  ## Change

    def __repr__(self):
        return "<ConditionalJunction: " + self.name + ">"

    @property
    def parent(self):
        """The super-state that this state belongs to."""
        return self._parent

    ## # Don't add type hints to this function.  The `__class__`
    ## #  reassignment makes type checking not work very well here.
    ## def make_super_state(
    ##     self, starting_state: Optional["State"] = None
    ## ) -> None:
    ##     """Make this state into a SuperState."""
    ##     logger.warning(
    ##         "Converting %s to a SuperState.  This is mostly for playing around and you shouldn't use it in production code.  (Create a SuperState object directly instead.)",
    ##         self,
    ##     )
    ##     self.__class__ = SuperState
    ##     # pylint: disable=no-member
    ##     self._init_super_state(starting_state)  # type: ignore

    def add_to_super_state(self, parent: "SuperState") -> None:
        """Add this state as a sub-state to a super-state."""
        if not isinstance(parent, SuperState):
            parent.make_super_state(self)
        if parent.starting_state is None:
            parent.starting_state = self
        self._parent = parent
        ##############################################################

    def add_condition(self, condition, state):
        """Add a condition to the list of conditions to be checked in a ConditionalJunction, along with the State it should transition to if True."""
        self.condition_list.append((condition, state))

    def evaluate(self):
        """Evaluate all the conditions in this ConditionalJunction and for the first condition that is True, return the State to transition to."""
        for i in range(len(self.condition_list)):
            if self.condition_list[i][0]():
                logging.debug(
                    "%s: Condition #%s is true; next state is %s",
                    self,
                    i,
                    self.condition_list[i][1],
                )
                return self.condition_list[i][1]
        logging.debug(
            "%s: No condition met; default state is: %s",
            self,
            self.default_state,
        )
        return self.default_state


class StateMachine:
    """Stores current state, and changes it based on events."""

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

        self._lock = RLock()

        self.enforce: Callable[[], None] = lambda: logger.debug(
            "Nothing to enforce on %s.", self
        )

        self._starting_state = starting_state
        self._current_state = None
        self.transition_directly_to_state(starting_state)

    def __repr__(self):
        return "<SMachine: " + self.name + ">"

    @property
    def current_state(self):
        """The current state the state machine is in."""
        return self._current_state

    def _get_handling_state(self, event, origin_state):
        handling_state = origin_state
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
        return handling_state

    def _is_internal_transition(self, proxy_destination, event):
        if proxy_destination is None:
            logger.debug(
                "%s handles %s internally.  No transition done.  No actions run.",
                self.current_state,
                event,
            )
            return True
        return False

    def _get_final_destination(self, proxy_destination):
        final_destination = proxy_destination
        while isinstance(final_destination, SuperState):
            logger.info(
                "%s is a SuperState, redirecting to the proper sub-state",
                final_destination,
            )
            # pylint: disable=protected-access
            # TODO `_preferred_entry` should not (as far as I can tell) be a private/protected member.  It's either something that someone ought to be able to set outside of the class, or that is set by a public method inside the class.
            if final_destination._preferred_entry == STARTING_STATE:
                final_destination = final_destination.starting_state
            elif final_destination._preferred_entry == DEEP_HISTORY:
                final_destination = final_destination._deep_history
            elif final_destination._preferred_entry == SHALLOW_HISTORY:
                final_destination = final_destination._shallow_history
            logger.info(
                "%s is the new final_destination", final_destination
            )
        return final_destination

    def _figure_out_ancestry(self, origin_state, final_destination):
        origin_ancestry = _get_ancestors(origin_state)
        logger.debug("origin_ancestry: %s", origin_ancestry)

        destination_ancestry = _get_ancestors(final_destination)
        logger.debug("destination_ancestry: %s", destination_ancestry)

        common_ancestor = _get_common_ancestor(
            origin_ancestry, destination_ancestry
        )
        logger.debug("common_ancestor: %s", common_ancestor)

        return common_ancestor

    def _proceess_uncommon_origin_ancestors(
        self, uncommon_origin_ancestors, origin_state
    ):
        child_state = origin_state
        for state in uncommon_origin_ancestors:
            state.on_exit()
            # pylint: disable=protected-access
            state._deep_history = origin_state
            state._shallow_history = child_state
            child_state = state

    def _exit_current_state(self, origin_state, common_ancestor):
        origin_ancestry = _get_ancestors(origin_state)
        if common_ancestor is None:
            uncommon_origin_ancestors = origin_ancestry[:]
        else:
            uncommon_origin_ancestors = origin_ancestry[
                : origin_ancestry.index(common_ancestor)
            ]

        if origin_state is not None:
            origin_state.on_exit()

        self._proceess_uncommon_origin_ancestors(
            uncommon_origin_ancestors, origin_state
        )

    def _enter_destination_state(
        self, final_destination, common_ancestor
    ):
        destination_ancestry = _get_ancestors(final_destination)
        if common_ancestor is None:
            uncommon_destination_ancestors = destination_ancestry[:]
        else:
            uncommon_destination_ancestors = destination_ancestry[
                : destination_ancestry.index(common_ancestor)
            ]
        uncommon_destination_ancestors.reverse()

        for state in uncommon_destination_ancestors:
            state.on_entry()
        final_destination.on_entry()

    def _enforce_all_relevant_states(self, final_destination):
        self._current_state.enforce()
        destination_ancestry = _get_ancestors(final_destination)
        for state in destination_ancestry:
            state.enforce()
        self.enforce()

    def transition_directly_to_state(
        self, final_destination, event=None
    ) -> None:
        """Transition directly to a state, running all the appropriate actions along the way."""
        with self._lock:
            origin_state = self._current_state

            logger.debug(
                "%s: Transition start: %s --> %s --> %s",
                self,
                self._current_state,
                event,
                final_destination,
            )

            if origin_state is not None:
                common_ancestor = self._figure_out_ancestry(
                    origin_state, final_destination
                )
            else:
                common_ancestor = None

            if event is not None:
                event.on_before_transition()

            self._exit_current_state(origin_state, common_ancestor)

            if event is not None:
                event.on_during_transition()

            self._enter_destination_state(
                final_destination, common_ancestor
            )
            self._current_state = final_destination

            if event is not None:
                event.on_after_transition()

            self._enforce_all_relevant_states(final_destination)

            if isinstance(final_destination, ConditionalJunction):
                self.transition_directly_to_state(
                    final_destination.evaluate()
                )

            logger.info(
                "%s: Transition done: %s --> %s --> %s",
                self,
                origin_state,
                event,
                self._current_state,
            )

    def process_event(self, event: Event) -> None:
        """Change to the next state, based on the event passed in."""
        with self._lock:
            origin_state = self._current_state
            handling_state = self._get_handling_state(event, origin_state)

            if isinstance(handling_state.transitions[event], Guard):
                guard_condition = handling_state.transitions[event]
                proxy_destination = guard_condition.evaluate()
            else:
                proxy_destination = handling_state.transitions[event]

            # If this is an internal transition, we don't need to do
            #  any transition at all.
            if self._is_internal_transition(proxy_destination, event):
                return
            final_destination = self._get_final_destination(
                proxy_destination
            )

            self.transition_directly_to_state(final_destination, event)


def _get_ancestors(state):
    ancestry_list = []
    if state is not None:
        while state.parent is not None:
            ancestry_list.append(state.parent)
            state = state.parent  # type: ignore
    return ancestry_list


def _get_common_ancestor(x, y):
    for i in x:
        if i in y:
            return i
    return None
