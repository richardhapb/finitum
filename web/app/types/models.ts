// User types
export interface User {
  id: string;
  username: string;
  email: string;
  bank: string;
  last_update: string;
  has_google_credentials?: boolean;
  is_google_credentials_valid?: boolean;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  bank: string;
}

export interface UserUpdate {
  username?: string;
  bank?: string;
}

export interface Bank {
  id: string;
  name: string;
}

export interface UserLogin {
  username?: string;
  email?: string;
  password: string;
}

export interface UserLoginResponse {
  user: User;
}

// Expense types
export interface Expense {
  id: string;
  user_id: string;
  commerce: string;
  amount: number;
  currency: string;
  category: string;
  date: string;
  description?: string;
}

export interface CreateExpenseRequest {
  commerce: string;
  amount: number;
  currency: string;
  category: string;
  date?: string;
  description?: string;
}

export interface GenericResponse {
  msg: string;
}
