"""Справочник плоских категорий и независимых тегов (сидер: scripts/seed_categories.py)."""

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
    "Животные": {"icon": "paw-print", "color": "#84cc16"},
    "Прочее": {"icon": "package", "color": "#78716c"},
}

INCOME_CATEGORY_META: dict[str, dict[str, str]] = {
    "Зарплата": {"icon": "wallet", "color": "#16a34a"},
    "Подработка": {"icon": "briefcase", "color": "#0891b2"},
    "Возвраты": {"icon": "undo-2", "color": "#64748b"},
    "Прочие доходы": {"icon": "sparkles", "color": "#eab308"},
}

# Плоские категории расходов (без иерархии)
EXPENSE_CATEGORIES: list[str] = list(EXPENSE_CATEGORY_META.keys())

INCOME_CATEGORIES: list[str] = list(INCOME_CATEGORY_META.keys())

# Системные теги — отдельная сущность, не привязаны к категории.
# Один и тот же тег может стоять у позиций из разных категорий.
SYSTEM_TAGS: list[str] = [
    # бывшие «подкатегории» продуктов
    "Молочные",
    "Сладости",
    "Овощи и фрукты",
    "Напитки",
    "Мясо и рыба",
    "Алкоголь",
    "Крупы",
    "Снэки",
    "Никотин",
    # здоровье
    "Аптека",
    "Спорт",
    "Врачи",
    # дом
    "Коммунальные",
    "Ремонт",
    "Бытовая химия",
    "Мебель",
    # транспорт
    "Топливо",
    "Такси",
    "Общественный транспорт",
    "Обслуживание авто",
    # развлечения
    "Кино",
    "Рестораны",
    "Подписки",
    "Хобби",
    # одежда (имя тега может совпадать с именем категории — это разные сущности)
    "Одежда",
    "Обувь",
    "Аксессуары",
    # связь
    "Мобильная связь",
    "Интернет",
    # образование
    "Курсы",
    "Книги",
]

# Эвристика по названию позиции, если LLM не вернул/вернул невалидные теги
_TAG_KEYWORD_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("Сладости", ("шок", "snickers", "батон", "конфет", "печень", "вафл", "драже")),
    ("Молочные", ("молок", "кефир", "сыр", "йогурт", "сметан", "творог")),
    (
        "Алкоголь",
        (
            "пиво",
            "вино",
            "водк",
            "виски",
            "коньяк",
            "шамп",
            "ликер",
            "ликёр",
            "алког",
            "beer",
            "wine",
            "whiskey",
            "whisky",
            "ром",
            "джин",
            "gin",
            "cider",
            "сидр",
            "настойк",
            "вермут",
            "абсент",
            "текил",
        ),
    ),
    (
        "Напитки",
        (
            "вода",
            "сок",
            "чай",
            "кофе",
            "лимонад",
            "cola",
            "кола",
            "энергет",
            "морс",
            "квас",
            "sprite",
            "fanta",
            "pepsi",
        ),
    ),
    (
        "Крупы",
        (
            "греч",
            "рис ",
            "рис.",
            "овсян",
            "перлов",
            "пшено",
            "горох",
            "чечев",
            "мука",
            "макарон",
            "спагет",
            "вермиш",
            "булгур",
            "киноа",
            "крупа",
            "геркул",
            "манк",
            "манная",
            "пшени",
            "ячмен",
            "фасоль",
            "нут ",
        ),
    ),
    ("Мясо и рыба", ("мясо", "колбас", "сосиск", "рыба", "филе")),
    ("Овощи и фрукты", ("овощ", "фрукт", "яблок", "банан", "картоф", "помидор")),
    (
        "Снэки",
        (
            "чипс",
            "снек",
            "snack",
            "попкорн",
            "орех",
            "орешк",
            "сухар",
            "крекер",
            "сухарик",
            "гренк",
            "семеч",
            "фисташ",
            "миндал",
            "кешью",
            "нутс",
        ),
    ),
    (
        "Никотин",
        (
            "сигар",
            "табак",
            "никотин",
            "стик",
            "iqos",
            "айкос",
            "glo",
            "вейп",
            "vape",
            "эсдн",
            "снюс",
            "насвай",
            "кальян",
        ),
    ),
    ("Аптека", ("витамин", "таблет", "бинт", "мазь", "сироп")),
    ("Спорт", ("спорт", "фитнес", "гантел")),
    (
        "Бытовая химия",
        ("мыло", "порошок", "чистящ", "спрей", "ватн", "диск", "палочк", "полотенц", "бумаг"),
    ),
    ("Мебель", ("мебель", "стул", "стол", "шкаф")),
    ("Одежда", ("майка", "футбол", "рубаш", "брюк", "плать", "куртк", "носк")),
    ("Обувь", ("обув", "кросс", "ботин", "туфл")),
    ("Аксессуары", ("бритв", "расческ", "заколк")),
    (
        "Животные",
        (
            "корм",
            "наполнит",
            "лоток",
            "ошейник",
            "поводок",
            "ветерин",
            "когтеточ",
            "аквариум",
            "террариум",
            "pet ",
            "pets",
        ),
    ),
]

