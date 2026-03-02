from __future__ import annotations

import unicodedata

from sqlmodel import Session, select

from category_catalog import get_builtin_category_definitions, slugify_category_name
from db.models import Category, CategoryCreate, CategoryPattern


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
        existing_patterns = session.exec(
            select(CategoryPattern).where(CategoryPattern.category_id.in_(category_ids))
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


def get_category_patterns(session: Session, category_ids: list[int]) -> dict[int, list[str]]:
    if not category_ids:
        return {}

    rows = session.exec(select(CategoryPattern).where(CategoryPattern.category_id.in_(category_ids))).all()
    patterns_by_category_id: dict[int, list[str]] = {}
    for row in rows:
        patterns_by_category_id.setdefault(row.category_id, []).append(row.pattern)

    for patterns in patterns_by_category_id.values():
        patterns.sort(key=str.casefold)

    return patterns_by_category_id


def list_categories_for_user(session: Session, user_id: int) -> list[Category]:
    sync_builtin_categories(session)
    categories = session.exec(
        select(Category).where((Category.user_id.is_(None)) | (Category.user_id == user_id))
    ).all()
    return sorted(categories, key=lambda category: category.name_es.casefold())


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


def resolve_category_for_user_text(session: Session, user_id: int, text: str, fallback_slug: str) -> Category:
    sync_builtin_categories(session)
    normalized_text = _normalize_pattern(text)
    if normalized_text:
        rows = session.exec(
            select(CategoryPattern, Category)
            .join(Category, CategoryPattern.category_id == Category.id)
            .where((Category.user_id.is_(None)) | (Category.user_id == user_id))
        ).all()

        matches: list[tuple[int, int, Category]] = []
        for pattern, category in rows:
            normalized_pattern = _normalize_pattern(pattern.pattern)
            if normalized_pattern and normalized_pattern in normalized_text:
                matches.append((len(normalized_pattern), 1 if category.user_id == user_id else 0, category))

        if matches:
            matches.sort(key=lambda row: (row[0], row[1]), reverse=True)
            return matches[0][2]

    return get_global_category_by_slug(session, fallback_slug)


def create_custom_category(session: Session, user_id: int, payload: CategoryCreate) -> Category:
    normalized_name = payload.name.strip()
    if not normalized_name:
        raise ValueError("Category name is required")

    existing_names = session.exec(select(Category).where(Category.user_id == user_id)).all()
    if any(category.name_es.casefold() == normalized_name.casefold() for category in existing_names):
        raise ValueError("Category already exists")

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

    normalized_pattern = payload.pattern.strip() if payload.pattern else ""
    if normalized_pattern:
        session.add(CategoryPattern(category_id=category.id, pattern=normalized_pattern))

    session.commit()
    session.refresh(category)
    return category
