import type {
  Bank,
  CreateExpenseRequest,
  Expense,
  GenericResponse,
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
};


