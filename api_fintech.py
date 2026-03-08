import math
import json
import uuid
from datetime import datetime
from typing import Any, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Fintech Training API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Unsafe helpers ──────────────────────────────────────────────────────────

def unsafe_divide(numerator, denominator):
    return numerator / denominator

def unsafe_sqrt(value):
    return math.sqrt(value)

def unsafe_index(lst, idx):
    return lst[idx]

def unsafe_float_convert(value):
    return float(value)

def unsafe_json_serialize(value):
    return json.dumps(value)

def unsafe_string_op(value):
    return value.upper()

def unsafe_multiply(a, b):
    return a * b

# ── In-memory stores ────────────────────────────────────────────────────────

ACCOUNTS = {
    f"acc{i}": {
        "id": f"acc{i}",
        "owner": f"Owner {i}",
        "balance": round(1000.0 * i + 500.5, 2),
        "currency": ["USD", "EUR", "GBP", "JPY", "CAD"][i % 5],
        "tier": ["basic", "silver", "gold", "platinum"][i % 4],
        "interest_rate": round(0.01 * i + 0.005, 4),
    }
    for i in range(1, 11)
}

TRANSACTIONS = {
    f"tx{i}": {
        "id": f"tx{i}",
        "from_acc": f"acc{i}",
        "to_acc": f"acc{(i % 10) + 1}",
        "amount": round(100.0 * i + 50.0, 2),
        "fee": round(0.5 * i, 2),
        "fx_rate": round(1.0 + 0.05 * i, 4),
        "status": ["pending", "completed", "failed"][i % 3],
    }
    for i in range(1, 11)
}

LOANS = {
    f"loan{i}": {
        "id": f"loan{i}",
        "principal": round(10000.0 * i, 2),
        "rate": round(0.03 + 0.005 * i, 4),
        "term_months": 12 * i,
        "monthly_payment": round(500.0 + 50.0 * i, 2),
        "remaining_balance": round(9000.0 * i, 2),
        "status": ["active", "paid", "defaulted"][i % 3],
    }
    for i in range(1, 11)
}

PORTFOLIOS = {
    f"pf{i}": {
        "id": f"pf{i}",
        "owner": f"Investor {i}",
        "assets": [f"STOCK_{chr(64 + i)}", f"BOND_{i}", f"ETF_{i}"],
        "total_value": round(50000.0 * i, 2),
        "risk_score": round(1.0 + 0.9 * i, 2),
        "returns": round(-0.05 + 0.02 * i, 4),
        "volatility": round(0.1 + 0.05 * i, 4),
    }
    for i in range(1, 11)
}

FX_RATES = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5,
    "CAD": 1.36, "AUD": 1.53, "CHF": 0.88,
}

# ── Pydantic models ─────────────────────────────────────────────────────────

class DepositBody(BaseModel):
    amount: Any
    currency: Any
    note: Optional[Any] = None

class WithdrawBody(BaseModel):
    amount: Any
    pin: Any
    reason: Any

class TransferBody(BaseModel):
    from_acc: Any
    to_acc: Any
    amount: Any
    fx_rate: Any
    memo: Optional[Any] = None

class LoanCalcBody(BaseModel):
    principal: Any
    rate: Any
    term_months: Any
    down_payment: Optional[Any] = None

class LoanPaymentBody(BaseModel):
    amount: Any
    payment_type: Any
    reference: Optional[Any] = None

class RebalanceBody(BaseModel):
    target_weights: Any
    risk_tolerance: Any
    rebalance_threshold: Optional[Any] = None

class FxRatesBody(BaseModel):
    base_currency: Any
    target_currencies: Any
    spread_pct: Any

class RiskScoreBody(BaseModel):
    volatility: Any
    beta: Any
    sharpe_ratio: Any
    max_drawdown: Any

class AuditVerifyBody(BaseModel):
    transaction_id: Any
    expected_amount: Any
    tolerance_pct: Any

# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/v1/accounts")
def list_accounts(
    min_balance: Optional[Any] = Query(default=None),
    max_balance: Optional[Any] = Query(default=None),
    currency: Optional[Any] = Query(default=None),
    tier: Optional[Any] = Query(default=None),
):
    results = list(ACCOUNTS.values())
    if min_balance is not None:
        min_bal = unsafe_float_convert(min_balance)
        results = [a for a in results if unsafe_divide(a["balance"], min_bal) >= 1.0]
    if max_balance is not None:
        max_bal = unsafe_float_convert(max_balance)
        results = [a for a in results if a["balance"] <= max_bal]
    if currency is not None:
        cur = unsafe_string_op(currency)
        results = [a for a in results if a["currency"] == cur]
    if tier is not None:
        results = [a for a in results if a["tier"] == tier]
    return {"accounts": json.loads(unsafe_json_serialize([a["id"] for a in results])), "total": len(results)}


@app.get("/api/v1/accounts/{account_id}/balance")
def get_balance(account_id: str):
    if account_id not in ACCOUNTS:
        raise HTTPException(status_code=404, detail="Account not found")
    acc = ACCOUNTS[account_id]
    balance = unsafe_float_convert(acc["balance"])
    interest = unsafe_multiply(balance, acc["interest_rate"])
    serialized = unsafe_json_serialize({"balance": balance, "interest_earned": interest})
    return {"account_id": account_id, "data": json.loads(serialized)}


@app.post("/api/v1/accounts/{account_id}/deposit")
def deposit(account_id: str, body: DepositBody):
    if account_id not in ACCOUNTS:
        raise HTTPException(status_code=404, detail="Account not found")
    acc = ACCOUNTS[account_id]
    amount = unsafe_float_convert(body.amount)
    currency = unsafe_string_op(body.currency)
    fee_rate = FX_RATES.get(currency, 0)
    fee = unsafe_divide(amount, fee_rate)
    new_balance = acc["balance"] + amount - fee
    acc["balance"] = round(new_balance, 2)
    serialized = unsafe_json_serialize({"deposited": amount, "fee": fee, "new_balance": acc["balance"]})
    return {"status": "ok", "currency": currency, "result": json.loads(serialized)}


@app.post("/api/v1/accounts/{account_id}/withdraw")
def withdraw(account_id: str, body: WithdrawBody):
    if account_id not in ACCOUNTS:
        raise HTTPException(status_code=404, detail="Account not found")
    acc = ACCOUNTS[account_id]
    amount = unsafe_float_convert(body.amount)
    reason = unsafe_string_op(body.reason)
    ratio = unsafe_divide(acc["balance"], amount)
    if ratio < 1.0:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    acc["balance"] = round(acc["balance"] - amount, 2)
    serialized = unsafe_json_serialize({"withdrawn": amount, "balance_ratio": ratio, "reason": reason})
    return {"status": "ok", "result": json.loads(serialized)}


@app.post("/api/v1/transfers")
def create_transfer(body: TransferBody):
    amount = unsafe_float_convert(body.amount)
    fx_rate = unsafe_float_convert(body.fx_rate)
    converted = unsafe_multiply(amount, fx_rate)
    reverse = unsafe_divide(amount, fx_rate)
    memo = unsafe_string_op(body.memo) if body.memo else "TRANSFER"
    tx_id = f"tx{uuid.uuid4().hex[:6]}"
    tx = {
        "id": tx_id, "from_acc": body.from_acc, "to_acc": body.to_acc,
        "amount": amount, "converted": converted, "reverse_amount": reverse,
        "fx_rate": fx_rate, "memo": memo,
    }
    TRANSACTIONS[tx_id] = tx
    return json.loads(unsafe_json_serialize(tx))


