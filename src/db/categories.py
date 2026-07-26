from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from sqlmodel import Session, select

from category_catalog import GENERAL_CATEGORY_SLUG, get_builtin_category_definitions, slugify_category_name
from db.models import (
    Category,
    CategoryCreate,
    CategoryOverride,
    CategoryPattern,
    CategoryUpdate,
    Expense,
    Transference,
)


@dataclass(frozen=True)
class CategoryView:
    """A category as a single user sees it, with their overrides applied."""

    id: int
    slug: str
    name: str
    name_en: str
    name_es: str
    is_custom: bool
    is_modified: bool
    patterns: list[str] = field(default_factory=list)


class CategoryNotFoundError(LookupError):
    """The category does not exist or is not visible to the user."""


def _sync_builtin_category_rows(session: Session, existing_by_slug: dict[str, Category]) -> bool:
    changed = False

    for definition in get_builtin_category_definitions():
        category = existing_by_slug.get(definition.slug)
        if category is None:
            category = Category(
                user_id=None,
                slug=definition.slug,
                name_en=definition.name_en,
                name_es=definition.name_es,
            )
            session.add(category)
            session.flush()
            existing_by_slug[definition.slug] = category
            changed = True
            continue

        if category.name_en != definition.name_en or category.name_es != definition.name_es:
            category.name_en = definition.name_en
            category.name_es = definition.name_es
            session.add(category)
            changed = True

    return changed


def _sync_builtin_patterns(session: Session, existing_by_slug: dict[str, Category]) -> bool:
    existing_categories = session.exec(select(Category).where(Category.user_id.is_(None))).all()
    existing_by_slug.update({category.slug: category for category in existing_categories})
    changed = False

    category_ids = [category.id for category in existing_by_slug.values() if category.id is not None]
    existing_patterns = []
    if category_ids:
        # Only the shared catalog rows count here: a user's forked keywords live
        # alongside them and must not keep a builtin keyword from being seeded.
        existing_patterns = session.exec(
            select(CategoryPattern).where(
                CategoryPattern.category_id.in_(category_ids),
                CategoryPattern.user_id.is_(None),
            )
        ).all()
    existing_pattern_keys = {(pattern.category_id, pattern.pattern) for pattern in existing_patterns}

    for definition in get_builtin_category_definitions():
        category = existing_by_slug[definition.slug]
        if category.id is None:
            session.flush()
        for pattern in definition.patterns:
            key = (category.id, pattern)
            if category.id is None or key in existing_pattern_keys:
                continue
            session.add(CategoryPattern(category_id=category.id, pattern=pattern))
            existing_pattern_keys.add(key)
            changed = True

    return changed


def sync_builtin_categories(session: Session) -> dict[str, Category]:
    existing_categories = session.exec(select(Category).where(Category.user_id.is_(None))).all()
    existing_by_slug = {category.slug: category for category in existing_categories}
    changed = _sync_builtin_category_rows(session, existing_by_slug)
    changed = _sync_builtin_patterns(session, existing_by_slug) or changed

    if changed:
        session.commit()
        for category in existing_by_slug.values():
            session.refresh(category)

    return existing_by_slug


