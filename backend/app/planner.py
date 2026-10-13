"""Базовий (rule-based) генератор плану харчування. Він же -- fallback для AI."""
import random

from .foods import FOODS, MEAL_SHARE, TEMPLATES, FIXED, is_excluded
from .schemas import Meal, MealItem


class PlanImpossible(Exception):
    """Не вдалося скласти план із такими винятками."""


def _build_meal(name: str, target_kcal: float, template, excluded: list[str]) -> Meal | None:
    foods = [(FOODS[fid], spec) for fid, spec in template]
    if any(is_excluded(f, excluded) for f, _ in foods):
        return None
    fixed_kcal = sum(f.kcal100 * spec[1] / 100 for f, spec in foods if isinstance(spec, tuple))
    remaining = target_kcal - fixed_kcal
    if remaining < target_kcal * 0.3:
        return None
    items = []
    for f, spec in foods:
        if isinstance(spec, tuple):
            grams = spec[1]
        else:
            grams = remaining * spec / f.kcal100 * 100
        grams = max(5, int(round(grams / 5.0) * 5))
        items.append(MealItem(name=f.name, grams=grams, kcal=round(f.kcal100 * grams / 100)))
    return Meal(name=name, items=items, kcal=sum(i.kcal for i in items))


def build_plan(target: int, excluded: list[str], rng: random.Random | None = None) -> list[Meal]:
    rng = rng or random.Random()
    meals = []
    for meal_name, share in MEAL_SHARE.items():
        options = list(TEMPLATES[meal_name])
        rng.shuffle(options)
        meal = None
        for tpl in options:
            meal = _build_meal(meal_name, target * share, tpl, excluded)
            if meal:
                break
        if meal is None:
            raise PlanImpossible(f"Не вдалося підібрати «{meal_name}» з урахуванням винятків.")
        meals.append(meal)
    return meals
