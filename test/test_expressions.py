"""Headless tests for the random expression generator.

``randomExpression``/``_randomExpression`` resolve the demo variables
(``foo``, ``accounts``, ...) via bare ``eval()``/``globals()[name]`` lookups
against ``myiagi_widget.expressions``'s own module globals (populated by its
``from .controls import *``) -- so these tests just call the public functions
and check the resulting strings, rather than poking at module globals
directly.
"""
import pytest

from myiagi_widget import expressions as expr_module
from myiagi_widget.expressions import (
    BinaryExpression,
    FunctionExpression,
    GetIndexExpression,
    GetValueKeyExpression,
    NotExpression,
    NumberLiteral,
    ParenthesizedExpression,
    get_expression,
    randomExpression,
)


def test_number_literal_str():
    assert str(NumberLiteral(3)) == "3"


def test_get_index_expression_str():
    assert str(GetIndexExpression("order", 2)) == "order[2]"


def test_get_value_key_expression_str_reprs_the_key():
    # repr() so string keys come out quoted (accounts[1] vs records['Ib'])
    assert str(GetValueKeyExpression("records", "Ib")) == "records['Ib']"
    assert str(GetValueKeyExpression("accounts", 1)) == "accounts[1]"


def test_binary_expression_str():
    e = BinaryExpression(NumberLiteral(1), "+", NumberLiteral(2))
    assert str(e) == "1 + 2"


def test_not_expression_str():
    assert str(NotExpression(NumberLiteral(1))) == "not 1"


def test_function_expression_str():
    assert str(FunctionExpression(NumberLiteral(3), "abs")) == "abs(3)"


def test_parenthesized_expression_str():
    e = BinaryExpression(NumberLiteral(1), "+", NumberLiteral(2))
    assert str(ParenthesizedExpression(e)) == "(1 + 2)"


# A generous topic_probs that exercises every branch (dicts/lists/strings,
# every operation) at roughly week-15 (end of course) difficulty.
_FULL_TOPIC_PROBS = expr_module.topic_probs


@pytest.mark.parametrize("leaf_prob", [0.8, 0.66, 0.6])
def test_get_expression_produces_evaluable_python(leaf_prob):
    for _ in range(50):
        code = get_expression(1, leaf_prob=leaf_prob, topic_probs=_FULL_TOPIC_PROBS)
        assert isinstance(code, str)
        assert code
        # must be valid, side-effect-free Python that evaluates against the
        # demo variables synced into this module's globals()
        eval(code, vars(expr_module))


def test_random_expression_returns_expression_instance():
    e = randomExpression(1, leaf_prob=0.6, topic_probs=_FULL_TOPIC_PROBS)
    assert isinstance(e, expr_module.Expression)
    # str(e) must round-trip through eval() -- randomExpression()'s own
    # retry loop already guarantees this, this just pins the contract.
    eval(str(e), vars(expr_module))
