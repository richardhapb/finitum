// User types
export interface User {
  id: string;
  username: string;
  email: string;
  bank: string;
  last_update: string;
  has_google_credentials?: boolean;
  is_google_credentials_valid?: boolean;
  // Forwarding ingestion status (replaces has_gmail_scope).
  ingest_address?: string | null;
  forwarding_active?: boolean;
  last_email_received_at?: string | null;
  verification_scan_enabled?: boolean;
}

export interface IngestAddress {
  address: string;
}

export interface ForwardingConfirmation {
  url?: string;
  code?: string;
}

export interface IngestConfirmationResponse {
  confirmation: ForwardingConfirmation | null;
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
  senders?: string[];
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
  id: number;
  user_id: number;
  commerce: string;
  amount: number;
  currency: string;
  category_id: number;
  category_slug: string;
  category_name: string;
  category_is_custom: boolean;
  date: string;
  description?: string;
}

export interface CreateExpenseRequest {
  commerce: string;
  amount: number;
  currency: string;
  category_id: number;
  date?: string;
  description?: string;
}

// Transference types
export interface Transference {
  id: number;
  user_id: number;
  recipient: string;
  amount: number;
  currency: string;
  category: string;
  category_slug: string;
  category_name: string;
  date: string;
  description?: string;
}

export interface Category {
  id: number;
  slug: string;
  name: string;
  name_en: string;
  name_es: string;
  is_custom: boolean;
  patterns: string[];
}

export interface CreateCategoryRequest {
  name: string;
  pattern?: string;
}

export interface GenericResponse {
  msg: string;
}

export interface EmailScanResponse {
  msg: string;
  task_id: string;
}
