from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Vulnerable Demo API")


# -----------------------
# Models
# -----------------------

class CalculateRequest(BaseModel):
    a: int
    b: int


class RegisterRequest(BaseModel):
    username: str
    password: str
    age: int


class TransferRequest(BaseModel):
    amount: float
    from_account: str
    to_account: str


# -----------------------
# Endpoints
# -----------------------

# 1️⃣ Division endpoint (Division by Zero vulnerability)
@app.post("/divide")
def divide(data: CalculateRequest):
    result = data.a / data.b  # ❌ No zero check
    return {"result": result}


# 2️⃣ Large factorial (Crash with big numbers)
@app.post("/factorial")
def factorial(data: CalculateRequest):
    def fact(n):
        if n == 0:
            return 1
        return n * fact(n - 1)  # ❌ No recursion limit protection

    return {"result": fact(data.a)}


# 3️⃣ Registration (No validation)
@app.post("/register")
def register(data: RegisterRequest):
    if len(data.password) < 3:
        raise ValueError("Password too short")  # ❌ Raises unhandled error

    return {
        "message": "User registered",
        "username": data.username
    }


# 4️⃣ Money transfer (Negative amount bug)
@app.post("/transfer")
def transfer(data: TransferRequest):
    # ❌ No negative validation
    new_balance = 1000 - data.amount
    return {
        "from": data.from_account,
        "to": data.to_account,
        "new_balance": new_balance
    }


# 5️⃣ Health check (Stable endpoint)
@app.get("/health")
def health():
    return {"status": "ok"}
