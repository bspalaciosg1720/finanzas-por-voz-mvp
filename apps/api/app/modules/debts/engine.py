from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class DebtProjectionInput:
    id: str
    name: str
    balance_minor: int
    minimum_payment_minor: int
    annual_interest_rate_bps: int | None


@dataclass(frozen=True)
class DebtProjectionResult:
    id: str
    completion_month: int
    interest_minor: int


def payoff_order(debts: list[DebtProjectionInput], strategy: str) -> list[DebtProjectionInput]:
    if strategy == "snowball":
        return sorted(debts, key=lambda item: (item.balance_minor, item.name.lower()))
    if strategy == "hybrid":
        smallest = min(debts, key=lambda item: (item.balance_minor, item.name.lower()))
        remaining = [item for item in debts if item.id != smallest.id]
        return [
            smallest,
            *sorted(
                remaining,
                key=lambda item: (
                    item.annual_interest_rate_bps is None,
                    -(item.annual_interest_rate_bps or 0),
                    item.balance_minor,
                ),
            ),
        ]
    return sorted(
        debts,
        key=lambda item: (
            item.annual_interest_rate_bps is None,
            -(item.annual_interest_rate_bps or 0),
            item.balance_minor,
        ),
    )


def simulate_payoff(
    debts: list[DebtProjectionInput],
    *,
    strategy: str,
    extra_payment_minor: int,
    maximum_months: int = 1200,
) -> tuple[list[DebtProjectionResult], int, int] | None:
    if any(item.annual_interest_rate_bps is None for item in debts):
        return None
    ordered = payoff_order(debts, strategy)
    monthly_budget = sum(item.minimum_payment_minor for item in ordered) + extra_payment_minor
    balances = {item.id: item.balance_minor for item in ordered}
    interest_total = {item.id: 0 for item in ordered}
    completion: dict[str, int] = {}

    for month in range(1, maximum_months + 1):
        active = [item for item in ordered if balances[item.id] > 0]
        if not active:
            break
        for item in active:
            monthly_rate = Decimal(item.annual_interest_rate_bps or 0) / Decimal(120_000)
            interest = int(
                (Decimal(balances[item.id]) * monthly_rate).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
            balances[item.id] += interest
            interest_total[item.id] += interest

        target = active[0]
        remaining_budget = monthly_budget
        for item in active:
            payment = min(item.minimum_payment_minor, balances[item.id])
            balances[item.id] = max(0, balances[item.id] - payment)
            remaining_budget -= payment
            if balances[item.id] == 0:
                completion[item.id] = month

        if balances[target.id] > 0 and remaining_budget > 0:
            payment = min(remaining_budget, balances[target.id])
            balances[target.id] -= payment
            if balances[target.id] == 0:
                completion[target.id] = month

        if all(item.minimum_payment_minor <= 0 for item in active) and extra_payment_minor <= 0:
            return None
    else:
        return None

    results = [
        DebtProjectionResult(item.id, completion[item.id], interest_total[item.id])
        for item in ordered
    ]
    return results, max(completion.values(), default=0), sum(interest_total.values())
