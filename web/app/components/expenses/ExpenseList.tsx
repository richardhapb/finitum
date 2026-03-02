import { useQuery } from '@tanstack/react-query';
import { expensesApi } from '../../lib/api';
import { DEFAULT_LOCALE, getExpenseCategoryName } from '../../lib/categories';
import type { Expense } from '../../types/models';
import { useMemo } from 'react';
import { queryClient } from '../../lib/queryClient';

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

async function handleDelete(expenseId: number) {
  if (!window.confirm('Quieres eliminar este gasto?')) return;
  try {
    await expensesApi.delete(expenseId); 
    queryClient.invalidateQueries({ queryKey: ['expenses'] });
  } catch (error) {
    console.error('Failed to delete expense:', error);
    alert('No se pudo eliminar el gasto. Intentalo de nuevo.');
  }
}

export function ExpenseList() {
  const { data: expenses = [], isLoading, error } = useQuery({
    queryKey: ['expenses'],
    queryFn: expensesApi.getAll,
  });

  // Derived + memoized sorted list (newest first)
  const sortedExpenses = useMemo(() => {
    if (!expenses.length) return [];
    return [...expenses].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [expenses]);

  const formatCurrency = (amount: number, currency: string) => {
    const normalizedCurrency = currency.toUpperCase();
    if (normalizedCurrency === 'CLP') {
      return `$${amount.toLocaleString(DEFAULT_LOCALE, { maximumFractionDigits: 0 })}`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: normalizedCurrency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) return 'Hoy';
    if (date.toDateString() === yesterday.toDateString()) return 'Ayer';
    return date.toLocaleDateString(DEFAULT_LOCALE, { month: 'short', day: 'numeric' });
  };

  const getCategoryStyle = (categorySlug: string) =>
    CATEGORY_COLORS[categorySlug.toUpperCase()] || CATEGORY_COLORS.GENERAL;

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-center text-gray-400">Cargando gastos...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-center text-red-400">
          Error cargando gastos: {(error as Error).message}
        </div>
      </div>
    );
  }

  if (sortedExpenses.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-center text-gray-500">
          Aun no hay gastos. Agrega el primero o conecta Gmail para importarlos automaticamente.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Transacciones recientes</h2>
        <p className="text-sm text-gray-400">{sortedExpenses.length} total</p>
      </div>

      <div className="divide-y divide-gray-700 max-h-125 overflow-y-auto"> {/* ← fixed height example */}
        {sortedExpenses.map((expense: Expense) => (
          <div
            key={expense.id}
            className="p-4 hover:bg-gray-750 transition-colors"
          >
            <div className="flex justify-between items-start gap-3">
              <div className="min-w-0 flex-1">
                <h3 className="font-medium text-white truncate">{expense.commerce}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${getCategoryStyle(expense.category_slug)}`}
                  >
                    {getExpenseCategoryName(expense)}
                  </span>
                  <span className="text-xs text-gray-500">{formatDate(expense.date)}</span>
                </div>
                {expense.description && (
                  <p className="text-sm text-gray-500 mt-1 truncate">{expense.description}</p>
                )}
              </div>

              <div className="text-right shrink-0">
                <p className="font-semibold text-white">
                  {formatCurrency(expense.amount, expense.currency)}
                </p>
                <p className="text-xs text-gray-500">{expense.currency.toUpperCase()}</p>
              </div>

              <button
                onClick={() => handleDelete(expense.id)}
                className="text-red-400 hover:text-red-300 transition-colors"
                title="Eliminar gasto"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
                  />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
