import { Navbar } from "../components/layout/Navbar";
import { ExpenseForm } from "../components/expenses/ExpenseForm";
import { ExpenseList } from "../components/expenses/ExpenseList";
import { ExpenseChart } from "../components/expenses/ExpenseChart";
import { useEffect } from "react";
import { useSearchParams } from "react-router";

export default function DashboardPage() {
  const [searchParams] = useSearchParams();
  const gmailScanStatus = searchParams.get("gmail_scan");

  useEffect(() => {
    if (!gmailScanStatus) {
      return;
    }
    const url = new URL(window.location.href);
    url.searchParams.delete("gmail_scan");
    window.history.replaceState({}, "", url.toString());
  }, [gmailScanStatus]);

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">

        {/* Charts section - full width */}
        <div className="mb-6">
          <ExpenseChart />
        </div>

        {/* Form + List section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Add expense form - takes 1 column */}
          <div className="lg:col-span-1">
            <ExpenseForm />
          </div>

          {/* Expense list - takes 2 columns */}
          <div className="lg:col-span-2">
            <ExpenseList />
          </div>
        </div>
      </div>
    </div>
  );
}
