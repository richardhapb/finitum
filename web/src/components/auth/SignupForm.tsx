import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import { authApi, banksApi } from '../../lib/api';

const signupSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.email('Invalid email address'),
  bank: z.string(),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
  termsAccepted: z.boolean(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
}).refine((data) => data.termsAccepted, {
  message: "Terms of services should be accepted",
  path: ['termsAccepted']
})

type SignupFormData = z.infer<typeof signupSchema>;

export function SignupForm() {
  const navigate = useNavigate();

  const { data: banks = [] } = useQuery({
    queryKey: ['banks'],
    queryFn: banksApi.getAll,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      bank: 'banco_chile',
    },
  });

  const signupMutation = useMutation({
    mutationFn: (data: SignupFormData) =>
      authApi.signup(data.username, data.email, data.password, data.bank),
    onSuccess: () => {
      alert('Account created! Please login.');
      navigate('/login');
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Signup failed');
    },
  });

  const onSubmit = (data: SignupFormData) => {
    signupMutation.mutate(data);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-white">Sign Up</h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Username</label>
            <input
              {...register('username')}
              type="text"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.username && (
              <p className="text-red-400 text-sm mt-1">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Email</label>
            <input
              {...register('email')}
              type="email"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.email && (
              <p className="text-red-400 text-sm mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Bank</label>
            <select
              {...register('bank')}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {banks.map((bank) => (
                <option key={bank.id} value={bank.id}>
                  {bank.name}
                </option>
              ))}
            </select>
            {errors.bank && (
              <p className="text-red-400 text-sm mt-1">{errors.bank.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Password</label>
            <input
              {...register('password')}
              type="password"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.password && (
              <p className="text-red-400 text-sm mt-1">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Confirm Password</label>
            <input
              {...register('confirmPassword')}
              type="password"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.confirmPassword && (
              <p className="text-red-400 text-sm mt-1">
                {errors.confirmPassword.message}
              </p>
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <input
                {...register('termsAccepted')}
                type="checkbox"
                className="h-4 w-4"
              />
              <label className="text-sm font-medium text-gray-300">Accept the terms of service</label>
            </div>
            {errors.termsAccepted && (
              <p className="text-red-400 text-sm mt-1 ml-6">
                {errors.termsAccepted.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={signupMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-600"
          >
            {signupMutation.isPending ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <p className="text-center mt-4 text-sm text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-400 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
