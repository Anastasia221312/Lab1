"""Перевірка AI-функції на 5 вхідних прикладах (таблиця для звіту).
Запуск з папки backend:  python tools/ai_validation.py
"""
import os, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import ai
from app.foods import forbidden_terms

CASES = [
    ("1. Жінка 25 р., помірна активність, підтримка", dict(age=25, sex="female", weight_kg=60, height_cm=165, activity="moderate", goal="maintain", excluded=[])),
    ("2. Чоловік 35 р., схуднення", dict(age=35, sex="male", weight_kg=95, height_cm=182, activity="light", goal="lose", excluded=[])),
    ("3. Студентка 17 р., схуднення (захист неповнолітніх)", dict(age=17, sex="female", weight_kg=58, height_cm=168, activity="high", goal="lose", excluded=[])),
    ("4. Чоловік 28 р., набір маси, виняток: молоко, горіхи", dict(age=28, sex="male", weight_kg=70, height_cm=178, activity="high", goal="gain", excluded=["молоко", "горіхи"])),
    ("5. Жінка 55 р., мала вага, виняток: риба, глютен (безпечний мінімум)", dict(age=55, sex="female", weight_kg=42, height_cm=152, activity="sedentary", goal="lose", excluded=["риба", "глютен"])),
]

rows = []
for i, (title, payload) in enumerate(CASES):
    t0 = time.perf_counter()
    out = ai.infer(payload, rng=random.Random(100 + i))
    ms = (time.perf_counter() - t0) * 1000
    banned = forbidden_terms(payload["excluded"])
    violated = [it["name"] for m in out["meals"] for it in m["items"] if any(t in it["name"].lower() for t in banned)]
    ok = out["deviation_pct"] <= 10 and not violated and len(out["meals"]) == 4
    rows.append((title, out, ms, violated, ok))
    print(f"{title}\n  норма={out['calories']['target']} ккал; план={out['total_kcal']} ккал; відхилення={out['deviation_pct']}%; "
          f"джерело={out['source']}; час={ms:.1f} мс; порушення винятків={violated or 'немає'}; попередження={out['warnings']}; OK={ok}")
