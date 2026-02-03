import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { expensesApi } from '../../lib/api';
import type { Expense } from '../../types/models';

const COLORS = [
  '#3b82f6', // blue
  '#ef4444', // red
  '#10b981', // green
  '#f59e0b', // yellow
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
];

export function ExpenseChart() {
  const { data: expenses, isLoading } = useQuery({
    queryKey: ['expenses'],
    queryFn: expensesApi.getAll,
  });

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading charts...</div>;
  }

  if (!expenses || expenses.length === 0) {
    return null;
  }

  // Group by category
  const categoryData = expenses.reduce((acc: Record<string, number>, expense: Expense) => {
    const category = expense.category || 'Other';
    acc[category] = (acc[category] || 0) + expense.amount;
    return acc;
  }, {});

  const categoryChartData = Object.entries(categoryData).map(([name, value]) => ({
    name,
    value: Number(value.toFixed(2)),
  }));

  // Group by month (last 6 months)
  const monthlyData = expenses.reduce((acc: Record<string, number>, expense: Expense) => {
    const date = new Date(expense.date);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    acc[monthKey] = (acc[monthKey] || 0) + expense.amount;
    return acc;
  }, {});

  const monthlyChartData = Object.entries(monthlyData)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-6) // Last 6 months
    .map(([month, amount]) => {
      const [year, monthNum] = month.split('-');
      const monthName = new Date(parseInt(year), parseInt(monthNum) - 1).toLocaleDateString('en-US', { month: 'short' });
      return {
        month: monthName,
        amount: Number(amount.toFixed(2)),
      };
    });

  // Calculate total
  const total = expenses.reduce((sum, exp) => sum + exp.amount, 0);

  return (
    <div className="space-y-6">
      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg border border-gray-700">
          <p className="text-sm text-gray-300">Total Expenses</p>
          <p className="text-2xl font-bold">${total.toFixed(2)}</p>
        </div>
        <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg border border-gray-700">
          <p className="text-sm text-gray-300">Transactions</p>
          <p className="text-2xl font-bold">{expenses.length}</p>
        </div>
        <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg border border-gray-700">
          <p className="text-sm text-gray-300">Average</p>
          <p className="text-2xl font-bold">${(total / expenses.length).toFixed(2)}</p>
        </div>
      </div>

      {/* Monthly Spending Chart */}
      <div className="bg-gray-800 text-white p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 className="text-lg font-bold mb-4">Monthly Spending</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyChartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="month" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              cursor={{ fill: '#374151', opacity: 0.3 }}
              formatter={(value: number | undefined) => value != null ? `$${value.toFixed(2)}` : ''}
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '6px',
                color: '#fff'
              }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend wrapperStyle={{ color: '#fff' }} />
            <Bar dataKey="amount" fill="#3b82f6" name="Amount ($)" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Category Breakdown */}
      <div className="bg-gray-800 text-white p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 className="text-lg font-bold mb-4">Spending by Category</h3>
        <div className="flex flex-col md:flex-row items-center gap-8">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }: { name?: string | number; percent?: number }) => `${name ?? ''}: ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryChartData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number | undefined) => value != null ? `$${value.toFixed(2)}` : ''}
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#fff'
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Category Legend with amounts */}
          <div className="w-full md:w-auto">
            <div className="space-y-2">
              {categoryChartData.map((item, index) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-sm text-gray-200">
                    {item.name}: ${item.value.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
