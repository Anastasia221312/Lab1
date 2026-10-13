"""Тести логіки backend (unittest, без запуску HTTP-сервера).
Запуск: python -m unittest discover -s tests -v   (з папки backend)
"""
import json
import os
import random
import unittest

from pydantic import ValidationError

from app import ai
from app.calc import daily_target
from app.planner import PlanImpossible, build_plan
from app.schemas import PlanRequest

BASE = dict(age=25, sex="female", weight_kg=60, height_cm=165, activity="moderate", goal="maintain", excluded=[])


def req(**kw):
    return PlanRequest(**{**BASE, **kw})


class CalcTests(unittest.TestCase):
    def test_mifflin_female(self):
        bmr, tdee, target, _ = daily_target(req())
        self.assertEqual(bmr, 1345)           # 600+1031.25-125-161
        self.assertEqual(tdee, round(1345.25 * 1.55))
        self.assertEqual(target, tdee)

    def test_goal_lose_and_gain(self):
        m = daily_target(req(sex="male", weight_kg=80, height_cm=180))[2]
        lose = daily_target(req(sex="male", weight_kg=80, height_cm=180, goal="lose"))[2]
        gain = daily_target(req(sex="male", weight_kg=80, height_cm=180, goal="gain"))[2]
        self.assertLess(lose, m)
        self.assertGreater(gain, m)

    def test_minor_has_no_deficit(self):
        _, tdee, target, warns = daily_target(req(age=16, goal="lose"))
        self.assertEqual(tdee, target)
        self.assertTrue(warns)

    def test_floor(self):
        _, _, target, warns = daily_target(req(weight_kg=40, height_cm=150, activity="sedentary", goal="lose", age=60))
        self.assertEqual(target, 1200)
        self.assertTrue(warns)


class ValidationTests(unittest.TestCase):
    def test_bad_values(self):
        for bad in [dict(age=15), dict(age=61), dict(weight_kg=0), dict(height_cm=-5),
                    dict(sex="x"), dict(activity="extreme"), dict(goal="fly"),
                    dict(excluded=["a"] * 11)]:
            with self.assertRaises(ValidationError, msg=str(bad)):
                req(**bad)

    def test_missing_field(self):
        d = dict(BASE); d.pop("weight_kg")
        with self.assertRaises(ValidationError):
            PlanRequest(**d)

    def test_excluded_cleaned(self):
        self.assertEqual(req(excluded=["  Молоко ", ""]).excluded, ["молоко"])


class PlannerTests(unittest.TestCase):
    def test_plan_close_to_target(self):
        for seed in range(30):
            for target in (1300, 1800, 2400, 3200):
                meals = build_plan(target, [], random.Random(seed))
                total = sum(m.kcal for m in meals)
                self.assertLess(abs(total - target) / target, 0.10, (seed, target, total))

    def test_exclusions_respected(self):
        names_bad = ["молок", "сир", "кефір", "йогурт", "яйц", "хліб", "макарон", "вівсян", "мигдал",
                     "курк", "індичк", "лосос", "тунец"]
        for ex, bad in [("молоко", ["молок", "сир", "кефір", "йогурт"]), ("яйця", ["яйц"]),
                        ("риба", ["лосос", "тунец"]), ("горіхи", ["мигдал"]),
                        ("глютен", ["хліб", "макарон", "вівсян"]), ("м'ясо", ["курк", "індичк"])]:
            for seed in range(20):
                meals = build_plan(2000, [ex], random.Random(seed))
                for m in meals:
                    for it in m.items:
                        self.assertFalse(any(b in it.name.lower() for b in bad), (ex, it.name))

    def test_impossible(self):
        with self.assertRaises(PlanImpossible):
            build_plan(2000, ["яблуко", "банан", "молоко"])  # жоден перекус не підходить

    def test_repeat_gives_variation(self):
        plans = {json.dumps([m.model_dump() for m in build_plan(2000, [], random.Random(s))]) for s in range(10)}
        self.assertGreater(len(plans), 1)


GOOD_GEMINI = json.dumps({"meals": [
    {"name": "Сніданок", "items": [{"name": "Вівсянка", "grams": 80, "kcal": 400}]},
    {"name": "Обід", "items": [{"name": "Курка з рисом", "grams": 300, "kcal": 700}]},
    {"name": "Перекус", "items": [{"name": "Яблуко", "grams": 150, "kcal": 80}]},
    {"name": "Вечеря", "items": [{"name": "Риба з овочами", "grams": 300, "kcal": 600}]},
]})


class AiTests(unittest.TestCase):
    def setUp(self):
        self._old = {k: os.environ.get(k) for k in ("GEMINI_API_KEY",)}
        os.environ.pop("GEMINI_API_KEY", None)
        self.payload = dict(BASE)

    def tearDown(self):
        for k, v in self._old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v

    def test_without_key_uses_rule_based(self):
        out = ai.infer(self.payload, rng=random.Random(1))
        self.assertEqual(out["source"], "rule-based")
        self.assertEqual(len(out["meals"]), 4)
        self.assertLess(out["deviation_pct"], 10)

    def test_gemini_ok(self):
        os.environ["GEMINI_API_KEY"] = "test"
        target = daily_target(req())[2]  # 2085
        good = json.loads(GOOD_GEMINI)
        good["meals"][1]["items"][0]["kcal"] = 700 + (target - 1780)
        out = ai.infer(self.payload, gemini_client=lambda *a: json.dumps(good))
        self.assertEqual(out["source"], "gemini")

    def test_gemini_error_falls_back(self):
        os.environ["GEMINI_API_KEY"] = "test"
        def boom(*a): raise RuntimeError("secret-key-xyz stack")
        out = ai.infer(self.payload, gemini_client=boom, rng=random.Random(1))
        self.assertEqual(out["source"], "rule-based")
        self.assertTrue(any("AI-сервіс" in w for w in out["warnings"]))
        self.assertNotIn("secret", json.dumps(out, ensure_ascii=False))

    def test_gemini_bad_json_falls_back(self):
        os.environ["GEMINI_API_KEY"] = "test"
        out = ai.infer(self.payload, gemini_client=lambda *a: "не json {", rng=random.Random(1))
        self.assertEqual(out["source"], "rule-based")

    def test_gemini_wrong_calories_falls_back(self):
        os.environ["GEMINI_API_KEY"] = "test"
        out = ai.infer(self.payload, gemini_client=lambda *a: GOOD_GEMINI.replace("700", "100"), rng=random.Random(1))
        self.assertEqual(out["source"], "rule-based")

    def test_gemini_forbidden_product_falls_back(self):
        os.environ["GEMINI_API_KEY"] = "test"
        self.payload["excluded"] = ["риба"]
        out = ai.infer(self.payload, gemini_client=lambda *a: GOOD_GEMINI, rng=random.Random(1))
        self.assertEqual(out["source"], "rule-based")


if __name__ == "__main__":
    unittest.main()
