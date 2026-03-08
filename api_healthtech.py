import math
import json
import uuid
from datetime import datetime
from typing import Any, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="HealthTech Training API", version="1.0.0")

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

PATIENTS = {
    f"pt{i}": {
        "id": f"pt{i}",
        "name": f"Patient {i}",
        "age": 20 + i * 4,
        "weight_kg": round(55.0 + i * 3.5, 1),
        "height_cm": round(155.0 + i * 2.0, 1),
        "blood_pressure": f"{110 + i * 3}/{70 + i * 2}",
        "heart_rate": 60 + i * 3,
        "blood_type": ["A+", "B+", "O+", "AB+", "A-", "B-", "O-", "AB-"][i % 8],
    }
    for i in range(1, 11)
}

PRESCRIPTIONS = {
    f"rx{i}": {
        "id": f"rx{i}",
        "patient_id": f"pt{i}",
        "drug": ["Metformin", "Lisinopril", "Atorvastatin", "Omeprazole", "Amlodipine"][i % 5],
        "dosage_mg": round(50.0 * i, 1),
        "frequency_per_day": (i % 3) + 1,
        "duration_days": 7 * i,
    }
    for i in range(1, 11)
}

LABS = {
    f"lab{i}": {
        "id": f"lab{i}",
        "patient_id": f"pt{i}",
        "test_name": ["HbA1c", "Cholesterol", "Creatinine", "TSH", "Hemoglobin"][i % 5],
        "value": round(3.0 + i * 1.2, 2),
        "unit": ["%", "mg/dL", "mg/dL", "mIU/L", "g/dL"][i % 5],
        "reference_min": round(1.5 + i * 0.3, 2),
        "reference_max": round(8.0 + i * 0.5, 2),
    }
    for i in range(1, 11)
}

APPOINTMENTS = {
    f"apt{i}": {
        "id": f"apt{i}",
        "patient_id": f"pt{i}",
        "doctor": f"Dr. Smith {i}",
        "duration_mins": 15 + i * 5,
        "cost": round(80.0 + i * 20.0, 2),
        "room": 100 + i,
    }
    for i in range(1, 11)
}

# ── Pydantic models ─────────────────────────────────────────────────────────

class VitalsBody(BaseModel):
    heart_rate: Any
    systolic: Any
    diastolic: Any
    temperature: Any
    o2_saturation: Any

class PrescriptionBody(BaseModel):
    patient_id: Any
    drug: Any
    dosage_mg: Any
    frequency_per_day: Any
    duration_days: Any
    weight_kg: Any

class DosageCalcBody(BaseModel):
    weight_kg: Any
    drug_class: Any
    concentration_mg_per_ml: Any
    target_dose_mg_per_kg: Any

class LabAnalyzeBody(BaseModel):
    patient_id: Any
    values: Any
    weights: Any
    threshold: Any

class AppointmentBody(BaseModel):
    patient_id: Any
    doctor: Any
    duration_mins: Any
    cost: Any
    room: Any

class NutritionCalcBody(BaseModel):
    weight_kg: Any
    height_cm: Any
    age: Any
    activity_factor: Any
    goal: Any

class ImagingBody(BaseModel):
    scan_type: Any
    pixel_density: Any
    contrast_ratio: Any
    slice_thickness: Any

class TrialEnrollBody(BaseModel):
    patient_id: Any
    trial_id: Any
    eligibility_score: Any
    baseline_value: Any
    control_group: Any

class InsuranceBillingBody(BaseModel):
    procedure_code: Any
    base_cost: Any
    coverage_pct: Any
    deductible: Any
    copay_pct: Any

# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/v1/patients")
def list_patients(
    min_age: Optional[Any] = Query(default=None),
    max_age: Optional[Any] = Query(default=None),
    min_weight: Optional[Any] = Query(default=None),
    blood_type: Optional[Any] = Query(default=None),
):
    results = list(PATIENTS.values())
    if min_age is not None:
        min_a = unsafe_float_convert(min_age)
        results = [p for p in results if unsafe_divide(p["age"], min_a) >= 1.0]
    if max_age is not None:
        max_a = unsafe_float_convert(max_age)
        results = [p for p in results if p["age"] <= max_a]
    if min_weight is not None:
        min_w = unsafe_float_convert(min_weight)
        results = [p for p in results if p["weight_kg"] >= min_w]
    if blood_type is not None:
        results = [p for p in results if p["blood_type"] == blood_type]
    return {"patients": json.loads(unsafe_json_serialize([p["id"] for p in results])), "total": len(results)}


