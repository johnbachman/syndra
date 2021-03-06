"""
Global Z3 solver for use by other files.
"""

from contextlib import contextmanager
from z3 import Solver


class MySolver(object):

    def __init__(self):
        self._solver = Solver()
        # TODO: Initialize datatypes here

    # TODO: Port the below functions to here as methods

    def push(self):
        """Push solver state."""
        self._solver.push()

    def pop(self):
        """Pop solver state."""
        self._solver.pop()

    def add(self, assertion):
        """Add an assertion to the solver state.

        Arguments:
            assertion : Z3-friendly predicate or boolean
        """
        return self._solver.add(assertion)

    def model(self):
        """Return a model for the current solver state.

        Returns:
            : Z3 model. TODO: Modify this all so that it returns sets, etc.
        """
        return self._solver.model()

    def check(self):
        """Check satisfiability of current satisfiability state.

        Returns:
            : boolean -- True if sat, False if unsat
        """
        # check() returns either unsat or sat
        # sat.r is 1, unsat.r is -1
        return self._solver.check().r > 0

    @contextmanager
    def context(self):
        """To do something in between a push and a pop, use a `with context()`."""
        self.push()
        yield
        self.pop()

    def quick_check(self, assertion):
        """Add an assertion only temporarily, and check sat."""
        with self.context():
            self.add(assertion)
            return self.check()


solver = MySolver()
