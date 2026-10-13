"""Невелика локальна база продуктів (ккал на 100 г) і шаблони страв."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Food:
    id: str
    name: str
    kcal100: int
    tags: frozenset


def _f(i, name, kcal, *tags):
    return Food(i, name, kcal, frozenset(tags))


FOODS = {f.id: f for f in [
    _f("oats", "Вівсяні пластівці (сухі)", 366, "gluten"),
    _f("milk", "Молоко 2,5%", 52, "dairy"),
    _f("banana", "Банан", 89),
    _f("apple", "Яблуко", 52),
    _f("orange", "Апельсин", 47),
    _f("egg", "Яйце варене", 155, "eggs"),
    _f("bread", "Хліб цільнозерновий", 247, "gluten"),
    _f("tomato", "Помідор", 18),
    _f("cucumber", "Огірок", 15),
    _f("cottage", "Сир кисломолочний 5%", 121, "dairy"),
    _f("honey", "Мед", 304),
    _f("yogurt", "Йогурт натуральний", 60, "dairy"),
    _f("kefir", "Кефір 1%", 40, "dairy"),
    _f("almond", "Мигдаль", 579, "nuts"),
    _f("buckwheat", "Гречка (суха)", 313),
    _f("rice", "Рис (сухий)", 360),
    _f("pasta", "Макарони (сухі)", 350, "gluten"),
    _f("lentils", "Сочевиця (суха)", 295),
    _f("chickpeas", "Нут (відварений)", 164),
    _f("potato", "Картопля варена", 82),
    _f("broccoli", "Броколі", 34),
    _f("olive_oil", "Оливкова олія", 884),
    _f("chicken", "Куряча грудка (варена)", 165, "meat"),
    _f("turkey", "Філе індички (варене)", 135, "meat"),
    _f("salmon", "Лосось запечений", 206, "fish"),
    _f("tuna", "Тунець консервований у власному соку", 116, "fish"),
]}

# Ключові слова, за якими користувацький виняток зіставляється з групою продуктів.
TAG_KEYWORDS = {
    "dairy": ["молок", "молоч", "лактоз", "сир", "йогурт", "кефір", "вершк"],
    "eggs": ["яйц", "яєчн", "яйк"],
    "gluten": ["глютен", "пшениц", "хліб", "борошн", "макарон"],
    "nuts": ["горіх", "мигдал", "арахіс"],
    "meat": ["м'яс", "мʼяс", "мяс", "курк", "індичк"],
    "fish": ["риб", "лосос", "тунец", "морепродукт"],
}


def resolve_exclusions(excluded: list[str]) -> tuple[set, set]:
    """Повертає (заборонені слова, заборонені теги)."""
    terms, tags = set(), set()
    for ex in excluded:
        if len(ex) < 3:
            continue
        terms.add(ex)
        for tag, kws in TAG_KEYWORDS.items():
            if any(ex in kw or kw in ex for kw in kws):
                tags.add(tag)
    return terms, tags


def forbidden_terms(excluded: list[str]) -> set:
    terms, tags = resolve_exclusions(excluded)
    for t in tags:
        terms.update(TAG_KEYWORDS[t])
    return terms


def is_excluded(food: Food, excluded: list[str]) -> bool:
    terms, tags = resolve_exclusions(excluded)
    name = food.name.lower()
    return bool(food.tags & tags) or any(t in name for t in terms)


# Шаблон: список (food_id, частка калорій) або (food_id, ("g", грами)) для фіксованих порцій.
FIXED = "g"
MEAL_SHARE = {"Сніданок": 0.25, "Обід": 0.35, "Перекус": 0.10, "Вечеря": 0.30}

TEMPLATES = {
    "Сніданок": [
        [("oats", 0.5), ("milk", 0.25), ("banana", 0.25)],
        [("egg", 0.5), ("bread", 0.5), ("tomato", (FIXED, 100))],
        [("cottage", 0.55), ("apple", 0.25), ("honey", 0.20)],
        [("buckwheat", 0.7), ("apple", 0.3)],
    ],
    "Обід": [
        [("chicken", 0.45), ("rice", 0.55), ("broccoli", (FIXED, 150)), ("olive_oil", (FIXED, 5))],
        [("salmon", 0.5), ("potato", 0.5), ("cucumber", (FIXED, 100))],
        [("turkey", 0.4), ("pasta", 0.6), ("tomato", (FIXED, 100))],
        [("lentils", 0.6), ("rice", 0.4), ("broccoli", (FIXED, 100))],
        [("chickpeas", 0.6), ("potato", 0.4), ("cucumber", (FIXED, 100)), ("olive_oil", (FIXED, 5))],
    ],
    "Перекус": [
        [("apple", 0.5), ("almond", 0.5)],
        [("kefir", 0.6), ("banana", 0.4)],
        [("yogurt", 0.7), ("honey", 0.3)],
        [("apple", 0.6), ("orange", 0.4)],
    ],
    "Вечеря": [
        [("tuna", 0.45), ("potato", 0.55), ("tomato", (FIXED, 100))],
        [("chicken", 0.5), ("buckwheat", 0.5), ("cucumber", (FIXED, 100))],
        [("egg", 0.4), ("bread", 0.3), ("cottage", 0.3)],
        [("lentils", 0.5), ("buckwheat", 0.5), ("broccoli", (FIXED, 100))],
        [("salmon", 0.45), ("rice", 0.55), ("broccoli", (FIXED, 100))],
    ],
}