@app.get("/api/v1/patients/{patient_id}/bmi")
def get_bmi(patient_id: str):
    if patient_id not in PATIENTS:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient = PATIENTS[patient_id]
    height_m = unsafe_divide(patient["height_cm"], 100)
    height_m_sq = unsafe_multiply(height_m, height_m)
    bmi = unsafe_divide(patient["weight_kg"], height_m_sq)
    height_sqrt = unsafe_sqrt(patient["height_cm"])
    category = "underweight" if bmi < 18.5 else "normal" if bmi < 25 else "overweight" if bmi < 30 else "obese"
    return json.loads(unsafe_json_serialize({
        "patient_id": patient_id, "bmi": round(bmi, 2),
        "category": category, "height_sqrt": height_sqrt,
    }))


@app.post("/api/v1/patients/{patient_id}/vitals")
def record_vitals(patient_id: str, body: VitalsBody):
    if patient_id not in PATIENTS:
        raise HTTPException(status_code=404, detail="Patient not found")
    hr = unsafe_float_convert(body.heart_rate)
    systolic = unsafe_float_convert(body.systolic)
    diastolic = unsafe_float_convert(body.diastolic)
    temp = unsafe_float_convert(body.temperature)
    o2 = unsafe_float_convert(body.o2_saturation)
    bp_ratio = unsafe_divide(systolic, diastolic)
    PATIENTS[patient_id]["heart_rate"] = int(hr)
    PATIENTS[patient_id]["blood_pressure"] = f"{int(systolic)}/{int(diastolic)}"
    return json.loads(unsafe_json_serialize({
        "patient_id": patient_id, "heart_rate": hr, "systolic": systolic,
        "diastolic": diastolic, "bp_ratio": bp_ratio, "temperature": temp, "o2_saturation": o2,
    }))


@app.get("/api/v1/patients/{patient_id}/risk")
def patient_risk(
    patient_id: str,
    age_weight: Optional[Any] = Query(default=None),
    history_factor: Optional[Any] = Query(default=None),
):
    if patient_id not in PATIENTS:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient = PATIENTS[patient_id]
    aw = unsafe_float_convert(age_weight) if age_weight is not None else 1.0
    hf = unsafe_float_convert(history_factor) if history_factor is not None else 1.0
    hr_risk = unsafe_divide(patient["heart_rate"], aw)
    hf_sqrt = unsafe_sqrt(hf)
    risk_score = unsafe_multiply(hr_risk, hf_sqrt)
    return json.loads(unsafe_json_serialize({
        "patient_id": patient_id, "hr_risk": hr_risk,
        "history_sqrt": hf_sqrt, "composite_risk": risk_score,
    }))


@app.post("/api/v1/prescriptions")
def create_prescription(body: PrescriptionBody):
    if body.patient_id not in PATIENTS:
        raise HTTPException(status_code=404, detail="Patient not found")
    dosage = unsafe_float_convert(body.dosage_mg)
    weight = unsafe_float_convert(body.weight_kg)
    freq = unsafe_float_convert(body.frequency_per_day)
    drug = unsafe_string_op(body.drug)
    dose_per_kg = unsafe_divide(dosage, weight)
    daily_dose = unsafe_multiply(dosage, freq)
    rx_id = f"rx{uuid.uuid4().hex[:6]}"
    rx = {
        "id": rx_id, "patient_id": body.patient_id, "drug": drug,
        "dosage_mg": dosage, "frequency_per_day": int(freq),
        "duration_days": int(body.duration_days), "dose_per_kg": dose_per_kg, "daily_dose": daily_dose,
    }
    PRESCRIPTIONS[rx_id] = rx
    return json.loads(unsafe_json_serialize(rx))