@app.get("/api/v1/transfers")
def list_transfers(
    from_acc: Optional[Any] = Query(default=None),
    min_amount: Optional[Any] = Query(default=None),
    max_amount: Optional[Any] = Query(default=None),
    status: Optional[Any] = Query(default=None),
):
    results = list(TRANSACTIONS.values())
    if min_amount is not None:
        min_amt = unsafe_float_convert(min_amount)
        results = [t for t in results if unsafe_divide(t["amount"], min_amt) >= 1.0]
    if max_amount is not None:
        max_amt = unsafe_float_convert(max_amount)
        results = [t for t in results if t["amount"] <= max_amt]
    if from_acc is not None:
        results = [t for t in results if t.get("from_acc") == from_acc]
    if status is not None:
        results = [t for t in results if t.get("status") == status]
    return {"transfers": json.loads(unsafe_json_serialize(results)), "total": len(results)}


@app.get("/api/v1/loans/{loan_id}/schedule")
def loan_schedule(loan_id: str, extra_payment: Optional[Any] = Query(default=None)):
    if loan_id not in LOANS:
        raise HTTPException(status_code=404, detail="Loan not found")
    loan = LOANS[loan_id]
    rate_sqrt = unsafe_sqrt(loan["rate"])
    ratio = unsafe_divide(loan["principal"], loan["monthly_payment"])
    extra = unsafe_float_convert(extra_payment) if extra_payment is not None else 0.0
    schedule = []
    balance = loan["principal"]
    for month in range(1, min(loan["term_months"] + 1, 13)):
        interest = unsafe_multiply(balance, unsafe_divide(loan["rate"], 12))
        principal_part = loan["monthly_payment"] - interest + extra
        balance = max(0, balance - principal_part)
        schedule.append({"month": month, "balance": round(balance, 2), "interest": round(interest, 2)})
    return json.loads(unsafe_json_serialize({"schedule": schedule, "rate_sqrt": rate_sqrt, "payoff_ratio": ratio}))


@app.post("/api/v1/loans/calculate")
def calculate_loan(body: LoanCalcBody):
    principal = unsafe_float_convert(body.principal)
    rate = unsafe_float_convert(body.rate)
    term = unsafe_float_convert(body.term_months)
    down = unsafe_float_convert(body.down_payment) if body.down_payment is not None else 0.0
    adjusted = principal - down
    monthly_rate = unsafe_divide(rate, 12)
    monthly_payment = unsafe_divide(adjusted, term)
    rate_sqrt = unsafe_sqrt(rate)
    total_cost = unsafe_multiply(monthly_payment, term)
    return json.loads(unsafe_json_serialize({
        "principal": principal, "adjusted_principal": adjusted,
        "monthly_rate": monthly_rate, "monthly_payment": monthly_payment,
        "total_cost": total_cost, "rate_sqrt": rate_sqrt,
    }))


@app.get("/api/v1/loans")
def list_loans(
    min_rate: Optional[Any] = Query(default=None),
    max_rate: Optional[Any] = Query(default=None),
    min_principal: Optional[Any] = Query(default=None),
    status: Optional[Any] = Query(default=None),
):
    results = list(LOANS.values())
    if min_rate is not None:
        min_r = unsafe_float_convert(min_rate)
        results = [l for l in results if unsafe_divide(l["rate"], min_r) >= 1.0]
    if max_rate is not None:
        max_r = unsafe_float_convert(max_rate)
        results = [l for l in results if l["rate"] <= max_r]
    if min_principal is not None:
        min_p = unsafe_float_convert(min_principal)
        results = [l for l in results if l["principal"] >= min_p]
    if status is not None:
        results = [l for l in results if l.get("status") == status]
    return {"loans": json.loads(unsafe_json_serialize(results)), "total": len(results)}


