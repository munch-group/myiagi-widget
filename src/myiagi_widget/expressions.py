"""Random Python expression generator for the myiagi trainer.

Builds an ``Expression`` node tree out of the demo variables in
``controls.py``, biased by the per-course-week ``topic_probs``, and
stringifies it -- ``app.py`` then feeds the string to
``steps_widget.steps._steps()`` to get the step-by-step trace the student must
reconstruct. Ported near-verbatim from bp-help's ``text_gui.py``.
"""

import random
from typing import Optional

# The demo variables (foo, bar, baz, ..., accounts, records) must live in
# *this* module's globals() -- randomExpression()/_randomExpression() below
# resolve them via bare eval()/globals()[name] lookups, which always operate
# on the globals() of the module the code is running in.
from .controls import *  # noqa: F401,F403


class Expression:
    pass

class NumberLiteral(Expression):
    def __init__(self, num):
        self.num = num

    def __str__(self):
        return str(self.num)

class Number(Expression):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)

class String(Expression):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)

class List(Expression):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)

class Dict(Expression):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)

class GetIndexExpression(Expression):
    def __init__(self, name, i):
        self.name = name
        self.i = i

    def __str__(self):
        return str(self.name) + '[' + str(self.i) + ']'

class NoArgMethodExpression(Expression):
    def __init__(self, name, method):
        self.name = name
        self.method = method

    def __str__(self):
        return str(self.name) + f'.{self.method}()'

class ArgMethodExpression(Expression):
    def __init__(self, name, method, arg):
        self.name = name
        self.method = method
        self.arg = arg

    def __str__(self):
        return str(self.name) + f'.{self.method}({self.arg})'

class GetValueKeyExpression(Expression):
    def __init__(self, name, key):
        self.name = name
        self.key = key

    def __str__(self):
        return str(self.name) + '[' + repr(self.key) + ']'

class GetVariableKeyExpression(Expression):
    def __init__(self, name, key):
        self.name = name
        self.key = key

    def __str__(self):
        return str(self.name) + '[' + self.key + ']'

class SliceFrontExpression(Expression):
    def __init__(self, name, i):
        self.name = name
        self.i = i

    def __str__(self):
        return str(self.name) + '[:' + str(self.i) + ']'

class SliceExpression(Expression):
    def __init__(self, name, i, j):
        self.name = name
        self.i = i
        self.j = j

    def __str__(self):
        return str(self.name) + '[' + str(self.i) + ':' + str(self.j) + ']'

class SliceBackExpression(Expression):
    def __init__(self, name, i):
        self.name = name
        self.i = i

    def __str__(self):
        return str(self.name) + '[' + str(self.i) + ':]'

class BinaryExpression(Expression):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __str__(self):
        return str(self.left) + " " + self.op + " " + str(self.right)

class NotExpression(Expression):
    def __init__(self, left):
        self.left = left

    def __str__(self):
        return "not " + str(self.left)

class ParenthesizedExpression(Expression):
    def __init__(self, exp):
        self.exp = exp

    def __str__(self):
        return "(" + str(self.exp) + ")"

class FunctionExpression(Expression):
    def __init__(self, exp, fun):
        self.exp = exp
        self.fun = fun

    def __str__(self):
        return self.fun + "(" + str(self.exp) + ")"


def find_variable_for_key(keys: list, variables: list) -> Optional[str]:
    vars = []
    for var in variables:
        val = globals()[var]
        if val in keys:
            vars.append(var)
    if vars:
        return random.choice(vars)
    else:
        return None


def find_variable_for_index(indices: list[int], variables: list[str]) -> Optional[str]:
    vars = []
    for var in variables:
        val = globals()[var]
        if val in indices:
            vars.append(var)
    if vars:
        return random.choice(vars)
    else:
        return None


def get_expression(prob: float, leaf_prob: float, topic_probs: dict) -> str:
    """Build a random expression tree and stringify it.

    ``prob``/``leaf_prob``/``topic_probs`` come from ``controls.py``'s
    per-course-week difficulty ramp -- see ``app.py``'s ``next_expression()``
    for how the result is fed to ``steps_widget.steps._steps()``.
    """
    return str(randomExpression(prob, leaf_prob, topic_probs))


def randomExpression(prob, leaf_prob, topic_probs):
    """Retry ``_randomExpression`` until it yields a syntactically valid,
    evaluable expression -- to make sure all sub expressions are valid."""
    expr = _randomExpression(prob, leaf_prob, topic_probs)
    # TODO: find bugs instead of try/except hack...
    for x in range(100):
        try:
            eval(str(expr))
        except Exception:
            expr = _randomExpression(prob, leaf_prob, topic_probs)
            continue
        break
    return expr