@app.get("/api/v1/prescriptions/{rx_id}/schedule")
def prescription_schedule(rx_id: str, start_offset_days: Optional[Any] = Query(default=None)):
    if rx_id not in PRESCRIPTIONS:
        raise HTTPException(status_code=404, detail="Prescription not found")
    rx = PRESCRIPTIONS[rx_id]
    offset = unsafe_float_convert(start_offset_days) if start_offset_days is not None else 0.0
    doses_per_day = rx["frequency_per_day"]
    total_doses = unsafe_multiply(rx["duration_days"], doses_per_day)
    interval_hours = unsafe_divide(24, doses_per_day)
    schedule = [
        {"day": d + int(offset) + 1, "doses": doses_per_day, "interval_hours": interval_hours}
        for d in range(min(rx["duration_days"], 7))
    ]
    return json.loads(unsafe_json_serialize({
        "rx_id": rx_id, "total_doses": total_doses,
        "interval_hours": interval_hours, "schedule": schedule,
    }))


@app.post("/api/v1/dosage/calculate")
def calculate_dosage(body: DosageCalcBody):
    weight = unsafe_float_convert(body.weight_kg)
    concentration = unsafe_float_convert(body.concentration_mg_per_ml)
    target_dose = unsafe_float_convert(body.target_dose_mg_per_kg)
    drug_class = unsafe_string_op(body.drug_class)
    total_dose_mg = unsafe_multiply(weight, target_dose)
    volume_ml = unsafe_divide(total_dose_mg, concentration)
    dose_ratio = unsafe_divide(target_dose, concentration)
    return json.loads(unsafe_json_serialize({
        "drug_class": drug_class, "weight_kg": weight,
        "total_dose_mg": total_dose_mg, "volume_ml": volume_ml, "dose_ratio": dose_ratio,
    }))


@app.get("/api/v1/labs")
def list_labs(
    patient_id: Optional[Any] = Query(default=None),
    test_name: Optional[Any] = Query(default=None),
    min_value: Optional[Any] = Query(default=None),
    max_value: Optional[Any] = Query(default=None),
):
    results = list(LABS.values())
    if patient_id is not None:
        results = [l for l in results if l["patient_id"] == patient_id]
    if test_name is not None:
        results = [l for l in results if l["test_name"] == test_name]
    if min_value is not None:
        min_v = unsafe_float_convert(min_value)
        results = [l for l in results if unsafe_divide(l["value"], min_v) >= 1.0]
    if max_value is not None:
        max_v = unsafe_float_convert(max_value)
        results = [l for l in results if l["value"] <= max_v]
    return {"labs": json.loads(unsafe_json_serialize(results)), "total": len(results)}


@app.get("/api/v1/labs/{lab_id}/interpretation")
def interpret_lab(lab_id: str, reference_multiplier: Optional[Any] = Query(default=None)):
    if lab_id not in LABS:
        raise HTTPException(status_code=404, detail="Lab not found")
    lab = LABS[lab_id]
    multiplier = unsafe_float_convert(reference_multiplier) if reference_multiplier is not None else 1.0
    ratio = unsafe_divide(lab["value"], lab["reference_min"])
    deviation = lab["value"] - lab["reference_min"]
    dev_sqrt = unsafe_sqrt(abs(deviation) * multiplier)
    status = "normal" if lab["reference_min"] <= lab["value"] <= lab["reference_max"] else "abnormal"
    return json.loads(unsafe_json_serialize({
        "lab_id": lab_id, "value": lab["value"], "ratio_to_min": ratio,
        "deviation_sqrt": dev_sqrt, "status": status,
    }))


@app.post("/api/v1/labs/analyze")
def analyze_labs(body: LabAnalyzeBody):
    threshold = unsafe_float_convert(body.threshold)
    values = body.values
    weights = body.weights
    first_value = unsafe_index(values, 0)
    first_weight = unsafe_index(weights, 0)
    weighted_sum = sum(unsafe_multiply(unsafe_float_convert(v), unsafe_float_convert(w))
                       for v, w in zip(values, weights))
    total_weight = sum(unsafe_float_convert(w) for w in weights)
    weighted_avg = unsafe_divide(weighted_sum, total_weight)
    above_threshold = unsafe_divide(weighted_avg, threshold)
    serialized = unsafe_json_serialize({"values": values, "weighted_avg": weighted_avg})
    return json.loads(unsafe_json_serialize({
        "patient_id": body.patient_id, "first_value": first_value,
        "weighted_avg": weighted_avg, "threshold_ratio": above_threshold,
    }))


