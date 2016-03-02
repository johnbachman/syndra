import z3

import atomic_predicate
from datatypes import _ensure_variable, _ensure_string
from datatypes import Node, Variable, Model
from datatypes import new_graph, new_action, new_model
from solver import solver
import z3_helpers


# Predicate and its subclasses.

class Predicate(object):
    def __init__(self):
        raise NotImplementedError("Predicate is an abstract class.")

    def get_model(self):
        # returns a set of sets of <graph, action> pairs, or at the very least
        # something that behaves on the surface as such. It might not
        # necessarily be a complete set. Actions should also behave as sets
        # (sets of atomic actions).
        with solver.context():
            model = new_model()
            interpretation = z3.Function('interpretation', Variable, Node)
            self._assert(model, interpretation)
            if not solver.check():
                raise ValueError("Tried to get model of unsat predicate")
            return solver.model()
            # TODO: Change the form of this output so that it's what
            # my tests specified: sets, etc. Do that either here or in solver.

    def check_sat(self):
        # returns a boolean
        with solver.context():
            model = new_model()
            interpretation = z3.Function('interpretation', Variable, Node)
            self._assert(model, interpretation)
            return solver.check()

    def _assert(self, model, interpretation):
        # model is something representing a set of sets of pairs
        # this is only used privately, in check_sat and/or get_model
        raise NotImplementedError("Implement _assert in subclasses.")


class And(Predicate):
    """`AND` two L predicates together."""
    def __init__(self, *preds):
        self.p1, self.p2 = _multi_to_binary(preds, And)

    def _assert(self, model, i):
        g = new_graph('g')
        a = new_action('a')
        s = new_model('s')
        t = new_model('t')
        return z3.Exists([s, t], z3.ForAll([g, a],
                z3.And(self.p1._assert(s, i), self.p2._assert(t, i),
                    z3_helpers.Iff(f(g, a), z3.And(s(g, a), t(g, a))))))


class Or(Predicate):
    """`OR` two L predicates together."""
    def __init__(self, *preds):
        self.p1, self.p2 = _multi_to_binary(preds, Or)

    def _assert(self, model, i):
        g = new_graph('g')
        a = new_action('a')
        s = new_model('s')
        t = new_model('t')
        return z3.Exists([s, t], z3.ForAll([g, a],
                z3.And(self.p1._assert(s, i), self.p2._assert(t, i),
                    z3_helpers.Iff(f(g, a), z3.And(s(g, a), t(g, a))))))


class Join(Predicate):
    """`&` two L predicates together."""
    def __init__(self, *preds):
        self.p1, self.p2 = _multi_to_binary(preds, Join)

    def _assert(self, model, i):
        g = new_graph('g')
        a = new_action('a')
        s = new_model('s')
        t = new_model('t')

        def is_plus(alpha, beta, a):
            # Assert that alpha + beta = a. All of these are Actions.
            # This is defined in Definition 2 of the L paper, on page 5.
            # TODO: implement this once you have a clear API for Action.
            pass

        def is_join(f, s, t, g, a):
            # Assert that f behaves, on inputs g and a, like s "joined" with t.
            # "joined" is the |><| operator.
            alpha = Action('alpha')
            beta = Action('beta')
            return z3_helpers.Iff(f(g, a),
                       z3.Exists(alpha, beta),
                       z3.And(s(g, alpha), t(g, beta), is_plus(alpha, beta, a)))

        return z3.Exists([s, t], z3.ForAll([g, a],
                z3.And(self.p1._assert(s, i), self.p2._assert(t, i),
                    is_join(f, s, t, g, a))))


class DontKnow(Predicate):
    """`_V_` ("don't know" operator) two L predicates together."""
    def __init__(self, *preds):
        self.p1, self.p2 = _multi_to_binary(preds, DontKnow)

    def _assert(self, model, i):
        return z3.Or(self.p1._assert(model, i), self.p2._assert(model, i))


class Not(Predicate):
    """`NOT` an L predicate."""
    def __init__(self, pred):
        self.pred = pred

    def _assert(self, model, i):
        g = new_graph('g')
        a = new_action('a')
        s = new_model('s')
        return z3.Exists([s], z3.ForAll([g, a],
                z3.And(self.pred._assert(s, i),
                    z3_helpers.Iff(f(g, a), z3.Not(s(g, a))))))


class ForAll(Predicate):
    def __init__(self, var, p, *args):
        _ensure_predicate(p)
        _ensure_variable(var)
        self.pred = p
        self.var = var

    def _assert(self, model, i):
        return z3.ForAll([self.var], self.pred._assert(model, i))


class Exists(Predicate):
    def __init__(self, var, p, *args):
        _ensure_predicate(p)
        _ensure_variable(var)
        self.pred = p
        self.var = var

    def _assert(self, model, i):
        return z3.Exists([self.var], self.pred._assert(model, i))


def Implies(predicate1, predicate2):
    # Macro for an implies predicate
    _ensure_predicate(predicate1)
    _ensure_predicate(predicate2)
    output = Or(Not(predicate1), predicate2)
    assert isinstance(output, Predicate)
    return output


# Private helper functions.

def _multi_to_binary(preds, classref):
    assert len(preds) >= 2, ("Cannot apply %s to one predicate only" %
                             str(classref))
    for p in preds:
        _ensure_predicate(p)

    p1 = preds[0]
    if len(preds) == 2:
        p2 = preds[1]
    else:
        assert len(preds[1:]) >= 2
        p2 = classref(*preds[1:])

    return (p1, p2)


def _atomic_predicate_wrapper(atomic_predicate_classref):
    # Modify the interpretation of the atomic_predicate so that it
    # behaves as a predicate.
    # Each atomic_predicate implements its own _assert
    class NewClass(Predicate):
        def __init__(self, *args):
            self.atomic = atomic_predicate_classref(*args)

        def _assert(self, model, i):
            # model is a function from g,a to bool (as an array)
            g = new_graph('g')
            a = new_action('a')
            return z3.ForAll([g, a],
                    z3_helpers.Iff(z3.And(Model.pregraph(model) == g,
                                       Model.action(model) == a),
                                   self.atomic._assert(g, a)))

    return NewClass


# Atomic predicates. This sets the value of a bunch of variables, e.g. Top and
# Add, in this namespace.

for classname in ['Top', 'Bottom', 'Equal', 'PreLabeled', 'PostLabeled',
                  'PostParent', 'DoParent', 'PreLink', 'PostLink',
                  'PostUnlabeled', 'Named', 'PreParent', 'PreUnlabeled',
                  'DoLink', 'DoUnlink', 'PreHas', 'PostHas', 'Add', 'Rem']:
    classref = getattr(atomic_predicate, classname)
    new_classref = _atomic_predicate_wrapper(classref)
    new_classref.__name__ = classname
    globals()[classname] = new_classref


def _ensure_predicate(thing):
    """Raise ValueError if thing is not an instance of Predicate."""
    if not isinstance(thing, Predicate):
        raise ValueError("Argument must be instance of Predicate. Instead, got %s" % repr(thing))
