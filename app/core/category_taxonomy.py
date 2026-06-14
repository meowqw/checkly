"""Справочник категорий расходов (синхронизирован с scripts/seed_categories.py)."""

# icon — имя иконки lucide-react на фронте, color — hex
EXPENSE_CATEGORY_META: dict[str, dict[str, str]] = {
    "Продукты": {"icon": "shopping-cart", "color": "#16a34a"},
    "Здоровье": {"icon": "heart-pulse", "color": "#ef4444"},
    "Дом": {"icon": "home", "color": "#f59e0b"},
    "Транспорт": {"icon": "car", "color": "#3b82f6"},
    "Развлечения": {"icon": "clapperboard", "color": "#a855f7"},
    "Одежда": {"icon": "shirt", "color": "#ec4899"},
    "Связь": {"icon": "smartphone", "color": "#06b6d4"},
    "Образование": {"icon": "book-open", "color": "#6366f1"},
    "Подарки": {"icon": "gift", "color": "#f97316"},
    "Прочее": {"icon": "package", "color": "#78716c"},
}

INCOME_CATEGORY_META: dict[str, dict[str, str]] = {
    "Зарплата": {"icon": "wallet", "color": "#16a34a"},
    "Подработка": {"icon": "briefcase", "color": "#0891b2"},
    "Возвраты": {"icon": "undo-2", "color": "#64748b"},
    "Прочие доходы": {"icon": "sparkles", "color": "#eab308"},
}

EXPENSE_TAXONOMY: dict[str, list[str]] = {
    "Продукты": [
        "Молочные",
        "Сладости",
        "Овощи и фрукты",
        "Напитки",
        "Мясо и рыба",
        "Алкоголь",
        "Крупы",
    ],
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
        ("Алкоголь", (
            "пиво", "вино", "водк", "виски", "коньяк", "шамп", "ликер", "ликёр",
            "алког", "beer", "wine", "whiskey", "whisky", "rom", "джин", "gin",
            "cider", "сидр", "настойк", "вермут", "абсент", "текил", "ром ",
        )),
        ("Напитки", (
            "вода", "сок", "чай", "кофе", "лимонад", "cola", "кола", "энергет",
            "морс", "квас", "sprite", "fanta", "pepsi",
        )),
        ("Крупы", (
            "греч", "рис ", "рис.", "овсян", "перлов", "пшено", "горох", "чечев",
            "мука", "макарон", "спагет", "вермиш", "булгур", "киноа", "крупа",
            "геркул", "манк", "манная", "пшени", "ячмен", "фасоль", "нут ",
        )),
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


def normalize_expense_category(category: str | None) -> str:
    """Только категории из справочника — для парсинга чеков."""
    name = (category or "Прочее").strip()
    return name if name in EXPENSE_TAXONOMY else "Прочее"


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
