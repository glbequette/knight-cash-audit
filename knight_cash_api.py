"""Knight Cash API with defensive validation for account transfers."""

from math import isfinite

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Knight Cash API")

INITIAL_BALANCES = {
    "arthur": 1000.00,
    "lancelot": 500.00,
    "guinevere": 750.00,
}

# This in-memory store is intentionally simple for the testing assignment.
balances = INITIAL_BALANCES.copy()


class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float


@app.get("/balance/{account}")
def get_balance(account: str) -> dict[str, str | float]:
    """Return an account's current balance."""
    account_key = account.strip().lower()
    if account_key not in balances:
        raise HTTPException(status_code=404, detail="Account not found")

    return {"account": account_key, "balance": balances[account_key]}


@app.post("/transfer")
def transfer(request: TransferRequest) -> dict[str, str | float]:
    """Atomically transfer a positive, finite amount between two accounts."""
    source = request.from_account.strip().lower()
    destination = request.to_account.strip().lower()

    if source not in balances:
        raise HTTPException(status_code=404, detail="Source account not found")
    if destination not in balances:
        raise HTTPException(status_code=404, detail="Destination account not found")
    if source == destination:
        raise HTTPException(
            status_code=400,
            detail="Source and destination accounts must be different",
        )
    if not isfinite(request.amount) or request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Transfer amount must be a positive finite number",
        )
    if request.amount > balances[source]:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    balances[source] -= request.amount
    balances[destination] += request.amount

    return {
        "message": "Transfer successful",
        "from_account": source,
        "to_account": destination,
        "amount": request.amount,
        "from_balance": balances[source],
        "to_balance": balances[destination],
    }

