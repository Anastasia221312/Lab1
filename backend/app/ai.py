"""AI-компонент: складає план харчування під цільові калорії.

infer(payload) -> dict  -- єдина точка входу (як вимагає методичка).
1) Якщо задано GEMINI_API_KEY -- запит до Gemini (JSON-відповідь), з таймаутом.
2) Відповідь перевіряється: структура (Pydantic), винятки, відхилення калорій <= 10%.
3) Будь-яка помилка/невалідна відповідь -> контрольований fallback на rule-based.
Ключі беруться тільки зі змінних середовища.
"""
import json
import logging
import os
import random
from typing import Callable


from .calc import daily_target
from .foods import forbidden_terms
from .planner import PlanImpossible, build_plan
from .schemas import Calories, Meal, PlanRequest, PlanResponse

log = logging.getLogger("dietox.ai")

TOLERANCE_PCT = 10.0
DISCLAIMER = ("Застосунок не є медичним сервісом. Результат орієнтовний; "
              "при хворобах чи особливих дієтах порадьтесь з лікарем.")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Тип клієнта: (prompt, api_key, model, timeout) -> текст відповіді (JSON-рядок)
GeminiClient = Callable[[str, str, str, float], str]


def _http_gemini(prompt: str, api_key: str, model: str, timeout: float) -> str:
    import httpx  # імпорт тут, щоб тести логіки не вимагали встановленого httpx
    resp = httpx.post(
        GEMINI_URL.format(model=model),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7}},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _prompt(req: PlanRequest, target: int) -> str:
    return (
        "Ти дієтолог-помічник у навчальному застосунку. Склади план харчування на ОДИН день "
        f"приблизно на {target} ккал (відхилення не більше 10%). "
        "Прийоми їжі: Сніданок, Обід, Перекус, Вечеря. "
        f"Не використовуй продукти: {', '.join(req.excluded) or 'обмежень немає'}. "
        "Назви продуктів українською, порції в грамах, калорії цілі числа. "
        'Поверни ТІЛЬКИ JSON виду {"meals":[{"name":"Сніданок","items":[{"name":"...","grams":100,"kcal":100}]}]} '
        "без пояснень. Не вигадуй медичних тверджень."
    )


def _parse_gemini(text: str, req: PlanRequest, target: int) -> list[Meal]:
    data = json.loads(text)
    meals = []
    for m in data["meals"]:
        items = m["items"]
        meal = Meal(name=m["name"], items=items, kcal=sum(int(i["kcal"]) for i in items))
        meals.append(meal)
    if len(meals) < 3:
        raise ValueError("Замало прийомів їжі")
    banned = forbidden_terms(req.excluded)
    for meal in meals:
        for item in meal.items:
            if any(t in item.name.lower() for t in banned):
                raise ValueError("План містить заборонений продукт")
    return meals


def _deviation(total: int, target: int) -> float:
    return round(abs(total - target) / target * 100, 1)


def infer(payload: dict, *, gemini_client: GeminiClient | None = None,
          rng: random.Random | None = None) -> dict:
    req = PlanRequest(**payload)
    bmr, tdee, target, warnings = daily_target(req)
    meals: list[Meal] | None = None
    source = "rule-based"

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        client = gemini_client or _http_gemini
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        try:
            timeout = float(os.environ.get("AI_TIMEOUT_S", "8"))
            parsed = _parse_gemini(client(_prompt(req, target), api_key, model, timeout), req, target)
            total = sum(m.kcal for m in parsed)
            if _deviation(total, target) > TOLERANCE_PCT:
                raise ValueError(f"Відхилення калорій {_deviation(total, target)}% > {TOLERANCE_PCT}%")
            meals, source = parsed, "gemini"
        except Exception as exc:  # не показуємо деталі користувачу, лише в лог
            log.warning("Gemini недоступний або повернув некоректну відповідь: %s", type(exc).__name__)
            warnings.append("AI-сервіс тимчасово недоступний, використано базовий алгоритм.")

    if meals is None:
        meals = build_plan(target, req.excluded, rng)  # може кинути PlanImpossible

    total = sum(m.kcal for m in meals)
    dev = _deviation(total, target)
    if dev > TOLERANCE_PCT:
        warnings.append(f"Сума калорій відхиляється від норми на {dev}%.")
    resp = PlanResponse(
        calories=Calories(bmr=bmr, tdee=tdee, target=target),
        meals=meals, total_kcal=total, deviation_pct=dev,
        source=source, warnings=warnings, disclaimer=DISCLAIMER,
    )
    return resp.model_dump()


__all__ = ["infer", "PlanImpossible"]