def _randomExpression(prob, leaf_prob, topic_probs):

    p = random.random()

    if leaf_prob > prob:
        # variable or number
        random.random()
        if topic_probs['types']['dicts'] > p:
            d = Dict(random.choice(dicts))
            keys = list(globals()[d.name].keys())
            variable_key = find_variable_for_key(keys, strings + numbers)
            if variable_key and random.random() > 0.3:
                return GetVariableKeyExpression(d.name, variable_key)
            else:
                key = random.choice(keys)
                return GetValueKeyExpression(d.name, key)
        elif topic_probs['types']['lists'] > p:
            sl = Dict(random.choice(lists))
            i = random.randint(0, len(globals()[sl.name]) - 1)
            j = random.randint(i, len(globals()[sl.name]) - 1)
            variable_idx = find_variable_for_key([i], numbers)
            if variable_idx:
                i = variable_idx
            variable_idx = find_variable_for_key([j], numbers)
            if variable_idx:
                j = variable_idx
            if random.random() > 0.7:
                # list indexing
                return GetIndexExpression(sl, i)
            elif random.random() > 0.5:
                # list slicing
                return SliceFrontExpression(sl, i)
            elif random.random() > 0.3:
                # list slicing
                return SliceBackExpression(sl, i)
            else:
                # list slicing
                return SliceExpression(sl, i, j)
        elif topic_probs['types']['strings'] > p:
            sl = Dict(random.choice(strings))
            i = random.randint(0, len(globals()[sl.name]) - 1)
            j = random.randint(i, len(globals()[sl.name]) - 1)
            variable_idx = find_variable_for_key([i], numbers)
            if variable_idx:
                i = variable_idx
            variable_idx = find_variable_for_key([j], numbers)
            if variable_idx:
                j = variable_idx
            if random.random() > 0.7:
                method = random.choice(['upper', 'isdigit', 'lower'])
                return NoArgMethodExpression(sl, method)
            if random.random() > 0.6:
                for _ in range(100):
                    arg = random.choice(lists)
                    if all(type(x) is str for x in arg):
                        break
                method = random.choice(['join'])
                return ArgMethodExpression(sl, method, arg)
            elif random.random() > 0.3:
                # string indexing
                return GetIndexExpression(sl, i)
            elif random.random() > 0.2:
                # string slicing
                return SliceFrontExpression(sl, i)
            elif random.random() > 0.1:
                # string slicing
                return SliceBackExpression(sl, i)
            else:
                # string slicing
                return SliceExpression(sl, i, j)
        elif topic_probs['types']['number'] > p:
            return Number(random.choice(numbers))
        else:
            return NumberLiteral(random.randint(1, 3))
    else:
        left = randomExpression(prob / 1.2, leaf_prob, topic_probs)
        if type(left) is GetIndexExpression and type(eval(str(left))) is list:
            # nested list
            return GetIndexExpression(left, random.randint(0, len(eval(str(left))) - 1))
        elif type(left) is GetValueKeyExpression and type(eval(str(left))) is dict:
            # nested dict
            keys = list(eval(str(left)).keys())
            variable_key = find_variable_for_key(keys, strings + numbers)
            if variable_key:
                return GetVariableKeyExpression(left, variable_key)
            else:
                key = random.choice(keys)
                return GetValueKeyExpression(left, key)
        elif topic_probs['operations']['parentheses'] > p:
            # parentheses
            if type(left) is BinaryExpression:
                return ParenthesizedExpression(left)
            else:
                return left
        elif topic_probs['operations']['abs'] > p:
            # abs function
            if type(eval(str(left))) in [int, float]:
                return FunctionExpression(left, 'abs')
            else:
                return left
        elif topic_probs['operations']['len'] > p:
            # len function
            if type(eval(str(left))) in [str, list, dict]:
                return FunctionExpression(left, 'len')
            else:
                return left
        elif topic_probs['operations']['sorted'] > p:
            # sorted function
            if type(eval(str(left))) in [list]:
                return FunctionExpression(left, 'sorted')
            else:
                return left
        elif topic_probs['operations']['list'] > p:
            # list function
            if type(eval(str(left))) in [str]:
                return FunctionExpression(left, 'list')
            else:
                return left
        elif topic_probs['operations']['not_op'] > p:
            # not
            if type(left) is not NotExpression:
                return NotExpression(left)
            else:
                return left
        elif topic_probs['operations']['logic_op'] > p:
            # logic operator
            right = randomExpression(prob / 1.2, leaf_prob, topic_probs)
            operators = ['>', '<', '>=', '<=', '==', '>', 'and', 'or']
            weights = [2, 2, 2, 2, 2, 2, 1, 1]
            for x in range(100):
                op = random.choices(operators, weights=weights)[0]
                expr = BinaryExpression(left, op, right)
                try:
                    eval(str(expr))
                except Exception:
                    continue
                break
            return expr
        else:
            # arithmetic operator
            right = randomExpression(prob / 1.2, leaf_prob, topic_probs)
            operators = ["+", "-", "*", "/", "//", "%"]
            weights = [5, 5, 2, 2, 1, 1]
            for x in range(100):
                op = random.choices(operators, weights=weights)[0]
                expr = BinaryExpression(left, op, right)
                try:
                    eval(str(expr))
                except Exception:
                    continue
                break
            return expr