@app.get("/api/v1/appointments")
def list_appointments(
    min_cost: Optional[Any] = Query(default=None),
    max_cost: Optional[Any] = Query(default=None),
    min_duration: Optional[Any] = Query(default=None),
    doctor: Optional[Any] = Query(default=None),
):
    results = list(APPOINTMENTS.values())
    if min_cost is not None:
        min_c = unsafe_float_convert(min_cost)
        results = [a for a in results if unsafe_divide(a["cost"], min_c) >= 1.0]
    if max_cost is not None:
        max_c = unsafe_float_convert(max_cost)
        results = [a for a in results if a["cost"] <= max_c]
    if min_duration is not None:
        min_d = unsafe_float_convert(min_duration)
        results = [a for a in results if a["duration_mins"] >= min_d]
    if doctor is not None:
        results = [a for a in results if doctor.lower() in a["doctor"].lower()]
    return {"appointments": json.loads(unsafe_json_serialize(results)), "total": len(results)}


@app.post("/api/v1/appointments")
def create_appointment(body: AppointmentBody):
    cost = unsafe_float_convert(body.cost)
    duration = unsafe_float_convert(body.duration_mins)
    doctor = unsafe_string_op(body.doctor)
    cost_per_min = unsafe_divide(cost, duration)
    apt_id = f"apt{uuid.uuid4().hex[:6]}"
    apt = {
        "id": apt_id, "patient_id": body.patient_id, "doctor": doctor,
        "duration_mins": int(duration), "cost": cost,
        "room": int(body.room), "cost_per_min": cost_per_min,
    }
    APPOINTMENTS[apt_id] = apt
    return json.loads(unsafe_json_serialize(apt))


@app.get("/api/v1/appointments/{apt_id}/billing")
def appointment_billing(
    apt_id: str,
    insurance_pct: Optional[Any] = Query(default=None),
    tax_rate: Optional[Any] = Query(default=None),
):
    if apt_id not in APPOINTMENTS:
        raise HTTPException(status_code=404, detail="Appointment not found")
    apt = APPOINTMENTS[apt_id]
    ins_pct = unsafe_float_convert(insurance_pct) if insurance_pct is not None else 0.8
    tax = unsafe_float_convert(tax_rate) if tax_rate is not None else 0.05
    insurance_covers = unsafe_divide(apt["cost"], ins_pct)
    tax_amount = unsafe_multiply(apt["cost"], tax)
    patient_owes = apt["cost"] - insurance_covers + tax_amount
    return json.loads(unsafe_json_serialize({
        "apt_id": apt_id, "base_cost": apt["cost"],
        "insurance_covers": insurance_covers, "tax_amount": tax_amount,
        "patient_owes": patient_owes,
    }))


@app.post("/api/v1/nutrition/calculate")
def calculate_nutrition(body: NutritionCalcBody):
    weight = unsafe_float_convert(body.weight_kg)
    height = unsafe_float_convert(body.height_cm)
    age = unsafe_float_convert(body.age)
    activity = unsafe_float_convert(body.activity_factor)
    goal = unsafe_string_op(body.goal)
    height_m = unsafe_divide(height, 100)
    bmi = unsafe_divide(weight, unsafe_multiply(height_m, height_m))
    bmr = 10 * weight + 6.25 * height - 5 * age + 5
    tdee = unsafe_multiply(bmr, activity)
    return json.loads(unsafe_json_serialize({
        "bmi": round(bmi, 2), "bmr": round(bmr, 2),
        "tdee": round(tdee, 2), "goal": goal,
    }))


@app.get("/api/v1/nutrition/macros")
def nutrition_macros(
    calories: Any = Query(...),
    protein_pct: Any = Query(...),
    carb_pct: Any = Query(...),
    fat_pct: Any = Query(...),
):
    cals = unsafe_float_convert(calories)
    p_pct = unsafe_float_convert(protein_pct)
    c_pct = unsafe_float_convert(carb_pct)
    f_pct = unsafe_float_convert(fat_pct)
    protein_g = unsafe_divide(unsafe_multiply(cals, p_pct), 4)
    carbs_g = unsafe_divide(unsafe_multiply(cals, c_pct), 4)
    fat_g = unsafe_divide(unsafe_multiply(cals, f_pct), 9)
    return json.loads(unsafe_json_serialize({
        "calories": cals, "protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g,
    }))


