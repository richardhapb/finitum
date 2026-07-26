"""Tests for user-managed categories.

Builtin categories are global rows shared by every user, so editing one is
stored as a private override plus a forked keyword set. These tests cover that
isolation, the reset path, deletion, and the backfill that re-applies keywords
to already stored transactions.
"""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from api import server
from api.jwt import get_current_user
from db.categories import (
    CategoryNotFoundError,
    create_custom_category,
    delete_custom_category,
    get_global_category_by_slug,
    list_category_views,
    recategorize_transactions,
    reset_builtin_category,
    resolve_category_for_user_text,
    update_category,
)
from db.models import (
    Category,
    CategoryCreate,
    CategoryPattern,
    CategoryUpdate,
    Expense,
    Transference,
    User,
)
from db.service import get_session


def create_user(session: Session, username: str, email: str) -> User:
    user = User.create(username=username, email=email, password="password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def view_by_slug(session: Session, user_id: int, slug: str):
    return next(view for view in list_category_views(session, user_id) if view.slug == slug)


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def test_adding_a_keyword_to_a_builtin_category_only_affects_that_user(session):
    owner = create_user(session, "owner", "owner@example.com")
    other = create_user(session, "other", "other@example.com")
    housing = get_global_category_by_slug(session, "housing")
    default_keywords = view_by_slug(session, owner.id, "housing").patterns

    update_category(
        session,
        owner.id,
        housing.id,
        CategoryUpdate(patterns=[*default_keywords, "JUNTA DE VECINOS"]),
    )

    owner_view = view_by_slug(session, owner.id, "housing")
    other_view = view_by_slug(session, other.id, "housing")

    assert "JUNTA DE VECINOS" in owner_view.patterns
    assert owner_view.is_modified is True
    assert "JUNTA DE VECINOS" not in other_view.patterns
    assert other_view.is_modified is False
    assert other_view.patterns == default_keywords

    resolved = resolve_category_for_user_text(
        session, owner.id, "PAGO JUNTA DE VECINOS", "general"
    )
    assert resolved.slug == "housing"
    assert resolve_category_for_user_text(
        session, other.id, "PAGO JUNTA DE VECINOS", "general"
    ).slug == "general"


def test_removing_a_builtin_keyword_stops_matching_for_that_user(session):
    owner = create_user(session, "owner", "owner@example.com")
    other = create_user(session, "other", "other@example.com")
    food = get_global_category_by_slug(session, "food")
    kept = [pattern for pattern in view_by_slug(session, owner.id, "food").patterns if pattern != "JUMBO"]

    update_category(session, owner.id, food.id, CategoryUpdate(patterns=kept))

    assert "JUMBO" not in view_by_slug(session, owner.id, "food").patterns
    assert "JUMBO" in view_by_slug(session, other.id, "food").patterns
    assert resolve_category_for_user_text(session, owner.id, "COMPRA EN JUMBO", "general").slug == "general"
    assert resolve_category_for_user_text(session, other.id, "COMPRA EN JUMBO", "general").slug == "food"


def test_renaming_a_builtin_category_is_private_to_the_user(session):
    owner = create_user(session, "owner", "owner@example.com")
    other = create_user(session, "other", "other@example.com")
    housing = get_global_category_by_slug(session, "housing")

    update_category(session, owner.id, housing.id, CategoryUpdate(name="Casa"))

    assert view_by_slug(session, owner.id, "housing").name == "Casa"
    assert view_by_slug(session, other.id, "housing").name == "Vivienda"
    # The shared row keeps its catalog labels.
    assert session.get(Category, housing.id).name_es == "Vivienda"


def test_builtin_keywords_are_not_reseeded_into_a_forked_category(session):
    owner = create_user(session, "owner", "owner@example.com")
    food = get_global_category_by_slug(session, "food")

    update_category(session, owner.id, food.id, CategoryUpdate(patterns=["PANADERIA"]))
    # A later request re-runs the builtin sync; the fork must survive it.
    list_category_views(session, owner.id)

    assert view_by_slug(session, owner.id, "food").patterns == ["PANADERIA"]


def test_reset_restores_builtin_name_and_keywords(session):
    owner = create_user(session, "owner", "owner@example.com")
    housing = get_global_category_by_slug(session, "housing")
    default_keywords = view_by_slug(session, owner.id, "housing").patterns

    update_category(session, owner.id, housing.id, CategoryUpdate(name="Casa", patterns=["ARRIENDO DEPTO"]))
    reset_builtin_category(session, owner.id, housing.id)

    restored = view_by_slug(session, owner.id, "housing")
    assert restored.name == "Vivienda"
    assert restored.patterns == default_keywords
    assert restored.is_modified is False
    assert session.exec(select(CategoryPattern).where(CategoryPattern.user_id == owner.id)).all() == []


def test_reset_rejects_custom_categories(session):
    owner = create_user(session, "owner", "owner@example.com")
    category = create_custom_category(session, owner.id, CategoryCreate(name="Mascotas"))

    with pytest.raises(ValueError, match="cannot be reset"):
        reset_builtin_category(session, owner.id, category.id)


def test_updating_a_custom_category_edits_it_in_place(session):
    owner = create_user(session, "owner", "owner@example.com")
    category = create_custom_category(session, owner.id, CategoryCreate(name="Mascotas", pattern="PETSHOP"))

    update_category(session, owner.id, category.id, CategoryUpdate(name="Mascotas y vet", patterns=["VET"]))

    view = next(view for view in list_category_views(session, owner.id) if view.id == category.id)
    assert view.name == "Mascotas y vet"
    assert view.patterns == ["VET"]
    assert view.is_custom is True
    assert resolve_category_for_user_text(session, owner.id, "PETSHOP CENTRO", "general").slug == "general"


def test_update_rejects_a_name_taken_by_another_visible_category(session):
    owner = create_user(session, "owner", "owner@example.com")
    category = create_custom_category(session, owner.id, CategoryCreate(name="Mascotas"))

    with pytest.raises(ValueError, match="Category already exists"):
        update_category(session, owner.id, category.id, CategoryUpdate(name="Comida"))


def test_update_rejects_another_users_category(session):
    owner = create_user(session, "owner", "owner@example.com")
    other = create_user(session, "other", "other@example.com")
    category = create_custom_category(session, owner.id, CategoryCreate(name="Mascotas"))

    with pytest.raises(CategoryNotFoundError):
        update_category(session, other.id, category.id, CategoryUpdate(name="Robado"))


def test_creating_a_category_accepts_several_keywords(session):
    owner = create_user(session, "owner", "owner@example.com")

    category = create_custom_category(
        session, owner.id, CategoryCreate(name="Mascotas", patterns=["PETSHOP", " vet ", "petshop", ""])
    )

    view = next(view for view in list_category_views(session, owner.id) if view.id == category.id)
    assert view.patterns == ["PETSHOP", "vet"]


def test_deleting_a_custom_category_moves_its_transactions_to_general(session):
    owner = create_user(session, "owner", "owner@example.com")
    category = create_custom_category(session, owner.id, CategoryCreate(name="Mascotas"))
    general = get_global_category_by_slug(session, "general")

    session.add(
        Expense(
            user_id=owner.id,
            commerce="PETSHOP",
            amount=1000,
            category_id=category.id,
            date=datetime.now(UTC),
        )
    )
    session.add(
        Transference(
            user_id=owner.id,
            recipient="PETSHOP",
            amount=2000,
            category_id=category.id,
            date=datetime.now(UTC),
        )
    )
    session.commit()

    reassigned = delete_custom_category(session, owner.id, category.id)

    assert reassigned == 2
    assert session.get(Category, category.id) is None
    assert {expense.category_id for expense in session.exec(select(Expense)).all()} == {general.id}
    assert {t.category_id for t in session.exec(select(Transference)).all()} == {general.id}


def test_deleting_a_builtin_category_is_rejected(session):
    owner = create_user(session, "owner", "owner@example.com")
    housing = get_global_category_by_slug(session, "housing")

    with pytest.raises(ValueError, match="cannot be deleted"):
        delete_custom_category(session, owner.id, housing.id)


def test_recategorize_backfills_existing_transactions(session):
    owner = create_user(session, "owner", "owner@example.com")
    general = get_global_category_by_slug(session, "general")
    housing = get_global_category_by_slug(session, "housing")
    default_keywords = view_by_slug(session, owner.id, "housing").patterns

    session.add(
        Expense(
            user_id=owner.id,
            commerce="PAGO JUNTA DE VECINOS",
            amount=50000,
            category_id=general.id,
            date=datetime.now(UTC),
        )
    )
    session.add(
        Transference(
            user_id=owner.id,
            recipient="ADMIN JUNTA DE VECINOS",
            amount=30000,
            category_id=general.id,
            date=datetime.now(UTC),
        )
    )
    session.commit()

    update_category(
        session,
        owner.id,
        housing.id,
        CategoryUpdate(patterns=[*default_keywords, "JUNTA DE VECINOS"]),
    )
    updated = recategorize_transactions(session, owner.id)

    assert updated == {"expenses": 1, "transferences": 1}
    assert session.exec(select(Expense)).first().category_id == housing.id
    assert session.exec(select(Transference)).first().category_id == housing.id


def test_recategorize_leaves_unmatched_transactions_alone(session):
    owner = create_user(session, "owner", "owner@example.com")
    category = create_custom_category(session, owner.id, CategoryCreate(name="Mascotas"))

    session.add(
        Expense(
            user_id=owner.id,
            commerce="ALGO SIN PALABRA CLAVE",
            amount=1000,
            category_id=category.id,
            date=datetime.now(UTC),
        )
    )
    session.commit()

    updated = recategorize_transactions(session, owner.id)

    assert updated == {"expenses": 0, "transferences": 0}
    assert session.exec(select(Expense)).first().category_id == category.id


def test_recategorize_ignores_other_users_transactions(session):
    owner = create_user(session, "owner", "owner@example.com")
    other = create_user(session, "other", "other@example.com")
    general = get_global_category_by_slug(session, "general")
    create_custom_category(session, owner.id, CategoryCreate(name="Mascotas", pattern="PETSHOP"))

    session.add(
        Expense(
            user_id=other.id,
            commerce="PETSHOP CENTRO",
            amount=1000,
            category_id=general.id,
            date=datetime.now(UTC),
        )
    )
    session.commit()

    updated = recategorize_transactions(session, owner.id)

    assert updated == {"expenses": 0, "transferences": 0}
    assert session.exec(select(Expense)).first().category_id == general.id


@pytest.fixture
def client(engine) -> Iterator[TestClient]:
    with Session(engine) as setup_session:
        user = create_user(setup_session, "api-user", "api@example.com")
        user_id = user.id

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    def override_user() -> User:
        with Session(engine) as session:
            return session.get(User, user_id)

    server.app.dependency_overrides[get_session] = override_session
    server.app.dependency_overrides[get_current_user] = override_user
    test_client = TestClient(server.app)
    test_client.user_id = user_id
    yield test_client
    server.app.dependency_overrides.clear()


def category_payload(client: TestClient, slug: str) -> dict:
    response = client.get("/categories")
    assert response.status_code == 200
    return next(category for category in response.json() if category["slug"] == slug)


def test_categories_endpoint_exposes_keywords_and_custom_flags(client):
    housing = category_payload(client, "housing")

    assert housing["is_custom"] is False
    assert housing["is_modified"] is False
    assert "DIVIDENDO" in [pattern.upper() for pattern in housing["patterns"]]


def test_patch_category_persists_keywords_and_rename(client):
    housing = category_payload(client, "housing")

    response = client.patch(
        f"/categories/{housing['id']}",
        json={"name": "Casa", "patterns": [*housing["patterns"], "JUNTA DE VECINOS"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Casa"
    assert body["is_modified"] is True
    assert "JUNTA DE VECINOS" in body["patterns"]
    assert category_payload(client, "housing")["name"] == "Casa"


def test_reset_endpoint_restores_defaults(client):
    housing = category_payload(client, "housing")
    client.patch(f"/categories/{housing['id']}", json={"name": "Casa", "patterns": ["JUNTA DE VECINOS"]})

    response = client.post(f"/categories/{housing['id']}/reset")

    assert response.status_code == 200
    assert response.json()["name"] == "Vivienda"
    assert category_payload(client, "housing")["is_modified"] is False


def test_delete_endpoint_rejects_builtin_categories(client):
    housing = category_payload(client, "housing")

    response = client.delete(f"/categories/{housing['id']}")

    assert response.status_code == 400


def test_delete_endpoint_removes_a_custom_category(client):
    created = client.post("/categories", json={"name": "Mascotas", "patterns": ["PETSHOP"]})
    assert created.status_code == 201

    response = client.delete(f"/categories/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json()["reassigned_expenses"] == 0
    assert all(category["slug"] != created.json()["slug"] for category in client.get("/categories").json())


def test_recategorize_endpoint_reports_updated_rows(client, engine):
    general_id = category_payload(client, "general")["id"]
    with Session(engine) as session:
        session.add(
            Expense(
                user_id=client.user_id,
                commerce="PETSHOP CENTRO",
                amount=1000,
                category_id=general_id,
                date=datetime.now(UTC),
            )
        )
        session.commit()

    client.post("/categories", json={"name": "Mascotas", "patterns": ["PETSHOP"]})
    response = client.post("/categories/recategorize")

    assert response.status_code == 200
    assert response.json()["expenses_updated"] == 1
    assert client.get("/expenses").json()[0]["category_name"] == "Mascotas"


def test_expenses_use_the_users_renamed_category(client, engine):
    housing = category_payload(client, "housing")
    client.patch(f"/categories/{housing['id']}", json={"name": "Casa"})
    with Session(engine) as session:
        session.add(
            Expense(
                user_id=client.user_id,
                commerce="PAGO DIVIDENDO",
                amount=1000,
                category_id=housing["id"],
                date=datetime.now(UTC),
            )
        )
        session.commit()

    expenses = client.get("/expenses").json()

    assert expenses[0]["category_name"] == "Casa"
