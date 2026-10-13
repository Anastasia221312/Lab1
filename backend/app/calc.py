"""Розрахунок добової норми калорій (формула Міффліна-Сан Жеора)."""
from .schemas import PlanRequest

ACTIVITY_FACTOR = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "high": 1.725}
GOAL_FACTOR = {"lose": 0.85, "maintain": 1.0, "gain": 1.10}
MIN_KCAL = {"male": 1500, "female": 1200}


def bmr(req: PlanRequest) -> float:
    base = 10 * req.weight_kg + 6.25 * req.height_cm - 5 * req.age
    return base + (5 if req.sex == "male" else -161)


def daily_target(req: PlanRequest) -> tuple[int, int, int, list[str]]:
    """Повертає (bmr, tdee, target, warnings)."""
    warnings: list[str] = []
    b = bmr(req)
    tdee = b * ACTIVITY_FACTOR[req.activity]
    goal_factor = GOAL_FACTOR[req.goal]
    if req.age < 18 and req.goal == "lose":
        goal_factor = 1.0
        warnings.append("Для віку до 18 років дефіцит калорій не застосовується.")
    target = tdee * goal_factor
    floor = MIN_KCAL[req.sex]
    if target < floor:
        target = floor
        warnings.append(f"Норму піднято до безпечного мінімуму {floor} ккал.")
    return round(b), round(tdee), round(target), warnings
