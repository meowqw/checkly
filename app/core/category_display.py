"""Отображаемые имена категорий для API."""


def category_display_name(category) -> str | None:
    if not category:
        return None
    return category.name
