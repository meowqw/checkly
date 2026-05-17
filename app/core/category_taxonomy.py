"""Справочник категорий расходов (синхронизирован с scripts/seed_categories.py)."""

EXPENSE_TAXONOMY: dict[str, list[str]] = {
    "Продукты": ["Молочные", "Сладости", "Овощи и фрукты", "Напитки", "Мясо и рыба"],
    "Здоровье": ["Аптека", "Спорт", "Врачи"],
    "Дом": ["Коммунальные", "Ремонт", "Бытовая химия", "Мебель"],
    "Транспорт": ["Топливо", "Такси", "Общественный транспорт", "Обслуживание авто"],
    "Развлечения": ["Кино", "Рестораны", "Подписки", "Хобби"],
    "Одежда": ["Одежда", "Обувь", "Аксессуары"],
    "Связь": ["Мобильная связь", "Интернет"],
    "Образование": ["Курсы", "Книги"],
    "Подарки": [],
    "Прочее": [],
}

# Подсказки для эвристики, если модель не вернула subcategory
_KEYWORD_HINTS: dict[str, list[tuple[str, str]]] = {
    "Продукты": [
        ("Сладости", ("шок", "snickers", "батон", "конфет", "печень", "вафл", "драже")),
        ("Молочные", ("молок", "кефир", "сыр", "йогурт", "сметан", "творог")),
        ("Напитки", ("вода", "сок", "чай", "кофе", "напит", "лимонад", "cola", "кола")),
        ("Мясо и рыба", ("мясо", "колбас", "сосиск", "рыба", "филе")),
        ("Овощи и фрукты", ("овощ", "фрукт", "яблок", "банан", "картоф", "помидор")),
    ],
    "Здоровье": [
        ("Аптека", ("витамин", "таблет", "бинт", "мазь", "сироп")),
        ("Спорт", ("спорт", "фитнес", "гантел")),
    ],
    "Дом": [
        ("Бытовая химия", ("мыло", "порошок", "чистящ", "спрей", "ватн", "диск", "палочк", "полотенц", "бумаг")),
        ("Мебель", ("мебель", "стул", "стол", "шкаф")),
    ],
    "Одежда": [
        ("Одежда", ("майка", "футбол", "рубаш", "брюк", "плать", "куртк", "носк")),
        ("Обувь", ("обув", "кросс", "ботин", "туфл")),
        ("Аксессуары", ("бритв", "расческ", "заколк")),
    ],
}


def build_taxonomy_prompt_block() -> str:
    lines = ["Дерево категорий (category → subcategory, выбирай ТОЛЬКО из списка):"]
    for parent, children in EXPENSE_TAXONOMY.items():
        if children:
            lines.append(f"- {parent}: {', '.join(children)}")
        else:
            lines.append(f"- {parent}: (без подкатегорий, subcategory = null)")
    return "\n".join(lines)


def resolve_subcategory(category: str, subcategory: str | None, raw_name: str) -> str | None:
    """Подобрать подкатегорию из справочника или по ключевым словам в названии."""
    allowed = EXPENSE_TAXONOMY.get(category, [])
    if not allowed:
        return None

    if subcategory:
        sub_clean = subcategory.strip()
        if sub_clean in allowed:
            return sub_clean
        sub_lower = sub_clean.lower()
        for candidate in allowed:
            if candidate.lower() == sub_lower or sub_lower in candidate.lower():
                return candidate
            if candidate.lower() in sub_lower:
                return candidate

    name_lower = raw_name.lower()
    for sub_name, keywords in _KEYWORD_HINTS.get(category, []):
        if any(kw in name_lower for kw in keywords):
            return sub_name

    return None