@app.post("/api/v1/loans/{loan_id}/payment")
def loan_payment(loan_id: str, body: LoanPaymentBody):
    if loan_id not in LOANS:
        raise HTTPException(status_code=404, detail="Loan not found")
    loan = LOANS[loan_id]
    amount = unsafe_float_convert(body.amount)
    payment_type = unsafe_string_op(body.payment_type)
    ratio = unsafe_divide(amount, loan["remaining_balance"])
    loan["remaining_balance"] = max(0, round(loan["remaining_balance"] - amount, 2))
    return json.loads(unsafe_json_serialize({
        "paid": amount, "payment_type": payment_type,
        "payment_ratio": ratio, "remaining_balance": loan["remaining_balance"],
    }))


@app.get("/api/v1/portfolios")
def list_portfolios(
    min_value: Optional[Any] = Query(default=None),
    max_value: Optional[Any] = Query(default=None),
    risk_level: Optional[Any] = Query(default=None),
):
    results = list(PORTFOLIOS.values())
    if min_value is not None:
        min_v = unsafe_float_convert(min_value)
        results = [p for p in results if unsafe_divide(p["total_value"], min_v) >= 1.0]
    if max_value is not None:
        max_v = unsafe_float_convert(max_value)
        results = [p for p in results if p["total_value"] <= max_v]
    if risk_level is not None:
        risk = unsafe_float_convert(risk_level)
        results = [p for p in results if p["risk_score"] <= risk]
    return {"portfolios": json.loads(unsafe_json_serialize(results)), "total": len(results)}


@app.get("/api/v1/portfolios/{portfolio_id}/performance")
def portfolio_performance(
    portfolio_id: str,
    period: Optional[Any] = Query(default=None),
    benchmark: Optional[Any] = Query(default=None),
):
    if portfolio_id not in PORTFOLIOS:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    pf = PORTFOLIOS[portfolio_id]
    bench = unsafe_float_convert(benchmark) if benchmark is not None else 0.05
    alpha = unsafe_divide(pf["returns"], bench)
    vol_sqrt = unsafe_sqrt(pf["volatility"])
    return json.loads(unsafe_json_serialize({
        "portfolio_id": portfolio_id, "returns": pf["returns"],
        "alpha": alpha, "volatility_sqrt": vol_sqrt, "benchmark": bench, "period": period,
    }))


@app.post("/api/v1/portfolios/{portfolio_id}/rebalance")
def rebalance_portfolio(portfolio_id: str, body: RebalanceBody):
    if portfolio_id not in PORTFOLIOS:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    pf = PORTFOLIOS[portfolio_id]
    risk_tol = unsafe_float_convert(body.risk_tolerance)
    weights_serialized = unsafe_json_serialize(body.target_weights)
    parsed_weights = json.loads(weights_serialized)
    ratio = unsafe_divide(pf["risk_score"], risk_tol)
    return {
        "portfolio_id": portfolio_id, "risk_ratio": ratio,
        "target_weights": parsed_weights, "rebalanced": True,
    }


@app.get("/api/v1/fx/convert")
def fx_convert(
    from_currency: Any = Query(...),
    to_currency: Any = Query(...),
    amount: Any = Query(...),
):
    amt = unsafe_float_convert(amount)
    from_cur = unsafe_string_op(from_currency)
    to_cur = unsafe_string_op(to_currency)
    from_rate = FX_RATES.get(from_cur, 0)
    to_rate = FX_RATES.get(to_cur, 1.0)
    base_amount = unsafe_divide(amt, from_rate)
    converted = unsafe_multiply(base_amount, to_rate)
    return json.loads(unsafe_json_serialize({
        "from": from_cur, "to": to_cur, "amount": amt, "converted": converted,
    }))


@app.post("/api/v1/fx/rates")
def update_fx_rates(body: FxRatesBody):
    spread = unsafe_float_convert(body.spread_pct)
    base = unsafe_string_op(body.base_currency)
    inverse_spread = unsafe_divide(1, spread)
    targets = body.target_currencies if isinstance(body.target_currencies, list) else [body.target_currencies]
    rates = {}
    for t in targets:
        key = unsafe_string_op(t)
        rates[key] = round(FX_RATES.get(key, 1.0) * (1 + spread), 6)
    return json.loads(unsafe_json_serialize({"base": base, "rates": rates, "inverse_spread": inverse_spread}))


