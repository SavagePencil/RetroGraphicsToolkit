from datetime import datetime, timedelta

class SimpleTimer:
    def __init__(self, name):
        self.name = name
        self._startTime = None
        self._endTime = None
        self._instantiations = 0
        self._elapsed_over_instantiations = timedelta()

    def begin(self):
        self._startTime = datetime.now()
        self._instantiations += 1

    def end(self):
        self._endTime = datetime.now()
        if self._startTime is None:
            raise RuntimeError(f"Forgot to call begin() before end() on timer {self.name}!")
        self._elapsed_over_instantiations += self.elapsed()
    
    def is_valid(self):
        if self._startTime is None or self._endTime is None:
            return False
        return True

    def elapsed(self):
        return self._endTime - self._startTime

    def get_instantiations(self):
        return self._instantiations

    def get_total_time_over_instantiations(self):
        return self._elapsed_over_instantiations