"""Отображаемые имена категорий для API."""


def category_display_name(category) -> str | None:
    if not category:
        return None
    if category.parent:
        return f"{category.parent.name} › {category.name}"
    return category.name
