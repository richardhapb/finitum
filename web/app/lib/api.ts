import type {
  Bank,
  Category,
  CreateCategoryRequest,
  CreateExpenseRequest,
  DeleteCategoryResponse,
  Expense,
  GenericResponse,
  IngestAddress,
  IngestConfirmationResponse,
  RecategorizeResponse,
  Transference,
  UpdateCategoryRequest,
  User,
  UserLoginResponse,
  UserUpdate,
} from "../types/models";
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9090';

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Auth API
export const authApi = {
  signup: async (
    username: string,
    email: string,
    password: string,
    bank: string,
  ): Promise<User> => {
    const response = await api.post<User>("/signup", {
      username,
      email,
      password,
      bank,
    });
    return response.data;
  },

  signin: async (
    usernameOrEmail: string,
    password: string,
  ): Promise<UserLoginResponse> => {
    // Check if input is email or username
    const isEmail = usernameOrEmail.includes("@");
    const payload = isEmail
      ? { email: usernameOrEmail, password }
      : { username: usernameOrEmail, password };

    const response = await api.post<UserLoginResponse>("/signin", payload);
    return response.data;
  },

  logout: async (): Promise<GenericResponse> => {
    const response = await api.get<GenericResponse>("/logout");
    return response.data
  },

  validateSession: async (): Promise<GenericResponse> => {
    const response = await api.get<GenericResponse>("/session");
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>("/me");
    return response.data;
  },

  updateMe: async (data: UserUpdate): Promise<User> => {
    const response = await api.patch<User>("/me", data);
    return response.data;
  },

  getGoogleAuthUrl: (): string => {
    return `${API_URL}/google-authorize`;
  },
};

// Banks API
export const banksApi = {
  getAll: async (): Promise<Bank[]> => {
    const response = await api.get<Bank[]>("/banks");
    return response.data;
  },
};

// Expenses API
export const expensesApi = {
  getAll: async (): Promise<Expense[]> => {
    const response = await api.get<Expense[]>("/expenses");
    return response.data;
  },

  create: async (expense: CreateExpenseRequest): Promise<Expense> => {
    const response = await api.post<Expense>("/expenses", expense);
    return response.data;
  },

  delete: async (id: Number): Promise<GenericResponse> => {
    const response = await api.delete<GenericResponse>(`/expenses/${id}`);
    return response.data;
  },
};

// Transferences API
export const transferencesApi = {
  getAll: async (): Promise<Transference[]> => {
    const response = await api.get<Transference[]>("/transferences");
    return response.data;
  },

  delete: async (id: Number): Promise<GenericResponse> => {
    const response = await api.delete<GenericResponse>(`/transferences/${id}`);
    return response.data;
  },
};

export const categoriesApi = {
  getAll: async (): Promise<Category[]> => {
    const response = await api.get<Category[]>("/categories");
    return response.data;
  },

  create: async (payload: CreateCategoryRequest): Promise<Category> => {
    const response = await api.post<Category>("/categories", payload);
    return response.data;
  },

  update: async (id: number, payload: UpdateCategoryRequest): Promise<Category> => {
    const response = await api.patch<Category>(`/categories/${id}`, payload);
    return response.data;
  },

  /** Restore a built-in category to its default name and keywords. */
  reset: async (id: number): Promise<Category> => {
    const response = await api.post<Category>(`/categories/${id}/reset`);
    return response.data;
  },

  remove: async (id: number): Promise<DeleteCategoryResponse> => {
    const response = await api.delete<DeleteCategoryResponse>(`/categories/${id}`);
    return response.data;
  },

  /** Re-apply the current keywords to already stored transactions. */
  recategorize: async (): Promise<RecategorizeResponse> => {
    const response = await api.post<RecategorizeResponse>("/categories/recategorize");
    return response.data;
  },
};

// Forwarding ingestion API
export const ingestApi = {
  getAddress: async (): Promise<IngestAddress> => {
    const response = await api.get<IngestAddress>("/ingest/address");
    return response.data;
  },

  getConfirmation: async (): Promise<IngestConfirmationResponse> => {
    const response = await api.get<IngestConfirmationResponse>("/ingest/confirmation");
    return response.data;
  },
};
