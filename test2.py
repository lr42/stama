# coding: utf-8
# %load test.py
import logging
logging.basicConfig(level=logging.INFO)
from stama import Event, State, StateMachine, SuperState
go = State('go')
stop = State('stop')
cycle = Event('cycle')
go.transitions[cycle] = stop
stop.transitions[cycle] = go
light = StateMachine(go)
print(light.current_state)
input()
light.process_event(cycle)
print(light.current_state)
input()
light.process_event(cycle)
print(light.current_state)
input("\nGet ready for a debug avalance!")
logging.getLogger().setLevel(logging.DEBUG)
light.process_event(cycle)
logging.getLogger().setLevel(logging.INFO)

print()
input()
on = State('on')
go.add_to_super_state(on)
stop.add_to_super_state(on)
off = State('off')
print(on._starting_state)
print(on._preferred_entry)
power = Event('toggle power')
on.transitions[power] = off
off.transitions[power] = on
light.process_event(power)

input()
light.process_event(power)
