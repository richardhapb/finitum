import type { Expense } from "../types/models";

export const DEFAULT_LOCALE = "es-CL";

export function fallbackCategoryName(slug: string): string {
  return slug
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function getExpenseCategoryName(expense: Expense): string {
  if (expense.category_name) {
    return expense.category_name;
  }

  return fallbackCategoryName(expense.category_slug);
}