def _normalize_pattern(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = "".join(char if char.isalnum() or char.isspace() else " " for char in normalized)
    return " ".join(normalized.split()).upper()


def _clean_patterns(values: list[str]) -> list[str]:
    """Trim, drop blanks and de-duplicate keywords, keeping the given order."""
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        pattern = value.strip()
        if not pattern:
            continue
        key = pattern.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(pattern)
    return cleaned


def get_overrides_by_category_id(session: Session, user_id: int) -> dict[int, CategoryOverride]:
    rows = session.exec(select(CategoryOverride).where(CategoryOverride.user_id == user_id)).all()
    return {row.category_id: row for row in rows}


def get_category_name_overrides(session: Session, user_id: int) -> dict[int, str]:
    """Renamed builtin categories, for serializing expenses and transferences."""
    overrides = get_overrides_by_category_id(session, user_id)
    return {category_id: override.name for category_id, override in overrides.items() if override.name}


def _effective_name(category: Category, override: CategoryOverride | None) -> str:
    if override is not None and override.name:
        return override.name
    return category.name_es


def _patterns_by_category_id(
    session: Session,
    user_id: int,
    categories: list[Category],
    overrides: dict[int, CategoryOverride],
) -> dict[int, list[str]]:
    category_ids = [category.id for category in categories if category.id is not None]
    if not category_ids:
        return {}

    rows = session.exec(select(CategoryPattern).where(CategoryPattern.category_id.in_(category_ids))).all()
    rows_by_category_id: dict[int, list[CategoryPattern]] = {}
    for row in rows:
        rows_by_category_id.setdefault(row.category_id, []).append(row)

    patterns_by_category_id: dict[int, list[str]] = {}
    for category in categories:
        if category.id is None:
            continue
        override = overrides.get(category.id)
        forked = override is not None and override.patterns_overridden
        selected: list[str] = []
        for row in rows_by_category_id.get(category.id, []):
            if category.user_id is not None:
                # Private category: rows written before keyword ownership
                # existed carry no user_id, so accept both.
                keep = row.user_id in {None, user_id}
            elif forked:
                keep = row.user_id == user_id
            else:
                keep = row.user_id is None
            if keep:
                selected.append(row.pattern)
        selected.sort(key=str.casefold)
        patterns_by_category_id[category.id] = selected

    return patterns_by_category_id


def list_categories_for_user(session: Session, user_id: int) -> list[Category]:
    sync_builtin_categories(session)
    categories = session.exec(
        select(Category).where((Category.user_id.is_(None)) | (Category.user_id == user_id))
    ).all()
    return sorted(categories, key=lambda category: category.name_es.casefold())


def _build_view(category: Category, override: CategoryOverride | None, patterns: list[str]) -> CategoryView:
    is_custom = category.user_id is not None
    return CategoryView(
        id=category.id or 0,
        slug=category.slug,
        name=_effective_name(category, override),
        name_en=category.name_en,
        name_es=category.name_es,
        is_custom=is_custom,
        is_modified=not is_custom and override is not None,
        patterns=patterns,
    )


def list_category_views(session: Session, user_id: int) -> list[CategoryView]:
    """Every category the user can use, with their renames and keywords applied."""
    categories = list_categories_for_user(session, user_id)
    overrides = get_overrides_by_category_id(session, user_id)
    patterns_by_category_id = _patterns_by_category_id(session, user_id, categories, overrides)
    views = [
        _build_view(
            category,
            overrides.get(category.id or 0),
            patterns_by_category_id.get(category.id or 0, []),
        )
        for category in categories
    ]
    return sorted(views, key=lambda view: view.name.casefold())


def get_category_view(session: Session, user_id: int, category: Category) -> CategoryView:
    overrides = get_overrides_by_category_id(session, user_id)
    patterns_by_category_id = _patterns_by_category_id(session, user_id, [category], overrides)
    return _build_view(
        category,
        overrides.get(category.id or 0),
        patterns_by_category_id.get(category.id or 0, []),
    )


def get_visible_category(session: Session, category_id: int, user_id: int) -> Category | None:
    sync_builtin_categories(session)
    return session.exec(
        select(Category).where(
            Category.id == category_id,
            (Category.user_id.is_(None)) | (Category.user_id == user_id),
        )
    ).first()


def get_global_category_by_slug(session: Session, slug: str) -> Category:
    categories_by_slug = sync_builtin_categories(session)
    category = categories_by_slug.get(slug)
    if category is None:
        msg = f"Unknown builtin category slug: {slug}"
        raise ValueError(msg)
    return category


def _visible_categories_with_patterns(
    session: Session, user_id: int
) -> tuple[list[Category], dict[int, list[str]]]:
    categories = list(
        session.exec(
            select(Category).where((Category.user_id.is_(None)) | (Category.user_id == user_id))
        ).all()
    )
    overrides = get_overrides_by_category_id(session, user_id)
    return categories, _patterns_by_category_id(session, user_id, categories, overrides)


def _match_category_for_text(
    text: str,
    user_id: int,
    categories: list[Category],
    patterns_by_category_id: dict[int, list[str]],
) -> Category | None:
    normalized_text = _normalize_pattern(text)
    if not normalized_text:
        return None

    matches: list[tuple[int, int, Category]] = []
    for category in categories:
        for pattern in patterns_by_category_id.get(category.id or 0, []):
            normalized_pattern = _normalize_pattern(pattern)
            if normalized_pattern and normalized_pattern in normalized_text:
                matches.append((len(normalized_pattern), 1 if category.user_id == user_id else 0, category))

    if not matches:
        return None

    # Longest keyword wins; a private category breaks ties with a builtin one.
    matches.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return matches[0][2]


def resolve_category_for_user_text(session: Session, user_id: int, text: str, fallback_slug: str) -> Category:
    sync_builtin_categories(session)
    categories, patterns_by_category_id = _visible_categories_with_patterns(session, user_id)
    match = _match_category_for_text(text, user_id, categories, patterns_by_category_id)
    if match is not None:
        return match
    return get_global_category_by_slug(session, fallback_slug)


def recategorize_transactions(session: Session, user_id: int) -> dict[str, int]:
    """Re-apply the user's keywords to their stored expenses and transferences.

    Only rows whose text matches a keyword move; anything unmatched keeps the
    category it has, so manual assignments are never wiped by a backfill.
    """
    sync_builtin_categories(session)
    categories, patterns_by_category_id = _visible_categories_with_patterns(session, user_id)

    expenses_updated = 0
    for expense in session.exec(select(Expense).where(Expense.user_id == user_id)).all():
        match = _match_category_for_text(expense.commerce, user_id, categories, patterns_by_category_id)
        if match is None or match.id is None or match.id == expense.category_id:
            continue
        expense.category_id = match.id
        session.add(expense)
        expenses_updated += 1

    transferences_updated = 0
    for transference in session.exec(select(Transference).where(Transference.user_id == user_id)).all():
        match = _match_category_for_text(transference.recipient, user_id, categories, patterns_by_category_id)
        if match is None or match.id is None or match.id == transference.category_id:
            continue
        transference.category_id = match.id
        session.add(transference)
        transferences_updated += 1

    if expenses_updated or transferences_updated:
        session.commit()

    return {"expenses": expenses_updated, "transferences": transferences_updated}


def _assert_name_available(
    session: Session,
    user_id: int,
    name: str,
    *,
    exclude_category_id: int | None = None,
) -> None:
    normalized = name.casefold()
    categories = list_categories_for_user(session, user_id)
    overrides = get_overrides_by_category_id(session, user_id)
    for category in categories:
        if category.id == exclude_category_id:
            continue
        if _effective_name(category, overrides.get(category.id or 0)).casefold() == normalized:
            raise ValueError("Category already exists")


def _replace_patterns(session: Session, category: Category, user_id: int, patterns: list[str]) -> None:
    """Swap the user's keyword rows for ``category``, never touching the catalog."""
    query = select(CategoryPattern).where(CategoryPattern.category_id == category.id)
    if category.user_id is None:
        # Builtin category: only this user's forked rows are ours to delete.
        query = query.where(CategoryPattern.user_id == user_id)

    for row in session.exec(query).all():
        session.delete(row)

    for pattern in patterns:
        session.add(CategoryPattern(category_id=category.id, user_id=user_id, pattern=pattern))


def create_custom_category(session: Session, user_id: int, payload: CategoryCreate) -> Category:
    normalized_name = payload.name.strip()
    if not normalized_name:
        raise ValueError("Category name is required")

    _assert_name_available(session, user_id, normalized_name)

    base_slug = slugify_category_name(normalized_name)
    slug = f"user-{user_id}-{base_slug}"
    suffix = 2

    while session.exec(select(Category).where(Category.slug == slug)).first() is not None:
        slug = f"user-{user_id}-{base_slug}-{suffix}"
        suffix += 1

    category = Category(
        user_id=user_id,
        slug=slug,
        name_en=normalized_name,
        name_es=normalized_name,
    )
    session.add(category)
    session.flush()

    patterns = _clean_patterns([*(payload.patterns or []), *([payload.pattern] if payload.pattern else [])])
    for pattern in patterns:
        session.add(CategoryPattern(category_id=category.id, user_id=user_id, pattern=pattern))

    session.commit()
    session.refresh(category)
    return category


def _apply_own_category_update(
    session: Session,
    category: Category,
    user_id: int,
    name: str | None,
    patterns: list[str] | None,
) -> None:
    if name is not None:
        category.name_en = name
        category.name_es = name
        session.add(category)
    if patterns is not None:
        _replace_patterns(session, category, user_id, _clean_patterns(patterns))


def _apply_builtin_category_override(
    session: Session,
    category: Category,
    user_id: int,
    name: str | None,
    patterns: list[str] | None,
) -> None:
    override = session.exec(
        select(CategoryOverride).where(
            CategoryOverride.user_id == user_id,
            CategoryOverride.category_id == category.id,
        )
    ).first()
    if override is None:
        override = CategoryOverride(user_id=user_id, category_id=category.id)

    if name is not None:
        # Storing the builtin name back is the same as having no rename.
        override.name = None if name == category.name_es else name
    if patterns is not None:
        override.patterns_overridden = True
        _replace_patterns(session, category, user_id, _clean_patterns(patterns))

    session.add(override)


def update_category(session: Session, user_id: int, category_id: int, payload: CategoryUpdate) -> Category:
    """Rename a category and/or replace its keywords.

    A user's own category is edited in place. Builtin categories are shared
    rows, so the change is stored as a per-user :class:`CategoryOverride` plus
    forked keyword rows -- everybody else keeps the defaults.
    """
    category = get_visible_category(session, category_id, user_id)
    if category is None:
        raise CategoryNotFoundError("Category not found")

    name: str | None = None
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise ValueError("Category name is required")
        _assert_name_available(session, user_id, name, exclude_category_id=category.id)

    if payload.name is None and payload.patterns is None:
        return category

    if category.user_id == user_id:
        _apply_own_category_update(session, category, user_id, name, payload.patterns)
    else:
        _apply_builtin_category_override(session, category, user_id, name, payload.patterns)

    session.commit()
    session.refresh(category)
    return category


def reset_builtin_category(session: Session, user_id: int, category_id: int) -> Category:
    """Drop the user's customization of a builtin category."""
    category = get_visible_category(session, category_id, user_id)
    if category is None:
        raise CategoryNotFoundError("Category not found")
    if category.user_id is not None:
        raise ValueError("Custom categories cannot be reset")

    overrides = session.exec(
        select(CategoryOverride).where(
            CategoryOverride.user_id == user_id,
            CategoryOverride.category_id == category.id,
        )
    ).all()
    for override in overrides:
        session.delete(override)

    forked_patterns = session.exec(
        select(CategoryPattern).where(
            CategoryPattern.category_id == category.id,
            CategoryPattern.user_id == user_id,
        )
    ).all()
    for pattern in forked_patterns:
        session.delete(pattern)

    session.commit()
    session.refresh(category)
    return category


def delete_custom_category(session: Session, user_id: int, category_id: int) -> int:
    """Delete one of the user's own categories.

    Its transactions move to the general category. Returns how many moved.
    """
    category = get_visible_category(session, category_id, user_id)
    if category is None:
        raise CategoryNotFoundError("Category not found")
    if category.user_id != user_id:
        raise ValueError("Builtin categories cannot be deleted")

    general_category = get_global_category_by_slug(session, GENERAL_CATEGORY_SLUG)
    expenses = session.exec(
        select(Expense).where(Expense.user_id == user_id, Expense.category_id == category.id)
    ).all()
    transferences = session.exec(
        select(Transference).where(Transference.user_id == user_id, Transference.category_id == category.id)
    ).all()
    for transaction in [*expenses, *transferences]:
        transaction.category_id = general_category.id
        session.add(transaction)

    for pattern in session.exec(select(CategoryPattern).where(CategoryPattern.category_id == category.id)).all():
        session.delete(pattern)
    for override in session.exec(
        select(CategoryOverride).where(CategoryOverride.category_id == category.id)
    ).all():
        session.delete(override)

    session.delete(category)
    session.commit()
    return len(expenses) + len(transferences)
