import { useState } from "react";
import api from "../api";

function MealPlanPage() {
  const [data, setData] = useState("");

  const load = async () => {
    const res = await api.get("/families/1/weekly-plan");
    setData(res.data.meal_plan);
  };

  return (
    <div className="page">
      <h1>Meal Plan</h1>
      <button onClick={load}>Generate Food</button>
      <pre>{data}</pre>
    </div>
  );
}

export default MealPlanPage;