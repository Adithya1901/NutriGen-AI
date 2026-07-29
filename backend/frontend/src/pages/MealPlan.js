import { useState } from "react";
import api from "../api";

function MealPlan() {

  const [plan, setPlan] = useState("");

  const load = async () => {
    const res =
      await api.get("/families/1/mealplan");

    setPlan(res.data.plan);
  };

  return (
    <div>
      <h1>Weekly Meal Plan</h1>

      <button onClick={load}>
        Generate Meal Plan
      </button>

      <div className="card pre">
        {plan}
      </div>
    </div>
  );
}

export default MealPlan;