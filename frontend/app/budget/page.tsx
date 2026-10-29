import React, { Suspense } from "react";
import { BudgetClient } from "@/components/budget/BudgetClient";

export default function BudgetPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm font-bold">Loading Budget Planner...</div>}>
      <BudgetClient />
    </Suspense>
  );
}
