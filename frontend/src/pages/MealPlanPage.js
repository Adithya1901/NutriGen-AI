import { useState, useEffect } from "react";
import api from "../api";

function MealPlanPage() {
  const [families, setFamilies] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState(null);
  const [dates, setDates] = useState([new Date().toISOString().split('T')[0]]);
  const [currentDateInput, setCurrentDateInput] = useState("");
  const [selectedMeals, setSelectedMeals] = useState(["Breakfast", "Lunch", "Dinner"]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [budget, setBudget] = useState("Medium");

  const MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snacks"];

  useEffect(() => {
    loadFamilies();
  }, []);

  useEffect(() => {
    if (selectedFamily) {
      loadUpcomingPlans();
    }
  }, [selectedFamily]);

  const loadFamilies = async () => {
    try {
      const res = await api.get("/families/");
      setFamilies(res.data);
      if (res.data && res.data.length > 0) {
        setSelectedFamily(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadUpcomingPlans = async () => {
    if (!selectedFamily) return;
    setLoading(true);
    try {
      const res = await api.get(`/families/${selectedFamily}/upcoming-plans`);
      setPlans(res.data.plans || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const toggleMeal = (meal) => {
    setSelectedMeals(prev => 
      prev.includes(meal) ? prev.filter(m => m !== meal) : [...prev, meal]
    );
  };

  const addDate = () => {
    if (currentDateInput && !dates.includes(currentDateInput)) {
      setDates([...dates, currentDateInput].sort());
      setCurrentDateInput("");
    }
  };

  const removeDate = (dateToRemove) => {
    setDates(dates.filter(d => d !== dateToRemove));
  };

  const generateAndLoadPlan = async () => {
    if (!selectedFamily) return;
    if (selectedMeals.length === 0) {
      setError("Please select at least one meal to generate.");
      return;
    }
    if (dates.length === 0) {
      setError("Please select at least one date.");
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      await api.post(`/families/${selectedFamily}/multi-daily-plan`, {
        dates,
        meals: selectedMeals,
        budget: budget
      });
      // reload all upcoming after generating
      loadUpcomingPlans();
    } catch (err) {
      console.error(err);
      setError("Failed to load or generate plan. Please try again.");
      setLoading(false);
    }
  };

  // Group plans by date for rendering
  const groupedPlans = plans.reduce((acc, plan) => {
    if (!acc[plan.date]) acc[plan.date] = [];
    acc[plan.date].push(plan);
    return acc;
  }, {});

  const deleteMealPlan = async (planId) => {
    if (!window.confirm("Delete this meal and regenerate grocery list?")) return;
    setLoading(true);
    try {
      await api.delete(`/families/${selectedFamily}/daily-plan/${planId}`);
      loadUpcomingPlans();
    } catch (err) {
      console.error(err);
      setError("Failed to delete meal.");
      setLoading(false);
    }
  };

  const deleteDayPlan = async (dateStr) => {
    if (!window.confirm(`Delete all meals for ${dateStr} and regenerate grocery list?`)) return;
    setLoading(true);
    try {
      await api.delete(`/families/${selectedFamily}/daily-plan/date/${dateStr}`);
      loadUpcomingPlans();
    } catch (err) {
      console.error(err);
      setError(`Failed to delete meals for ${dateStr}.`);
      setLoading(false);
    }
  };

  const currentTime = new Date().toLocaleString();

  return (
    <div className="page anim-fade-in">
      <h1 style={{ color: "#38bdf8", textShadow: "0 0 10px rgba(56,189,248,0.3)" }}>
        Multi-Day Meal Planner
      </h1>
      <p style={{color: "#64748b"}}>Current System Time: {currentTime}</p>
      
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
          {families.length > 0 && (
            <select 
              value={selectedFamily || ""} 
              onChange={e => setSelectedFamily(e.target.value)}
              className="date-picker"
              style={{ padding: "12px", borderRadius: "8px" }}
            >
              {families.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          )}

          <div style={{ display: 'flex', gap: '10px' }}>
            <input 
              type="date" 
              className="date-picker"
              value={currentDateInput}
              onChange={(e) => setCurrentDateInput(e.target.value)}
            />
            <button onClick={addDate} style={{ marginTop: '0', background: '#10b981' }}>Add Date</button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {dates.map(d => (
            <div key={d} style={{ background: '#334155', padding: '5px 12px', borderRadius: '15px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {d} <span style={{ cursor: 'pointer', color: '#ef4444', fontWeight: 'bold' }} onClick={() => removeDate(d)}>×</span>
            </div>
          ))}
        </div>

        <div>
          <h3 style={{ margin: "10px 0", color: "#94a3b8" }}>Select Required Meals:</h3>
          <div className="meal-bar-container">
            {MEAL_TYPES.map(meal => (
              <button 
                key={meal}
                className={`meal-btn ${selectedMeals.includes(meal) ? 'active' : ''}`}
                onClick={() => toggleMeal(meal)}
              >
                {meal}
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 style={{ margin: "10px 0", color: "#94a3b8" }}>Set Budget:</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            {["Low", "Medium", "High"].map(b => (
              <label key={b} style={{ color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", gap: "5px" }}>
                <input 
                  type="radio" 
                  name="budget" 
                  value={b} 
                  checked={budget === b} 
                  onChange={(e) => setBudget(e.target.value)} 
                />
                {b}
              </label>
            ))}
          </div>
        </div>

        <button 
          onClick={generateAndLoadPlan} 
          disabled={loading}
          style={{ 
            alignSelf: 'flex-start', 
            background: loading ? "#475569" : "#0ea5e9",
            fontWeight: "bold",
            padding: "12px 24px"
          }}
        >
          {loading ? "Processing..." : "Generate Missing Meals"}
        </button>
      </div>

      {error && <p style={{ color: "#ef4444" }}>{error}</p>}

      <h2 style={{marginTop: "30px", paddingBottom: "10px", borderBottom: "1px solid #334155"}}>📅 All Scheduled Plans</h2>

      {plans.length > 0 && !loading && (
        <div className="anim-fade-in">
          {Object.entries(groupedPlans).map(([date, datePlans]) => (
            <div key={date} style={{ marginBottom: "30px" }}>
              <h2 style={{ color: "#fff", borderBottom: "2px solid #38bdf8", paddingBottom: "10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>Target Date: {date}</span>
                <button 
                  onClick={() => deleteDayPlan(date)}
                  style={{ background: '#f43f5e', padding: '8px 16px', fontSize: '0.6em', borderRadius: '5px', textTransform: 'uppercase', fontWeight: 'bold' }}
                >
                  Delete Entire Day
                </button>
              </h2>
              <div className="grid">
                {datePlans.map((plan, idx) => (
                  <div key={idx} className="card daily-plan-card" style={{ position: 'relative' }}>
                    <button 
                      onClick={() => deleteMealPlan(plan.id)}
                      style={{ position: 'absolute', top: '10px', right: '10px', background: '#ef4444', padding: '5px 10px', fontSize: '0.8em', borderRadius: '5px' }}
                    >
                      Delete
                    </button>
                    <h3 className="meal-type-title">{plan.meal_type}</h3>
                    <div className="pre">{plan.plan_text}</div>
                    <span style={{ fontSize: '0.8em', color: '#64748b', display: 'block', marginTop: '10px' }}>Generated Date: {plan.date}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {plans.length === 0 && !loading && !error && (
        <div style={{ textAlign: "center", marginTop: "40px", color: "#64748b" }}>
          <h3>No plans currently active.</h3>
          <p>Add dates, select meals, and hit generate to schedule your plan!</p>
        </div>
      )}
    </div>
  );
}

export default MealPlanPage;