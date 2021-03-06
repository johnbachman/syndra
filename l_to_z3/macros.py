from predicate import PreLabeled, PreUnlabeled, Named, PostLabeled, And, Implies, ForAll
from datatypes import new_variable

from labels import ACTIVE, PHOSPHORYLATED

def directly_phosphorylates(name_a, name_b):
    """
    Macro for '"A" phosphorylates "B"'.
    """
    A = new_variable(nickname=name_a)
    B = new_variable(nickname=name_b)
    return ForAll(A, ForAll(B,
               Implies(Named(A, name_a), Implies(Named(B, name_b),
                   And(PreLabeled(A, ACTIVE),
                       PreUnlabeled(B, PHOSPHORYLATED),
                       PostLabeled(A, ACTIVE),
                       PostLabeled(B, PHOSPHORYLATED))))))

# n.b.: there is an INDRA statement for this -- posttranslational modification 
def phosphorylated_is_active(name_b):
    """
    Macro for 'phosphorylated "B" is active'.
    """
    B = new_variable(nickname=name_b)
    return ForAll(B, Implies(Named(B, name_b),
               And(Implies(PreLabeled(B, PHOSPHORYLATED),
                           PreLabeled(B, ACTIVE)),
                   Implies(PostLabeled(B, PHOSPHORYLATED),
                           PostLabeled(B, ACTIVE)))))

# n.b.: this is ActivityActivity
def directly_activates(name _a, name_b):
    """
    Macro for '"A" activates "B"'.
    """
    A = new_variable(nickname=name_a)
    B = new_variable(nickname=name_b)
    return ForAll(A, ForAll(B,
               Implies(Named(A, name_a), Implies(Named(B, name_b),
                   And(PreLabeled(A, ACTIVE),
                       PreUnlabeled(B, ACTIVE),
                       PostLabeled(A, ACTIVE),
                       PostLabeled(B, ACTIVE))))))

# Other things: more specific phosphorylation (serine-phosphorylated;
# serine-phosphorylated-at). Can prove theorems about this. 

# Other theorems to prove: can't have phosphorylated_is_active and not
# phosphorylated_is_active.

# Use cases for reductions (from transitive closure to minimal set of rules)
# Use cases for inconsistency of rules with each other
# Link to INDRA statements
