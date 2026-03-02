from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
KEYWORDS_PATH = ROOT_DIR / "categories.json"
SPANISH_LABELS_PATH = ROOT_DIR / "category_labels.es.json"
GENERAL_CATEGORY_SLUG = "general"

PARSER_CATEGORY_TO_SLUG: dict[str, str] = {
    "Food": "food",
    "Education": "education",
    "Transport": "transport",
    "Services": "services",
    "Transfers": "transfers",
    "Clothing": "clothing",
    "Entertainment": "entertainment",
    "Sports": "sports",
    "Loan": "loan",
    "ATM_withdrawal": "atm_withdrawal",
    "Investments": "investments",
    "Housing": "housing",
    "External_food": "external_food",
    "Recreation": "recreation",
    "Online": "online",
    "Commissions": "commissions",
    "Travel": "travel",
    "Health": "health",
    "Family": "family",
    "Laundry": "laundry",
    "Books": "books",
    "Purified_water": "purified_water",
}

ENGLISH_LABELS_BY_SLUG: dict[str, str] = {
    GENERAL_CATEGORY_SLUG: "Other",
    "food": "Food",
    "education": "Education",
    "transport": "Transport",
    "services": "Services",
    "transfers": "Transfers",
    "clothing": "Clothing",
    "entertainment": "Entertainment",
    "sports": "Sports",
    "loan": "Loan",
    "atm_withdrawal": "ATM Withdrawal",
    "investments": "Investments",
    "housing": "Housing",
    "external_food": "Restaurants",
    "recreation": "Recreation",
    "online": "Online",
    "commissions": "Commissions",
    "travel": "Travel",
    "health": "Health",
    "family": "Family",
    "laundry": "Laundry",
    "books": "Books",
    "purified_water": "Purified Water",
}

DEFAULT_SPANISH_LABELS_BY_SLUG: dict[str, str] = {
    "general": "Otros",
    "food": "Comida",
    "education": "Educacion",
    "transport": "Transporte",
    "services": "Servicios",
    "transfers": "Transferencias",
    "clothing": "Ropa",
    "entertainment": "Entretenimiento",
    "sports": "Deportes",
    "loan": "Prestamos",
    "atm_withdrawal": "Retiro en cajero",
    "investments": "Inversiones",
    "housing": "Vivienda",
    "external_food": "Restaurantes",
    "recreation": "Recreacion",
    "online": "En linea",
    "commissions": "Comisiones",
    "travel": "Viajes",
    "health": "Salud",
    "family": "Familia",
    "laundry": "Lavanderia",
    "books": "Libros",
    "purified_water": "Agua purificada",
}


@dataclass(frozen=True)
class CategoryDefinition:
    slug: str
    name_en: str
    name_es: str
    patterns: tuple[str, ...]
    parser_key: str | None = None


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as file_obj:
        data = json.load(file_obj)
    if not isinstance(data, dict):
        msg = f"Expected a JSON object in {path}"
        raise TypeError(msg)
    return data


def _load_spanish_labels() -> dict[str, object]:
    if SPANISH_LABELS_PATH.exists():
        return _load_json(SPANISH_LABELS_PATH)
    return dict(DEFAULT_SPANISH_LABELS_BY_SLUG)


@lru_cache
def get_builtin_category_definitions() -> tuple[CategoryDefinition, ...]:
    raw_keywords = _load_json(KEYWORDS_PATH)
    spanish_labels = _load_spanish_labels()

    definitions = [
        CategoryDefinition(
            slug=GENERAL_CATEGORY_SLUG,
            name_en=ENGLISH_LABELS_BY_SLUG[GENERAL_CATEGORY_SLUG],
            name_es=str(spanish_labels[GENERAL_CATEGORY_SLUG]),
            patterns=(),
        )
    ]

    for parser_key, slug in PARSER_CATEGORY_TO_SLUG.items():
        keywords = raw_keywords.get(parser_key, [])
        if not isinstance(keywords, list):
            msg = f"Expected a keyword list for parser category {parser_key}"
            raise TypeError(msg)

        name_es = spanish_labels.get(slug)
        if not isinstance(name_es, str):
            msg = f"Missing Spanish label for category slug {slug}"
            raise TypeError(msg)

        definitions.append(
            CategoryDefinition(
                slug=slug,
                name_en=ENGLISH_LABELS_BY_SLUG[slug],
                name_es=name_es,
                patterns=tuple(str(keyword) for keyword in keywords),
                parser_key=parser_key,
            )
        )

    return tuple(definitions)


@lru_cache
def get_builtin_category_by_slug() -> dict[str, CategoryDefinition]:
    return {definition.slug: definition for definition in get_builtin_category_definitions()}


@lru_cache
def get_builtin_category_by_parser_key() -> dict[str, CategoryDefinition]:
    return {
        definition.parser_key: definition
        for definition in get_builtin_category_definitions()
        if definition.parser_key is not None
    }


def get_builtin_category_slugs() -> tuple[str, ...]:
    return tuple(definition.slug for definition in get_builtin_category_definitions())


def slugify_category_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or GENERAL_CATEGORY_SLUG


def humanize_category_slug(slug: str) -> str:
    return slug.replace("_", " ").replace("-", " ").title()
