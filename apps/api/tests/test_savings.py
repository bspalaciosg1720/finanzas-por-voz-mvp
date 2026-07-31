from fastapi.testclient import TestClient
from tests.test_transactions import auth_headers, register


def add_goal(
    client: TestClient,
    auth: dict,
    *,
    name: str = "Viaje",
    target: int = 1_000_000,
    currency: str = "COP",
):
    return client.post(
        "/api/v1/savings-goals",
        headers=auth_headers(auth),
        json={
            "name": name,
            "target_amount_minor": target,
            "currency": currency,
            "target_date": "2027-01-15",
        },
    )


def contribute(client: TestClient, auth: dict, goal_id: str, amount: int):
    return client.post(
        f"/api/v1/savings-goals/{goal_id}/contributions",
        headers=auth_headers(auth),
        json={
            "amount_minor": amount,
            "contributed_at": "2026-07-30T12:00:00-05:00",
            "note": "Aporte mensual",
        },
    )


def test_goal_progress_completion_and_contribution_removal(client: TestClient) -> None:
    auth = register(client, "savings-progress@example.com")
    goal_id = add_goal(client, auth).json()["id"]
    first = contribute(client, auth, goal_id, 400_000)
    second = contribute(client, auth, goal_id, 600_000)
    assert first.status_code == 201
    assert second.status_code == 201

    goal = client.get(
        "/api/v1/savings-goals",
        headers=auth_headers(auth),
    ).json()[0]
    assert goal["saved_amount_minor"] == 1_000_000
    assert goal["progress_percent"] == 100.0
    assert goal["status"] == "completed"
    assert len(goal["contributions"]) == 2

    deleted = client.delete(
        f"/api/v1/savings-goals/{goal_id}/contributions/{second.json()['id']}",
        headers=auth_headers(auth),
    )
    assert deleted.status_code == 204
    updated = client.get(
        "/api/v1/savings-goals",
        headers=auth_headers(auth),
    ).json()[0]
    assert updated["saved_amount_minor"] == 400_000
    assert updated["status"] == "active"


def test_goal_edit_archive_validation_and_default_currency(client: TestClient) -> None:
    auth = register(client, "savings-lifecycle@example.com")
    assert add_goal(client, auth, target=0).status_code == 422
    assert add_goal(client, auth, currency="USD").status_code == 422
    goal_id = add_goal(client, auth, name="Computador").json()["id"]

    assert (
        client.patch(
            f"/api/v1/savings-goals/{goal_id}",
            headers=auth_headers(auth),
            json={
                "name": "Portátil",
                "target_amount_minor": 2_000_000,
                "target_date": None,
            },
        ).status_code
        == 204
    )
    goal = client.get(
        "/api/v1/savings-goals",
        headers=auth_headers(auth),
    ).json()[0]
    assert goal["name"] == "Portátil"
    assert goal["target_date"] is None

    assert (
        client.delete(
            f"/api/v1/savings-goals/{goal_id}",
            headers=auth_headers(auth),
        ).status_code
        == 204
    )
    assert (
        client.get("/api/v1/savings-goals", headers=auth_headers(auth)).json()
        == []
    )


def test_goals_and_contributions_are_isolated_between_users(
    client: TestClient,
) -> None:
    owner = register(client, "savings-owner@example.com")
    other = register(client, "savings-other@example.com")
    goal_id = add_goal(client, owner).json()["id"]

    assert contribute(client, other, goal_id, 100_000).status_code == 404
    assert (
        client.patch(
            f"/api/v1/savings-goals/{goal_id}",
            headers=auth_headers(other),
            json={"name": "Ajena"},
        ).status_code
        == 404
    )
    assert (
        client.get("/api/v1/savings-goals", headers=auth_headers(other)).json()
        == []
    )
