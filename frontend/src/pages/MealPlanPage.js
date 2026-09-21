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
    if (!selectedFamily) {
      setError("Please create or select a family before generating a meal plan.");
      return;
    }
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
        budget: budget,
        overwrite: true
      });
      // reload all upcoming after generating
      await loadUpcomingPlans();
      setTimeout(() => {
        const heading = document.getElementById("all-scheduled-plans-heading");
        if (heading) {
          heading.scrollIntoView({ behavior: "smooth" });
        }
      }, 150);
    } catch (err) {
      console.error("Failed to generate meal plan:", err);
      const detailMsg = err.response?.data?.detail || err.message || "Failed to load or generate plan. Please try again.";
      setError(detailMsg);
    } finally {
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

  const parseMealDetails = (planText) => {
    if (!planText) {
      return { meal_name: "Indian Home Meal", description: "", components: [], estimated_cost: 0, calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 };
    }
    try {
      const parsed = typeof planText === 'string' ? JSON.parse(planText) : planText;
      if (parsed && typeof parsed === 'object') {
        const mealName = parsed.meal_name || parsed.name || "Indian Meal";
        const comps = Array.isArray(parsed.components)
          ? parsed.components
          : (Array.isArray(parsed.ingredients) ? [{ component_name: "Main Dish", ingredients: parsed.ingredients }] : []);

        return {
          meal_name: mealName,
          description: parsed.description || "",
          components: comps,
          estimated_cost: parsed.estimated_cost || 0,
          calories: parsed.calories || 0,
          protein_g: parsed.protein_g || 0,
          carbohydrates_g: parsed.carbohydrates_g || 0,
          fat_g: parsed.fat_g || 0
        };
      }
    } catch (e) {
      // Fallback for plain text
    }

    const lines = planText.split('\n').map(l => l.trim()).filter(Boolean);
    let firstLine = lines[0] || planText;
    firstLine = firstLine.replace(/^[\-\*\•]\s*/, '').replace(/^["']|["']$/g, '');
    return {
      meal_name: firstLine,
      description: lines.slice(1).join(' '),
      components: [],
      estimated_cost: 0,
      calories: 0,
      protein_g: 0,
      carbohydrates_g: 0,
      fat_g: 0
    };
  };

  const getMealIcon = (mealType) => {
    switch ((mealType || '').toLowerCase()) {
      case 'breakfast': return '🍳';
      case 'lunch': return '🥗';
      case 'dinner': return '🍽️';
      case 'snacks':
      case 'snack': return '🥪';
      default: return '🍲';
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
          <h3 style={{ margin: "10px 0", color: "#94a3b8" }}>Set Budget Level:</h3>
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
            background: loading ? "#475569" : "linear-gradient(135deg, #0ea5e9, #2563eb)",
            fontWeight: "bold",
            padding: "12px 24px"
          }}
        >
          {loading ? "Processing..." : "Generate Missing Meals"}
        </button>
      </div>

      {error && (
        <div style={{ marginTop: "15px", padding: "12px 18px", background: "rgba(239, 68, 68, 0.12)", borderLeft: "4px solid #ef4444", color: "#fca5a5", borderRadius: "8px" }}>
          {error}
        </div>
      )}

      <h2 id="all-scheduled-plans-heading" style={{marginTop: "30px", paddingBottom: "10px", borderBottom: "1px solid #334155"}}>📅 All Scheduled Plans</h2>

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
                {datePlans.map((plan, idx) => {
                  const mealDetails = parseMealDetails(plan.plan_text);
                  const mealIcon = getMealIcon(plan.meal_type);

                  return (
                    <div key={idx} className="card daily-plan-card" style={{ position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                          <h3 className="meal-type-title" style={{ margin: 0, borderBottom: 'none', paddingBottom: 0 }}>
                            <span style={{ fontSize: '1.2em', marginRight: '6px' }}>{mealIcon}</span>
                            {plan.meal_type.toUpperCase()}
                          </h3>
                          <button 
                            onClick={() => deleteMealPlan(plan.id)}
                            title="Delete meal"
                            style={{ 
                              background: 'rgba(239, 68, 68, 0.15)', 
                              color: '#ef4444', 
                              border: '1px solid rgba(239, 68, 68, 0.3)',
                              padding: '6px 12px', 
                              fontSize: '0.75em', 
                              borderRadius: '8px',
                              cursor: 'pointer',
                              fontWeight: '600',
                              marginTop: 0,
                              boxShadow: 'none',
                              transition: 'all 0.2s ease'
                            }}
                          >
                            Delete
                          </button>
                        </div>

                        {/* Structured Meal Card */}
                        <div 
                          style={{
                            background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(59, 130, 246, 0.06))',
                            border: '1px solid rgba(56, 189, 248, 0.25)',
                            borderRadius: '12px',
                            padding: '16px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '10px',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <span style={{ 
                              color: '#f8fafc', 
                              fontWeight: '700', 
                              fontSize: '1.15rem', 
                              letterSpacing: '0.3px',
                              lineHeight: '1.4'
                            }}>
                              ✨ {mealDetails.meal_name}
                            </span>
                          </div>

                          {/* Meal Description */}
                          {mealDetails.description && (
                            <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.9rem', lineHeight: '1.5' }}>
                              {mealDetails.description}
                            </p>
                          )}

                          {/* Components List */}
                          {mealDetails.components && mealDetails.components.length > 0 && (
                            <div style={{ marginTop: '5px' }}>
                              <strong style={{ color: '#38bdf8', fontSize: '0.85rem', textTransform: 'uppercase' }}>Components:</strong>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                                {mealDetails.components.map((comp, cIdx) => (
                                  <span 
                                    key={cIdx}
                                    style={{
                                      background: '#1e293b',
                                      color: '#f8fafc',
                                      border: '1px solid rgba(56, 189, 248, 0.3)',
                                      fontSize: '0.78rem',
                                      padding: '3px 10px',
                                      borderRadius: '8px',
                                      fontWeight: '600'
                                    }}
                                  >
                                    • {comp.component_name || comp.name || `Component ${cIdx+1}`}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Macros & Cost Badges */}
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                            {mealDetails.estimated_cost > 0 && (
                              <span style={{ background: 'rgba(16, 185, 129, 0.18)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)', fontSize: '0.78rem', fontWeight: '700', padding: '3px 9px', borderRadius: '8px' }}>
                                ₹{mealDetails.estimated_cost}
                              </span>
                            )}
                            {mealDetails.calories > 0 && (
                              <span style={{ background: 'rgba(245, 158, 11, 0.18)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)', fontSize: '0.78rem', fontWeight: '700', padding: '3px 9px', borderRadius: '8px' }}>
                                🔥 {mealDetails.calories} kcal
                              </span>
                            )}
                            {mealDetails.protein_g > 0 && (
                              <span style={{ background: 'rgba(56, 189, 248, 0.18)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', fontSize: '0.78rem', fontWeight: '700', padding: '3px 9px', borderRadius: '8px' }}>
                                🥩 {mealDetails.protein_g}g protein
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.78em', color: '#64748b', fontWeight: '500' }}>
                          Generated Date: {plan.date}
                        </span>
                        <span style={{ 
                          fontSize: '0.72em', 
                          background: 'rgba(16, 185, 129, 0.15)', 
                          color: '#34d399', 
                          padding: '3px 10px', 
                          borderRadius: '12px',
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                          fontWeight: '600'
                        }}>
                          Scheduled
                        </span>
                      </div>
                    </div>
                  );
                })}
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