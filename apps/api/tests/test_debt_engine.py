from app.modules.debts.engine import DebtProjectionInput, payoff_order, simulate_payoff

DEBTS = [
    DebtProjectionInput("a", "Tarjeta", 1_000_000, 100_000, 2400),
    DebtProjectionInput("b", "Préstamo", 500_000, 50_000, 1200),
]


def test_snowball_and_avalanche_have_deterministic_order():
    assert [item.id for item in payoff_order(DEBTS, "snowball")] == ["b", "a"]
    assert [item.id for item in payoff_order(DEBTS, "avalanche")] == ["a", "b"]
    assert [item.id for item in payoff_order(DEBTS, "hybrid")] == ["b", "a"]


def test_projection_calculates_months_and_interest():
    result = simulate_payoff(DEBTS, strategy="avalanche", extra_payment_minor=100_000)
    assert result is not None
    debts, months, interest = result
    assert months > 0
    assert interest > 0
    assert all(item.completion_month <= months for item in debts)


def test_projection_refuses_to_invent_missing_interest_rate():
    unknown = [DebtProjectionInput("a", "Tarjeta", 100_000, 20_000, None)]
    assert simulate_payoff(unknown, strategy="snowball", extra_payment_minor=0) is None