_SYSTEM_TAGS_SET = set(SYSTEM_TAGS)
_SYSTEM_TAGS_LOWER = {t.lower(): t for t in SYSTEM_TAGS}


def normalize_expense_category(category: str | None) -> str:
    """Только категории из справочника — для парсинга чеков."""
    name = (category or "Прочее").strip()
    return name if name in EXPENSE_CATEGORY_META else "Прочее"


def normalize_tag_name(name: str | None) -> str | None:
    """Привести имя тега к каноническому из справочника или None."""
    if not name:
        return None
    clean = name.strip()
    if clean in _SYSTEM_TAGS_SET:
        return clean
    return _SYSTEM_TAGS_LOWER.get(clean.lower())


def resolve_tags(
    suggested: list[str] | str | None,
    raw_name: str,
    *,
    max_tags: int = 3,
) -> list[str]:
    """Валидные теги из ответа LLM + keyword-hints по названию позиции."""
    tags: list[str] = []
    seen: set[str] = set()

    raw_list: list[str] = []
    if isinstance(suggested, str) and suggested.strip():
        raw_list = [suggested]
    elif isinstance(suggested, list):
        raw_list = [str(x) for x in suggested if x]

    for item in raw_list:
        canonical = normalize_tag_name(item)
        if canonical and canonical not in seen:
            tags.append(canonical)
            seen.add(canonical)
        if len(tags) >= max_tags:
            return tags

    name_lower = (raw_name or "").lower()
    for tag_name, keywords in _TAG_KEYWORD_HINTS:
        if tag_name not in _SYSTEM_TAGS_SET:
            continue
        if tag_name in seen:
            continue
        if any(kw in name_lower for kw in keywords):
            tags.append(tag_name)
            seen.add(tag_name)
            if len(tags) >= max_tags:
                break

    return tags


def build_taxonomy_prompt_block() -> str:
    """Текст для LLM: плоские категории + независимый словарь тегов."""
    lines = [
        "Категории расходов (поле category — РОВНО одно значение из списка):",
        ", ".join(EXPENSE_CATEGORIES),
        "",
        "Теги (поле tags — массив строк; 0…3 штуки). Теги НЕ привязаны к категории:",
        "одна и та же позиция «Продукты» и «Дом» может иметь общий тег.",
        "Выбирай теги ТОЛЬКО из списка (или пустой массив, если ничего не подходит):",
        ", ".join(SYSTEM_TAGS),
        "",
        "Примеры:",
        '- молоко → category: "Продукты", tags: ["Молочные"]',
        '- чипсы → category: "Продукты", tags: ["Снэки"]',
        '- корм для кошек → category: "Животные", tags: []',
        '- стиральный порошок → category: "Дом", tags: ["Бытовая химия"]',
        '- кроссовки → category: "Одежда", tags: ["Обувь"]',
    ]
    return "\n".join(lines)
