 Unsorted
========================================================================

 Features
------------------------------------------------------------------------

- [ ] Add functions to set different actions on States.
- [ ] Add functions to add States to StateMachines.
- [ ] Add a way to make Events specific to a StateMachine?
- [ ] Add transitions as something that can be set with the Constructor.
	- How valuable would this be?  We need a set of States before we can
	  create transitions to them.
- [ ] Add an analysis method to StateMachine that will test for things
  like:
	- Unused states
	- Unused events
	- Super states with only one sub state
	- Many states that have similar transitions, that could instead all
	  be part of a super state
- [ ] Add the ability to output a representation of a StateMachine as a
  mermaid diagram.
- [ ] Add the ability to output a representation of a StateMachine as a
  PlantUML diagram.
- [ ] Add the ability to output a representation of a StateMachine as a
  state table.


 Bugs
------------------------------------------------------------------------

- [ ] TK


 Maintenance
------------------------------------------------------------------------

- [ ] Do unit testing.
- [ ] Do unit testing for hierarchical state machines.
- [ ] Since I need Union anyway, should I just use Union everywhere
  instead of `|`?
- [ ] Refactor big ole' functions and methods into smaller
  ones.  (Especially `process_event()`.)


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
