import { useQuery } from '@tanstack/react-query';
import { expensesApi } from '../../lib/api';
import type { Expense } from '../../types/models';

export function ExpenseList() {
  const { data: expenses, isLoading, error } = useQuery({
    queryKey: ['expenses'],
    queryFn: expensesApi.getAll,
  });

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading expenses...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-400">
        Error loading expenses: {error.message}
      </div>
    );
  }

  if (!expenses || expenses.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No expenses yet. Add your first expense!
      </div>
    );
  }

  // Sort by date (newest first)
  const sortedExpenses = [...expenses].sort((a, b) =>
    new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (

    <div className="dark-scroll space-y-3 max-h-150 overflow-y-auto pr-2">
      <h2 className="text-xl font-bold mb-4 text-white sticky top-0 bg-gray-900 pb-2 z-10">Recent Expenses</h2>
      {sortedExpenses.map((expense: Expense) => (
        <div
          key={expense.id}
          className="bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-700 hover:border-gray-600 transition-all"
        >
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-semibold text-lg text-white">{expense.commerce}</h3>
              <p className="text-sm text-gray-400 mt-1">
                {expense.category}
              </p>
              {expense.description && (
                <p className="text-sm text-gray-500 mt-1">{expense.description}</p>
              )}
            </div>
            <div className="text-right">
              <p className="font-bold text-lg text-white">
                {formatCurrency(expense.amount, expense.currency)}
              </p>
              <p className="text-sm text-gray-400">{formatDate(expense.date)}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
