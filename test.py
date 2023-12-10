# coding: utf-8
import logging
logging.basicConfig(level=logging.INFO)
from stama import Event, State, StateMachine
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
