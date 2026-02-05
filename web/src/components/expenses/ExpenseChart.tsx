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
  ResponsiveContainer,
} from 'recharts';
import { expensesApi } from '../../lib/api';
import type { Expense } from '../../types/models';

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // yellow
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#84cc16', // lime
  '#14b8a6', // teal
  '#a855f7', // violet
  '#f43f5e', // rose
];

const formatCurrency = (value: number, currency = 'CLP') => {
  if (currency === 'USD') {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `$${value.toLocaleString('es-CL', { maximumFractionDigits: 0 })}`;
};

const formatCategoryName = (name: string) => {
  return name
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

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

  // Group by category and sort by value descending
  const categoryData = expenses.reduce((acc: Record<string, number>, expense: Expense) => {
    const category = expense.category || 'OTHER';
    acc[category] = (acc[category] || 0) + expense.amount;
    return acc;
  }, {});

  const categoryChartData = Object.entries(categoryData)
    .map(([name, value]) => ({
      name: formatCategoryName(name),
      value: Number(value.toFixed(2)),
    }))
    .sort((a, b) => b.value - a.value);

  // Group by month (last 6 months)
  const monthlyData = expenses.reduce((acc: Record<string, number>, expense: Expense) => {
    const date = new Date(expense.date);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    acc[monthKey] = (acc[monthKey] || 0) + expense.amount;
    return acc;
  }, {});

  const monthlyChartData = Object.entries(monthlyData)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-6)
    .map(([month, amount]) => {
      const [year, monthNum] = month.split('-');
      const monthName = new Date(parseInt(year), parseInt(monthNum) - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
      return {
        month: monthName,
        amount: Number(amount.toFixed(2)),
      };
    });

  // Calculate stats
  const total = expenses.reduce((sum, exp) => sum + exp.amount, 0);
  const thisMonth = new Date().toISOString().slice(0, 7);
  const thisMonthTotal = expenses
    .filter((exp) => exp.date.startsWith(thisMonth))
    .reduce((sum, exp) => sum + exp.amount, 0);

  return (
    <div className="space-y-6">
      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg border border-gray-700">
          <p className="text-sm text-gray-400">Total Expenses</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(total)}</p>
        </div>
        <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg border border-gray-700">
          <p className="text-sm text-gray-400">This Month</p>
          <p className="text-2xl font-bold text-blue-400">{formatCurrency(thisMonthTotal)}</p>
        </div>
        <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg border border-gray-700">
          <p className="text-sm text-gray-400">Transactions</p>
          <p className="text-2xl font-bold text-white">{expenses.length}</p>
        </div>
        <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg border border-gray-700">
          <p className="text-sm text-gray-400">Average</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(total / expenses.length)}</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Spending Chart */}
        <div className="bg-gray-800 text-white p-6 rounded-lg shadow-lg border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Monthly Spending</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={monthlyChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
              <XAxis
                dataKey="month"
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                axisLine={{ stroke: '#374151' }}
              />
              <YAxis
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                axisLine={{ stroke: '#374151' }}
                tickFormatter={(value) => value >= 1000000 ? `${(value / 1000000).toFixed(1)}M` : value >= 1000 ? `${(value / 1000).toFixed(0)}K` : value}
              />
              <Tooltip
                cursor={{ fill: '#374151', opacity: 0.3 }}
                formatter={(value: number | undefined) => value != null ? [formatCurrency(value), 'Amount'] : ['', '']}
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Category Breakdown - Pie Chart */}
        <div className="bg-gray-800 text-white p-6 rounded-lg shadow-lg border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Spending by Category</h3>
          <div className="flex items-center">
            <div className="w-1/2">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {categoryChartData.map((_entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                        stroke="#1f2937"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number | undefined, _name, props) => {
                      const percent = ((value || 0) / total * 100).toFixed(1);
                      return value != null ? [`${formatCurrency(value)} (${percent}%)`, props.payload.name] : ['', ''];
                    }}
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#fff',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Category Legend with amounts */}
            <div className="w-1/2 pl-4 max-h-70 overflow-y-auto">
              <div className="space-y-2">
                {categoryChartData.slice(0, 8).map((item, index) => {
                  const percent = ((item.value / total) * 100).toFixed(1);
                  return (
                    <div key={item.name} className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div
                          className="w-3 h-3 rounded-sm shrink-0"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="text-sm text-gray-300 truncate">{item.name}</span>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-sm font-medium text-white">{percent}%</span>
                      </div>
                    </div>
                  );
                })}
                {categoryChartData.length > 8 && (
                  <p className="text-xs text-gray-500 pt-1">+{categoryChartData.length - 8} more categories</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top Categories Bar */}
      <div className="bg-gray-800 text-white p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Top Spending Categories</h3>
        <div className="space-y-3">
          {categoryChartData.slice(0, 5).map((item, index) => {
            const percent = (item.value / total) * 100;
            return (
              <div key={item.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">{item.name}</span>
                  <span className="text-white font-medium">{formatCurrency(item.value)}</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${percent}%`,
                      backgroundColor: COLORS[index % COLORS.length],
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