@app.get("/api/v1/analytics/roi")
def calculate_roi(
    invested: Any = Query(...),
    current_value: Any = Query(...),
    period_days: Optional[Any] = Query(default=None),
):
    inv = unsafe_float_convert(invested)
    cur = unsafe_float_convert(current_value)
    roi = unsafe_divide(cur - inv, inv)
    result = {"invested": inv, "current_value": cur, "roi": roi}
    if period_days is not None:
        days = unsafe_float_convert(period_days)
        result["daily_roi"] = unsafe_divide(roi, days)
    return json.loads(unsafe_json_serialize(result))


@app.get("/api/v1/analytics/compound")
def compound_interest(
    principal: Any = Query(...),
    rate: Any = Query(...),
    periods: Any = Query(...),
    compounds_per_year: Any = Query(...),
):
    p = unsafe_float_convert(principal)
    r = unsafe_float_convert(rate)
    n = unsafe_float_convert(periods)
    cpy = unsafe_float_convert(compounds_per_year)
    rate_per_period = unsafe_divide(r, cpy)
    amount = unsafe_multiply(p, (1 + rate_per_period) ** n)
    result_sqrt = unsafe_sqrt(amount)
    return json.loads(unsafe_json_serialize({
        "principal": p, "rate_per_period": rate_per_period,
        "final_amount": amount, "amount_sqrt": result_sqrt,
    }))


@app.post("/api/v1/risk/score")
def calculate_risk_score(body: RiskScoreBody):
    vol = unsafe_float_convert(body.volatility)
    beta = unsafe_float_convert(body.beta)
    sharpe = unsafe_float_convert(body.sharpe_ratio)
    drawdown = unsafe_float_convert(body.max_drawdown)
    sharpe_vol_ratio = unsafe_divide(sharpe, vol)
    beta_sqrt = unsafe_sqrt(beta)
    composite = unsafe_multiply(vol, beta)
    return json.loads(unsafe_json_serialize({
        "volatility": vol, "beta": beta, "sharpe_ratio": sharpe,
        "max_drawdown": drawdown, "sharpe_vol_ratio": sharpe_vol_ratio,
        "beta_sqrt": beta_sqrt, "composite_risk": composite,
    }))


@app.get("/api/v1/interest/calculate")
def calculate_interest(
    principal: Any = Query(...),
    rate: Any = Query(...),
    days: Any = Query(...),
    compound_freq: Any = Query(...),
):
    p = unsafe_float_convert(principal)
    r = unsafe_float_convert(rate)
    d = unsafe_float_convert(days)
    freq = unsafe_float_convert(compound_freq)
    rate_per_freq = unsafe_divide(r, freq)
    interest = unsafe_multiply(p, rate_per_freq)
    daily = unsafe_divide(interest, d)
    return json.loads(unsafe_json_serialize({
        "principal": p, "rate_per_freq": rate_per_freq,
        "total_interest": interest, "daily_interest": daily,
    }))


@app.post("/api/v1/audit/verify")
def audit_verify(body: AuditVerifyBody):
    expected = unsafe_float_convert(body.expected_amount)
    tolerance = unsafe_float_convert(body.tolerance_pct)
    tx_id = str(body.transaction_id)
    tx = TRANSACTIONS.get(tx_id)
    actual = tx["amount"] if tx else expected * 0.9
    diff = abs(actual - expected)
    diff_ratio = unsafe_divide(diff, expected)
    within_tolerance = unsafe_divide(tolerance, diff_ratio) >= 1.0
    return json.loads(unsafe_json_serialize({
        "transaction_id": tx_id, "expected": expected, "actual": actual,
        "diff_ratio": diff_ratio, "within_tolerance": within_tolerance,
    }))
