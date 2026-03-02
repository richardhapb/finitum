import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from db.categories import (
    create_custom_category,
    get_visible_category,
    list_categories_for_user,
    resolve_category_for_user_text,
    sync_builtin_categories,
)
from db.models import CategoryCreate, CategoryPattern, User


def create_user(session: Session, username: str, email: str) -> User:
    user = User.create(username=username, email=email, password="password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_sync_builtin_categories_seeds_global_catalog():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        categories_by_slug = sync_builtin_categories(session)
        patterns = session.exec(select(CategoryPattern)).all()

        assert "general" in categories_by_slug
        assert "external_food" in categories_by_slug
        assert categories_by_slug["food"].name_es == "Comida"
        assert categories_by_slug["general"].user_id is None
        assert any(pattern.pattern == "UBER EATS" for pattern in patterns)


def test_custom_categories_are_private_to_the_owner():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        owner = create_user(session, "owner", "owner@example.com")
        another_user = create_user(session, "other", "other@example.com")

        owner_category = create_custom_category(session, owner.id, CategoryCreate(name="Mascotas"))
        another_category = create_custom_category(session, another_user.id, CategoryCreate(name="Juegos"))

        owner_categories = list_categories_for_user(session, owner.id)
        owner_slugs = {category.slug for category in owner_categories}

        assert owner_category.slug in owner_slugs
        assert another_category.slug not in owner_slugs
        assert get_visible_category(session, owner_category.id, owner.id) is not None
        assert get_visible_category(session, another_category.id, owner.id) is None


def test_custom_category_can_store_a_pattern():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = create_user(session, "owner", "owner@example.com")
        category = create_custom_category(session, user.id, CategoryCreate(name="Mascotas", pattern="PETSHOP"))
        patterns = session.exec(select(CategoryPattern).where(CategoryPattern.category_id == category.id)).all()

        assert [pattern.pattern for pattern in patterns] == ["PETSHOP"]


def test_custom_pattern_overrides_builtin_categorization():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = create_user(session, "owner", "owner@example.com")
        create_custom_category(session, user.id, CategoryCreate(name="Mascotas", pattern="JUMBO"))

        resolved = resolve_category_for_user_text(session, user.id, "COMPRA EN JUMBO BILBAO", "food")

        assert resolved.name_es == "Mascotas"
        assert resolved.user_id == user.id


def test_custom_category_names_must_be_unique_per_user():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = create_user(session, "owner", "owner@example.com")
        create_custom_category(session, user.id, CategoryCreate(name="Mascotas"))

        with pytest.raises(ValueError, match="Category already exists"):
            create_custom_category(session, user.id, CategoryCreate(name="mascotas"))
