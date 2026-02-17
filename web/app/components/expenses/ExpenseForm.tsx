import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { expensesApi } from '../../lib/api';

const CATEGORIES = [
  { value: 'food', label: 'Food' },
  { value: 'external_food', label: 'Restaurants' },
  { value: 'transport', label: 'Transport' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'recreation', label: 'Recreation' },
  { value: 'clothing', label: 'Clothing' },
  { value: 'services', label: 'Services' },
  { value: 'health', label: 'Health' },
  { value: 'education', label: 'Education' },
  { value: 'housing', label: 'Housing' },
  { value: 'online', label: 'Online' },
  { value: 'travel', label: 'Travel' },
  { value: 'sports', label: 'Sports' },
  { value: 'family', label: 'Family' },
  { value: 'general', label: 'Other' },
];

const expenseSchema = z.object({
  commerce: z.string().min(1, 'Commerce name is required'),
  amount: z.coerce.number().positive('Amount must be positive'),
  currency: z.string().min(1, 'Currency is required'),
  category: z.string().min(1, 'Category is required'),
  description: z.string().optional(),
  date: z.string().optional(),
});

type ExpenseFormData = z.infer<typeof expenseSchema>;

export function ExpenseForm() {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ExpenseFormData>({
    resolver: zodResolver(expenseSchema) as any,
    defaultValues: {
      currency: 'clp',
      category: 'general',
      date: new Date().toISOString().split('T')[0],
    },
  });

  const createExpenseMutation = useMutation({
    mutationFn: expensesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      reset({
        currency: 'clp',
        category: 'general',
        date: new Date().toISOString().split('T')[0],
        commerce: '',
        amount: undefined,
        description: '',
      });
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail;
      let message = 'Failed to add expense';
      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
      }
      alert(message);
    },
  });

  const onSubmit = (data: ExpenseFormData) => {
    createExpenseMutation.mutate(data);
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
      <h2 className="text-xl font-bold mb-4 text-white">Add Expense</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-200">Commerce</label>
            <input
              {...register('commerce')}
              type="text"
              placeholder="e.g., Starbucks"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
            />
            {errors.commerce && (
              <p className="text-red-400 text-sm mt-1">{errors.commerce.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-200">Category</label>
            <select
              {...register('category')}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
            {errors.category && (
              <p className="text-red-400 text-sm mt-1">{errors.category.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-200">Amount</label>
              <input
                {...register('amount')}
                type="number"
                step="0.01"
                placeholder="0.00"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
              />
              {errors.amount && (
                <p className="text-red-400 text-sm mt-1">{errors.amount.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-200">Currency</label>
              <select
                {...register('currency')}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="clp">CLP</option>
                <option value="usd">USD</option>
              </select>
              {errors.currency && (
                <p className="text-red-400 text-sm mt-1">{errors.currency.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-200">Date</label>
            <input
              {...register('date')}
              type="date"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.date && (
              <p className="text-red-400 text-sm mt-1">{errors.date.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-200">
              Description (optional)
            </label>
            <textarea
              {...register('description')}
              rows={3}
              placeholder="Additional notes..."
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={createExpenseMutation.isPending}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
        >
          {createExpenseMutation.isPending ? 'Adding...' : 'Add Expense'}
        </button>
      </form>
    </div>
  );
}
