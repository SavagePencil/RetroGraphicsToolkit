from typing import Optional

class State:
    @staticmethod
    def on_enter(context: object) -> Optional['State']:
        # Default to no transition.
        return None
    
    @staticmethod
    def on_update(context: object) -> Optional['State']:
        # Default to no transition
        return None

    @staticmethod
    def on_exit(context: object):
        # Exiting can't initiate a transition
        return


class FSM:
    def __init__(self, context: object):
        self._context = context
        self._current_state = None

    def start(self, initial_state: State):
        # Enter the initial state.
        self.transition_state(initial_state)

    def get_current_state(self) -> State:
        return self._current_state

    def transition_state(self, new_state: State):
        while new_state != None:
            # Exit the current state.
            if self._current_state is not None:
                self._current_state.on_exit(self._context)

            # Update current
            self._current_state = new_state

            # Enter the now-current state
            new_state = self._current_state.on_enter(self._context)

    def update(self):
        new_state = self._current_state.on_update(self._context)

        if new_state is not None:
            self.transition_state(new_state)

