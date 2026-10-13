"""Pydantic-моделі вхідних даних і відповіді API."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Sex = Literal["male", "female"]
Activity = Literal["sedentary", "light", "moderate", "high"]
Goal = Literal["lose", "maintain", "gain"]


class PlanRequest(BaseModel):
    age: int = Field(ge=16, le=60, description="Вік, повних років (16-60)")
    sex: Sex
    weight_kg: float = Field(ge=30, le=250)
    height_cm: float = Field(ge=120, le=230)
    activity: Activity
    goal: Goal
    excluded: list[str] = Field(default_factory=list, max_length=10,
                                description="Продукти-винятки (алергії, вподобання)")

    @field_validator("excluded")
    @classmethod
    def clean_excluded(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip().lower() for s in v if s and s.strip()]
        if any(len(s) > 40 for s in cleaned):
            raise ValueError("Назва винятку задовга (макс. 40 символів)")
        return cleaned


class Calories(BaseModel):
    bmr: int
    tdee: int
    target: int


class MealItem(BaseModel):
    name: str
    grams: int = Field(gt=0)
    kcal: int = Field(ge=0)


class Meal(BaseModel):
    name: str
    items: list[MealItem] = Field(min_length=1)
    kcal: int


class PlanResponse(BaseModel):
    calories: Calories
    meals: list[Meal]
    total_kcal: int
    deviation_pct: float
    source: Literal["gemini", "rule-based"]
    warnings: list[str] = []
    disclaimer: str


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
