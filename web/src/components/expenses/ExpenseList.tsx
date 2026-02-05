import { useQuery } from '@tanstack/react-query';
import { expensesApi } from '../../lib/api';
import type { Expense } from '../../types/models';

const CATEGORY_COLORS: Record<string, string> = {
  FOOD: 'bg-orange-500/20 text-orange-400',
  EXTERNAL_FOOD: 'bg-orange-500/20 text-orange-400',
  TRANSPORT: 'bg-blue-500/20 text-blue-400',
  ENTERTAINMENT: 'bg-purple-500/20 text-purple-400',
  RECREATION: 'bg-purple-500/20 text-purple-400',
  SHOPPING: 'bg-pink-500/20 text-pink-400',
  CLOTHING: 'bg-pink-500/20 text-pink-400',
  SERVICES: 'bg-gray-500/20 text-gray-400',
  HEALTH: 'bg-red-500/20 text-red-400',
  EDUCATION: 'bg-cyan-500/20 text-cyan-400',
  HOUSING: 'bg-amber-500/20 text-amber-400',
  TRANSFERS: 'bg-green-500/20 text-green-400',
  ATM_WITHDRAWAL: 'bg-green-500/20 text-green-400',
  ONLINE: 'bg-indigo-500/20 text-indigo-400',
  TRAVEL: 'bg-teal-500/20 text-teal-400',
  SPORTS: 'bg-lime-500/20 text-lime-400',
  GENERAL: 'bg-slate-500/20 text-slate-400',
};

const formatCategoryName = (name: string) => {
  return name
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

export function ExpenseList() {
  const { data: expenses, isLoading, error } = useQuery({
    queryKey: ['expenses'],
    queryFn: expensesApi.getAll,
  });

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-center text-gray-400">Loading expenses...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-center text-red-400">
          Error loading expenses: {error.message}
        </div>
      </div>
    );
  }

  if (!expenses || expenses.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-center text-gray-500">
          No expenses yet. Add your first expense or connect Gmail to import automatically.
        </div>
      </div>
    );
  }

  // Sort by date (newest first)
  const sortedExpenses = [...expenses].sort((a, b) =>
    new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  const formatCurrency = (amount: number, currency: string) => {
    if (currency === 'CLP') {
      return `$${amount.toLocaleString('es-CL', { maximumFractionDigits: 0 })}`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const getCategoryStyle = (category: string) => {
    return CATEGORY_COLORS[category.toUpperCase()] || CATEGORY_COLORS.GENERAL;
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Recent Transactions</h2>
        <p className="text-sm text-gray-400">{expenses.length} total</p>
      </div>
      <div className="divide-y divide-gray-700 max-h-[500px] overflow-y-auto">
        {sortedExpenses.map((expense: Expense) => (
          <div
            key={expense.id}
            className="p-4 hover:bg-gray-750 transition-colors"
          >
            <div className="flex justify-between items-start gap-3">
              <div className="min-w-0 flex-1">
                <h3 className="font-medium text-white truncate">{expense.commerce}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryStyle(expense.category)}`}>
                    {formatCategoryName(expense.category)}
                  </span>
                  <span className="text-xs text-gray-500">{formatDate(expense.date)}</span>
                </div>
                {expense.description && (
                  <p className="text-sm text-gray-500 mt-1 truncate">{expense.description}</p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <p className="font-semibold text-white">
                  {formatCurrency(expense.amount, expense.currency)}
                </p>
                <p className="text-xs text-gray-500">{expense.currency}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
