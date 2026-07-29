import { useState } from "react";
import api from "../api";

function GroceryPage() {
  const [data, setData] = useState("");

  const load = async () => {
    const res = await api.get("/families/1/weekly-grocery");
    setData(res.data.grocery);
  };

  return (
    <div className="page">
      <h1>Weekly Grocery</h1>
      <button onClick={load}>Generate Grocery</button>
      <pre>{data}</pre>
    </div>
  );
}

export default GroceryPage;