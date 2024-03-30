 Unsorted
========================================================================

 Features
------------------------------------------------------------------------

- [x] Add conditional junctions.
- [ ] Add pass-through junctions, that run their `on_entry` actions, but
  then transition directly to the next state, running their `on_exit()`
  methods on the way.  Basically a conditional junction, without any
  conditions, only a default state to transitions to.
- [ ] Add concurrent states.  (Edited to add: What did I mean by this?)
- [ ] Add forks and unions.
- [ ] Add functions to set different actions on States.
- [ ] Add an analysis method to StateMachine that will test for things
  like:
	- Unused states
	- Unused events
	- Super states with only one sub state
	- Many states that have similar transitions, that could instead all
	  be part of a super state
	- StateMachines that fully overlap
	- StateMachines that partially overlap!
		- Something pretty crazy must be going on for this to happen.
- [ ] Add the ability to output a representation of a StateMachine as a
  mermaid diagram.
- [ ] Add the ability to output a representation of a StateMachine as a
  PlantUML diagram.
	- [ ] Possibly use the `__doc__` property to give more information
	about states.
- [ ] Add the ability to output a representation of a StateMachine as a
  Graphviz (dot) file?
- [ ] Add the ability to output a representation of a StateMachine as a
  state table.
	- As CSV?
	- A LaTex?
- [ ] Add a 'lenient' flag that lets a user upgrade a state?
	- Would it be better to just pass a State to a SuperState, to get a
	  new SuperState back, and then assign that as a new parent?
- [ ] Allow creating/importing a state machine and all states and events
  from a JSON tree or something similar.
	- Maybe a state table?
- [ ] Allow outputting a StateMachine as JSON/XML/or something else.
- [ ] Better documentation for class and method parameters.


 Bugs
------------------------------------------------------------------------

- [ ] Fix potential race conditions when modifiying states or events
  when a state transition is happening, by adding locks in appropriate
  places.  (See commit: `39bf3d94377b5e029e18bf8247b528c43fd32b75`.)
- [ ] Currently the ConditionalJunction logs are wrong.  They don't show
  where we are coming from.  The currently look like the following:

	INFO:stama.stama:<SMachine: M0>: Transition done: <ConditionalJunction: CJ0> --> None --> <State: Waiting for a short break>



 Maintenance
------------------------------------------------------------------------

- [x] Since I need Union anyway, should I just use Union everywhere
  instead of `|`?
- [ ] Use an enum for preferred substate selection?
- [ ] Create a proper `Node` class, to reduce code reuse.  (This class
  could be a better bass class for `State`, `Junction`, and possibly
  others.)
- [ ] Set up git hooks to handle testing, linting, formatting, etc.
- [ ] Change line widths to 79, to match PEP8.
- [ ] Add docstrings to the unit tests?
- [ ] Add a start() method to StateMachine, so we can delay initializing
  it until we are ready for it.  (Perhaps we want to set up our starting
  state after we create our StateMachine.)
- [ ] Only show enforced actions if there are any enforced actions at
  all.  I don't need to see which states don't have enforced actions if
  none of them do.
	- Are there any other places where this applies?


 Up next
========================================================================

 Features
------------------------------------------------------------------------



 Maintenance
------------------------------------------------------------------------



 Done
========================================================================

 Features
------------------------------------------------------------------------

- [x] Add a name and description to StateMachine.


 Maintenance
------------------------------------------------------------------------

- [x] I need to add an indicator that a state is a super state, a
  starting state, history, deep history, and the preferred entry state
  for super states.
- [x] Handle 'internal' transitions, where the transition is set to
  `None`.
- [x] Use `setup` and `teardown` functions inside of unit tests.
	- If possible, it'd be nice to remove the need for a global variable
	  as well.
- [x] Do unit testing.
- [x] Do unit testing for hierarchical state machines.
- [x] Refactor big ole' functions and methods into smaller
  ones (especially `process_event()`).
- [x] {DELETED} Add transitions as something that can be set with the
  Constructor.
	- How valuable would this be?  We need a set of States before we can
	  create transitions to them.
- [x] {DELETED} Add functions to add States to StateMachines.
	- I'd rather analyze States to see if they belong to a
	  StateMachine.  I cna use the whole list of StateMachines to test
	  all StateMachines and see if there are States that are orphaned or
	  that belong to more than one StateMachine.
- [x] {DELETED} Add a way to make Events specific to a StateMachine?
	- See above.
- [x] Add guard conditions.
