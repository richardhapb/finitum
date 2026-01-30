import type {
    CreateExpenseRequest,
    Expense,
    User,
    UserLoginResponse,
} from "../types/models";
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9090';

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

// Request interceptor: add access token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 with refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't tried refreshing yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Another request is already refreshing, queue this one
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(
          `${API_URL}/refresh`,
          {},
          { withCredentials: true }
        );

        const newToken = data.access_token;
        localStorage.setItem('access_token', newToken);

        processQueue(null, newToken);

        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);


// Auth API
export const authApi = {
    signup: async (
        username: string,
        email: string,
        password: string,
    ): Promise<User> => {
        const response = await api.post<User>("/signup", {
            username,
            email,
            password,
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

    getMe: async (): Promise<User> => {
        const response = await api.get<User>("/me");
        return response.data;
    },

    getGoogleAuthUrl: (): string => {
        return `${API_URL}/google-authorize`;
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