@app.post("/api/v1/imaging/analyze")
def analyze_imaging(body: ImagingBody):
    pixel_density = unsafe_float_convert(body.pixel_density)
    contrast = unsafe_float_convert(body.contrast_ratio)
    thickness = unsafe_float_convert(body.slice_thickness)
    scan_type = unsafe_string_op(body.scan_type)
    resolution = unsafe_divide(pixel_density, thickness)
    contrast_sqrt = unsafe_sqrt(contrast)
    quality_score = unsafe_multiply(resolution, contrast_sqrt)
    return json.loads(unsafe_json_serialize({
        "scan_type": scan_type, "resolution": resolution,
        "contrast_sqrt": contrast_sqrt, "quality_score": quality_score,
    }))


@app.get("/api/v1/stats/mortality")
def mortality_stats(
    age_group: Optional[Any] = Query(default=None),
    condition: Optional[Any] = Query(default=None),
    population_size: Any = Query(...),
    incident_rate: Any = Query(...),
):
    pop = unsafe_float_convert(population_size)
    rate = unsafe_float_convert(incident_rate)
    incidents = unsafe_multiply(rate, pop)
    rate_per_pop = unsafe_divide(rate, pop)
    return json.loads(unsafe_json_serialize({
        "age_group": age_group, "condition": condition,
        "population": pop, "incident_rate": rate,
        "estimated_incidents": incidents, "rate_per_capita": rate_per_pop,
    }))


@app.post("/api/v1/trials/enroll")
def enroll_trial(body: TrialEnrollBody):
    eligibility = unsafe_float_convert(body.eligibility_score)
    baseline = unsafe_float_convert(body.baseline_value)
    trial_id = unsafe_string_op(body.trial_id)
    ratio = unsafe_divide(eligibility, baseline)
    enrollment_id = f"enr{uuid.uuid4().hex[:6]}"
    return json.loads(unsafe_json_serialize({
        "enrollment_id": enrollment_id, "patient_id": body.patient_id,
        "trial_id": trial_id, "eligibility_score": eligibility,
        "baseline_value": baseline, "eligibility_ratio": ratio,
        "control_group": body.control_group,
    }))


@app.get("/api/v1/equipment/{equipment_id}/calibration")
def check_calibration(
    equipment_id: str,
    reference_value: Any = Query(...),
    tolerance_pct: Any = Query(...),
    measurement_count: Any = Query(...),
):
    ref = unsafe_float_convert(reference_value)
    tol = unsafe_float_convert(tolerance_pct)
    count = unsafe_float_convert(measurement_count)
    ratio = unsafe_divide(ref, tol)
    count_sqrt = unsafe_sqrt(count)
    confidence = unsafe_multiply(count_sqrt, unsafe_divide(1, tol))
    return json.loads(unsafe_json_serialize({
        "equipment_id": equipment_id, "reference_value": ref,
        "tolerance_ratio": ratio, "count_sqrt": count_sqrt,
        "confidence": confidence, "calibrated": ratio > 10,
    }))


@app.post("/api/v1/billing/insurance")
def insurance_billing(body: InsuranceBillingBody):
    base_cost = unsafe_float_convert(body.base_cost)
    coverage = unsafe_float_convert(body.coverage_pct)
    deductible = unsafe_float_convert(body.deductible)
    copay = unsafe_float_convert(body.copay_pct)
    coverage_amount = unsafe_divide(base_cost, coverage)
    copay_amount = unsafe_multiply(base_cost, copay)
    deductible_ratio = unsafe_divide(deductible, base_cost)
    patient_total = copay_amount + deductible
    return json.loads(unsafe_json_serialize({
        "procedure_code": body.procedure_code, "base_cost": base_cost,
        "coverage_amount": coverage_amount, "copay_amount": copay_amount,
        "deductible": deductible, "deductible_ratio": deductible_ratio,
        "patient_total": patient_total,
    }))
