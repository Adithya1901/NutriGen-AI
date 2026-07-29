import { useState } from "react";
import api from "../api";

function Grocery() {

  const [data, setData] = useState("");

  const load = async () => {
    const res =
      await api.get("/families/1/grocery");

    setData(res.data.grocery);
  };

  return (
    <div>
      <h1>Weekly Grocery</h1>

      <button onClick={load}>
        Generate Grocery
      </button>

      <div className="card pre">
        {data}
      </div>
    </div>
  );
}

export default Grocery;