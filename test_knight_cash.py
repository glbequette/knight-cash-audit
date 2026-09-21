"""Branch-focused tests for knight_cash_api.py."""

import pytest
from fastapi.testclient import TestClient

import knight_cash_api


@pytest.fixture(autouse=True)
def reset_balances():
    """Give every test an isolated copy of the original account data."""
    knight_cash_api.balances.clear()
    knight_cash_api.balances.update(knight_cash_api.INITIAL_BALANCES)
    yield
    knight_cash_api.balances.clear()
    knight_cash_api.balances.update(knight_cash_api.INITIAL_BALANCES)


@pytest.fixture
def client():
    return TestClient(knight_cash_api.app)


@pytest.fixture
def valid_transfer():
    return {
        "from_account": "arthur",
        "to_account": "lancelot",
        "amount": 125.50,
    }


def test_balance_happy_path(client):
    response = client.get("/balance/arthur")
    assert response.status_code == 200
    assert response.json() == {"account": "arthur", "balance": 1000.0}


def test_balance_normalizes_case_and_whitespace(client):
    response = client.get("/balance/%20ARTHUR%20")
    assert response.status_code == 200
    assert response.json()["balance"] == 1000.0


def test_balance_unknown_account(client):
    response = client.get("/balance/mordred")
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"


def test_transfer_happy_path(client, valid_transfer):
    response = client.post("/transfer", json=valid_transfer)
    assert response.status_code == 200
    assert response.json() == {
        "message": "Transfer successful",
        "from_account": "arthur",
        "to_account": "lancelot",
        "amount": 125.5,
        "from_balance": 874.5,
        "to_balance": 625.5,
    }

    assert client.get("/balance/arthur").json()["balance"] == 874.5
    assert client.get("/balance/lancelot").json()["balance"] == 625.5


def test_transfer_normalizes_account_names(client):
    response = client.post(
        "/transfer",
        json={
            "from_account": " ARTHUR ",
            "to_account": " Lancelot ",
            "amount": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["from_account"] == "arthur"
    assert response.json()["to_account"] == "lancelot"


@pytest.mark.parametrize("amount", [0, -0.01, -100])
def test_transfer_rejects_nonpositive_amounts_without_mutation(client, amount):
    before = knight_cash_api.balances.copy()
    response = client.post(
        "/transfer",
        json={
            "from_account": "arthur",
            "to_account": "lancelot",
            "amount": amount,
        },
    )
    assert response.status_code == 400
    assert "positive finite" in response.json()["detail"]
    assert knight_cash_api.balances == before


def test_transfer_rejects_nonfinite_amount_without_mutation(client):
    before = knight_cash_api.balances.copy()
    response = client.post(
        "/transfer",
        content=(
            '{"from_account":"arthur","to_account":"lancelot","amount":1e400}'
        ),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400
    assert knight_cash_api.balances == before


def test_transfer_rejects_insufficient_funds_without_mutation(client):
    before = knight_cash_api.balances.copy()
    response = client.post(
        "/transfer",
        json={
            "from_account": "lancelot",
            "to_account": "arthur",
            "amount": 500.01,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"
    assert knight_cash_api.balances == before


def test_transfer_allows_exact_available_balance(client):
    response = client.post(
        "/transfer",
        json={
            "from_account": "lancelot",
            "to_account": "guinevere",
            "amount": 500,
        },
    )
    assert response.status_code == 200
    assert response.json()["from_balance"] == 0
    assert response.json()["to_balance"] == 1250


def test_transfer_rejects_unknown_source(client):
    response = client.post(
        "/transfer",
        json={
            "from_account": "mordred",
            "to_account": "arthur",
            "amount": 10,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Source account not found"


def test_transfer_rejects_unknown_destination(client):
    response = client.post(
        "/transfer",
        json={
            "from_account": "arthur",
            "to_account": "mordred",
            "amount": 10,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Destination account not found"


def test_transfer_rejects_same_account_without_mutation(client):
    before = knight_cash_api.balances.copy()
    response = client.post(
        "/transfer",
        json={
            "from_account": "arthur",
            "to_account": " ARTHUR ",
            "amount": 10,
        },
    )
    assert response.status_code == 400
    assert "must be different" in response.json()["detail"]
    assert knight_cash_api.balances == before


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"from_account": "arthur", "to_account": "lancelot"},
        {"from_account": "arthur", "to_account": "lancelot", "amount": "abc"},
        {"from_account": None, "to_account": "lancelot", "amount": 10},
    ],
)
def test_transfer_rejects_malformed_requests(client, payload):
    before = knight_cash_api.balances.copy()
    response = client.post("/transfer", json=payload)
    assert response.status_code == 422
    assert knight_cash_api.balances == before

