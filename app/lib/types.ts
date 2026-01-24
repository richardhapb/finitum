// Currency and category values must match backend enums (lowercase)
export type Currency = "usd" | "clp";

export type ExpenseCategory =
  | "general"
  | "food"
  | "education"
  | "transport"
  | "services"
  | "transfers"
  | "clothing"
  | "entertainment"
  | "sports"
  | "loan"
  | "atm_withdrawal"
  | "investments"
  | "housing"
  | "external_food"
  | "recreation"
  | "online"
  | "commissions"
  | "travel"
  | "health"
  | "family"
  | "laundry"
  | "books"
  | "purified_water";

export interface Expense {
  id: number;
  user_id: number;
  commerce: string;
  amount: number;
  currency: Currency;
  category: ExpenseCategory;
  date: string;
  description: string | null;
}

export interface User {
  id: number;
  username: string;
  email: string;
  last_update: string;
  has_google_credentials?: boolean;
}

export interface UserLoginResponse {
  user: User;
  access_token: string;
  token_type: string;
}

export interface CreateExpenseRequest {
  commerce: string;
  amount: number;
  currency?: Currency;
  category?: ExpenseCategory;
  date?: string;
  description?: string;
}

export const CATEGORY_LABELS: Record<ExpenseCategory, string> = {
  general: "General",
  food: "Food",
  education: "Education",
  transport: "Transport",
  services: "Services",
  transfers: "Transfers",
  clothing: "Clothing",
  entertainment: "Entertainment",
  sports: "Sports",
  loan: "Loan",
  atm_withdrawal: "ATM Withdrawal",
  investments: "Investments",
  housing: "Housing",
  external_food: "External Food",
  recreation: "Recreation",
  online: "Online",
  commissions: "Commissions",
  travel: "Travel",
  health: "Health",
  family: "Family",
  laundry: "Laundry",
  books: "Books",
  purified_water: "Purified Water",
};

export const CATEGORY_ICONS: Record<ExpenseCategory, string> = {
  general: "ellipsis-horizontal",
  food: "restaurant",
  education: "school",
  transport: "car",
  services: "build",
  transfers: "swap-horizontal",
  clothing: "shirt",
  entertainment: "game-controller",
  sports: "basketball",
  loan: "cash",
  atm_withdrawal: "cash-outline",
  investments: "trending-up",
  housing: "home",
  external_food: "fast-food",
  recreation: "happy",
  online: "globe",
  commissions: "card",
  travel: "airplane",
  health: "medkit",
  family: "people",
  laundry: "water",
  books: "book",
  purified_water: "water-outline",
};

export const ALL_CATEGORIES: ExpenseCategory[] = [
  "general",
  "food",
  "education",
  "transport",
  "services",
  "transfers",
  "clothing",
  "entertainment",
  "sports",
  "loan",
  "atm_withdrawal",
  "investments",
  "housing",
  "external_food",
  "recreation",
  "online",
  "commissions",
  "travel",
  "health",
  "family",
  "laundry",
  "books",
  "purified_water",
];

export const CURRENCIES: Currency[] = ["clp", "usd"];
