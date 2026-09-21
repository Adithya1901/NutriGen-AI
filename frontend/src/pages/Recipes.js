import React, { useState, useEffect } from "react";
import api from "../api";

function Recipes() {
  const [families, setFamilies] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState(null);
  
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedMealType, setSelectedMealType] = useState("Breakfast");
  const [selectedLanguage, setSelectedLanguage] = useState("English");
  
  const [recipe, setRecipe] = useState(null);
  const [mealDescription, setMealDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [scheduledDates, setScheduledDates] = useState([]);
  const [checkedIngredients, setCheckedIngredients] = useState({});
  const [completedSteps, setCompletedSteps] = useState({});

  const MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snacks"];
  const LANGUAGES = ["English", "Hindi", "Kannada", "Tamil", "Telugu", "Marathi", "Bengali", "Gujarati", "Malayalam", "Punjabi", "Urdu"];

  useEffect(() => {
    loadFamilies();
    const today = new Date().toISOString().split("T")[0];
    setSelectedDate(today);
  }, []);

  useEffect(() => {
    if (selectedFamily) {
      loadScheduledDates(selectedFamily);
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

  const loadScheduledDates = async (famId) => {
    try {
      const res = await api.get(`/families/${famId}/upcoming-plans`);
      const plans = res.data.plans || [];
      const uniqueDates = Array.from(new Set(plans.map(p => p.date))).sort();
      setScheduledDates(uniqueDates);
      if (uniqueDates.length > 0) {
        setSelectedDate(uniqueDates[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadRecipe = async () => {
    if (!selectedFamily) {
      setError("Please select or create a family first.");
      return;
    }
    if (!selectedDate) {
      setError("Please select a date for the recipe.");
      return;
    }
    if (!selectedMealType) {
      setError("Please select a meal time.");
      return;
    }
    
    setLoading(true);
    setRecipe(null);
    setMealDescription("");
    setError("");
    setCheckedIngredients({});
    setCompletedSteps({});

    try {
      const res = await api.get(`/families/${selectedFamily}/recipe`, {
        params: {
          date: selectedDate,
          meal_type: selectedMealType,
          language: selectedLanguage
        }
      });
      setRecipe(res.data.recipe);
      setMealDescription(res.data.meal_description || "");

      setTimeout(() => {
        const recipeElement = document.getElementById("generated-recipe-section");
        if (recipeElement) {
          recipeElement.scrollIntoView({ behavior: "smooth" });
        }
      }, 150);
    } catch (err) {
      console.error("Failed to fetch AI recipe:", err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Recipe generation failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleIngredient = (id) => {
    setCheckedIngredients(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleStep = (id) => {
    setCompletedSteps(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const getParsedRecipe = () => {
    if (!recipe) return null;

    let data = recipe;
    if (typeof data === "string") {
      try {
        data = JSON.parse(data);
      } catch (e) {
        data = null;
      }
    }

    if (data && typeof data === "object") {
      let rName = data.recipe_name || data.name || mealDescription || "Nutritious Recipe";
      const genericNames = ["breakfast", "lunch", "dinner", "snack", "snacks", "nutritious healthy meal", "healthy meal"];
      if (genericNames.includes(String(rName).trim().toLowerCase())) {
        rName = (mealDescription && !genericNames.includes(String(mealDescription).trim().toLowerCase())) 
          ? mealDescription 
          : `${selectedMealType} Dish`;
      }

      const ytQuery = data.youtube_search_query || `${rName} recipe in ${selectedLanguage}`;
      const ytUrl = data.youtube_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(ytQuery)}`;

      const ingredients = Array.isArray(data.ingredients)
        ? data.ingredients.map(ing => {
            if (typeof ing === "object" && ing !== null) {
              return {
                name: ing.name || "Ingredient",
                quantity: ing.quantity || "",
                unit: ing.unit || ""
              };
            }
            return { name: String(ing), quantity: "", unit: "" };
          })
        : [];

      const prepSteps = Array.isArray(data.preparation_steps)
        ? data.preparation_steps
        : (data.preparation_steps ? [String(data.preparation_steps)] : []);

      const cookSteps = Array.isArray(data.cooking_steps)
        ? data.cooking_steps
        : (data.cooking_steps ? [String(data.cooking_steps)] : []);

      const nutrition = data.nutrition || {
        calories: "250 kcal",
        protein: "12g",
        carbohydrates: "30g",
        fat: "8g"
      };

      return {
        recipe_name: rName,
        meal_type: data.meal_type || selectedMealType,
        description: data.description || "",
        servings: data.servings || 2,
        cooking_time_minutes: data.cooking_time_minutes || 25,
        ingredients,
        preparation_steps: prepSteps,
        cooking_steps: cookSteps,
        nutrition,
        youtube_url: ytUrl,
        youtube_search_query: ytQuery
      };
    }

    return null;
  };

  const parsedRecipe = getParsedRecipe();
  const currentTime = new Date().toLocaleString();

  return (
    <div className="page anim-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '15px' }}>
        <div>
          <h1 style={{ color: "#10b981", textShadow: "0 0 10px rgba(16,185,129,0.3)", margin: 0 }}>
            👩‍🍳 AI Master Recipe Generator
          </h1>
          <p style={{ color: "#64748b", marginTop: "5px" }}>Current System Time: {currentTime}</p>
        </div>
      </div>

      {/* Control Card */}
      <div className="card anim-fade-in" style={{ borderTop: "4px solid #3b82f6", display: "flex", flexWrap: "wrap", gap: "15px", alignItems: "flex-end", marginTop: "20px" }}>
        
        {families.length > 0 && (
          <div style={{ flex: "1 1 180px" }}>
            <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8", fontWeight: "500" }}>Select Family</label>
            <select
              value={selectedFamily || ""}
              onChange={e => setSelectedFamily(e.target.value)}
              className="date-picker"
              style={{ width: "100%", padding: "10px 14px", borderRadius: "10px" }}
            >
              {families.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </div>
        )}

        <div style={{ flex: "1 1 180px" }}>
          <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8", fontWeight: "500" }}>
            Date {scheduledDates.length > 0 ? "📅 Scheduled Plan" : ""}
          </label>
          {scheduledDates.length > 0 ? (
            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="date-picker"
              style={{ width: "100%", padding: "10px 14px", borderRadius: "10px" }}
            >
              {scheduledDates.map(d => (
                <option key={d} value={d}>{d} (Scheduled)</option>
              ))}
            </select>
          ) : (
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="date-picker"
              style={{ width: "100%", padding: "10px 14px", borderRadius: "10px" }}
            />
          )}
        </div>

        <div style={{ flex: "1 1 160px" }}>
          <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8", fontWeight: "500" }}>Meal Time</label>
          <select
            value={selectedMealType}
            onChange={(e) => setSelectedMealType(e.target.value)}
            className="date-picker"
            style={{ width: "100%", padding: "10px 14px", borderRadius: "10px" }}
          >
            {MEAL_TYPES.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        <div style={{ flex: "1 1 160px" }}>
          <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8", fontWeight: "500" }}>Language</label>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="date-picker"
            style={{ width: "100%", padding: "10px 14px", borderRadius: "10px" }}
          >
            {LANGUAGES.map(lang => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>
        </div>

        <div style={{ flex: "1 1 180px" }}>
          <button 
            onClick={loadRecipe} 
            disabled={loading}
            style={{ 
              width: "100%", 
              background: loading ? "#64748b" : "linear-gradient(135deg, #0ea5e9, #2563eb)", 
              padding: "12px",
              marginTop: "auto",
              fontWeight: "bold",
              borderRadius: "10px"
            }}
          >
            {loading ? "Chef is cooking..." : "Generate AI Recipe"}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ marginTop: "20px", padding: "15px 20px", background: "rgba(239, 68, 68, 0.12)", borderLeft: "4px solid #ef4444", color: "#fca5a5", borderRadius: "8px" }}>
          {error}
        </div>
      )}

      {/* Recipe Rendering Section */}
      {parsedRecipe && (
        <div id="generated-recipe-section" style={{ marginTop: "30px", display: "flex", flexDirection: "column", gap: "30px" }}>
          {(() => {
            const r = parsedRecipe;
            const imagePrompt = `Photorealistic delicious finished dish of ${r.recipe_name}, professional culinary food photography, bright lighting, appetizing 8k`;

            return (
              <div className="anim-fade-in" style={{ display: "flex", flexDirection: "column", gap: "25px" }}>
                
                {/* Hero Dish Banner Card */}
                <div className="card daily-plan-card" style={{ padding: "30px", borderTop: "4px solid #10b981" }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "30px", alignItems: "center" }}>
                    
                    {/* Food Image Frame */}
                    <div style={{ flex: "1 1 320px", maxWidth: "420px", borderRadius: "16px", overflow: "hidden", boxShadow: "0 10px 30px rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)", position: "relative" }}>
                      <img 
                        src={`https://image.pollinations.ai/prompt/${encodeURIComponent(imagePrompt)}?width=420&height=280&nologo=true`} 
                        alt={r.recipe_name}
                        style={{ width: "100%", height: "260px", objectFit: "cover", display: "block" }}
                      />
                      <span style={{ position: "absolute", bottom: "12px", right: "12px", background: "rgba(15,23,42,0.85)", backdropFilter: "blur(8px)", color: "#34d399", padding: "4px 12px", borderRadius: "12px", fontSize: "0.8em", fontWeight: "600", border: "1px solid rgba(16,185,129,0.3)" }}>
                        AI Culinary Showcase
                      </span>
                    </div>

                    {/* Dish Info & Stats */}
                    <div style={{ flex: "1 1 340px", display: "flex", flexDirection: "column", gap: "15px" }}>
                      <h2 style={{ color: "#f8fafc", fontSize: "2.2rem", margin: 0, fontWeight: "700", lineHeight: "1.3" }}>
                        🍽️ {r.recipe_name}
                      </h2>

                      {r.description && (
                        <p style={{ color: "#cbd5e1", fontSize: "1.05rem", lineHeight: "1.6", margin: 0 }}>
                          {r.description}
                        </p>
                      )}

                      {/* Stat Badges */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "5px" }}>
                        <div style={{ background: "rgba(56, 189, 248, 0.12)", border: "1px solid rgba(56, 189, 248, 0.3)", padding: "6px 14px", borderRadius: "12px", color: "#38bdf8", fontSize: "0.9rem", fontWeight: "600" }}>
                          ⏱️ Cooking Time: {r.cooking_time_minutes} mins
                        </div>
                        <div style={{ background: "rgba(16, 185, 129, 0.12)", border: "1px solid rgba(16, 185, 129, 0.3)", padding: "6px 14px", borderRadius: "12px", color: "#34d399", fontSize: "0.9rem", fontWeight: "600" }}>
                          👨‍👩‍👧 Servings: {r.servings}
                        </div>
                        <div style={{ background: "rgba(168, 85, 247, 0.12)", border: "1px solid rgba(168, 85, 247, 0.3)", padding: "6px 14px", borderRadius: "12px", color: "#c084fc", fontSize: "0.9rem", fontWeight: "600" }}>
                          🌐 Language: {selectedLanguage}
                        </div>
                      </div>

                      {/* YouTube Video Link */}
                      {r.youtube_url && (
                        <div style={{ marginTop: "10px" }}>
                          <a 
                            href={r.youtube_url} 
                            target="_blank" 
                            rel="noreferrer" 
                            style={{ 
                              display: "inline-flex", 
                              alignItems: "center", 
                              gap: "10px", 
                              background: "linear-gradient(135deg, #ef4444, #dc2626)", 
                              color: "white", 
                              padding: "12px 22px", 
                              borderRadius: "12px", 
                              textDecoration: "none", 
                              fontWeight: "bold", 
                              boxShadow: "0 6px 20px rgba(239, 68, 68, 0.35)",
                              transition: "transform 0.2s ease"
                            }}
                          >
                            ▶ Watch Video Tutorial on YouTube
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Grid for Ingredients & Preparation */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "25px" }}>
                  
                  {/* Ingredients Section */}
                  {r.ingredients.length > 0 && (
                    <div className="card daily-plan-card" style={{ padding: "25px" }}>
                      <h3 style={{ color: "#f59e0b", marginTop: 0, marginBottom: "18px", fontSize: "1.25rem", display: "flex", alignItems: "center", gap: "10px" }}>
                        🌿 Measure & Prepare Ingredients
                      </h3>
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        {r.ingredients.map((ing, iIdx) => {
                          const ingId = `recipe-ing-${iIdx}`;
                          const isChecked = !!checkedIngredients[ingId];

                          return (
                            <div 
                              key={iIdx}
                              className={`grocery-item-row ${isChecked ? 'checked' : ''}`}
                              onClick={() => toggleIngredient(ingId)}
                              style={{ cursor: "pointer", margin: 0 }}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                                <input 
                                  type="checkbox" 
                                  checked={isChecked} 
                                  onChange={() => {}} 
                                  className="custom-checkbox"
                                />
                                <span className="item-name" style={{ color: isChecked ? "#64748b" : "#f8fafc", fontWeight: "500" }}>
                                  {ing.quantity && <strong style={{ color: "#f59e0b", marginRight: "4px" }}>{ing.quantity} {ing.unit}</strong>} {ing.name}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Preparation Steps */}
                  {r.preparation_steps.length > 0 && (
                    <div className="card daily-plan-card" style={{ padding: "25px" }}>
                      <h3 style={{ color: "#38bdf8", marginTop: 0, marginBottom: "18px", fontSize: "1.25rem", display: "flex", alignItems: "center", gap: "10px" }}>
                        🔪 Chef's Preparation Guide
                      </h3>
                      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                        {r.preparation_steps.map((pStep, pIdx) => (
                          <div key={pIdx} style={{ display: "flex", gap: "12px", background: "rgba(14, 165, 233, 0.06)", borderLeft: "3px solid #38bdf8", padding: "12px 16px", borderRadius: "0 10px 10px 0" }}>
                            <strong style={{ color: "#38bdf8", minWidth: "24px" }}>{pIdx + 1}.</strong>
                            <span style={{ color: "#e2e8f0", lineHeight: "1.5" }}>{pStep}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Step-by-Step Cooking Instructions */}
                {r.cooking_steps.length > 0 && (
                  <div className="card daily-plan-card" style={{ padding: "30px" }}>
                    <h3 style={{ color: "#38bdf8", marginTop: 0, marginBottom: "25px", fontSize: "1.35rem", display: "flex", alignItems: "center", gap: "10px" }}>
                      🔥 Step-By-Step Cooking Guide
                    </h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
                      {r.cooking_steps.map((cStep, sIdx) => {
                        const stepId = `recipe-step-${sIdx}`;
                        const isDone = !!completedSteps[stepId];

                        return (
                          <div 
                            key={sIdx}
                            onClick={() => toggleStep(stepId)}
                            style={{
                              background: isDone ? "rgba(16, 185, 129, 0.08)" : "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.7))",
                              border: isDone ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(255, 255, 255, 0.06)",
                              borderLeft: isDone ? "5px solid #10b981" : "5px solid #3b82f6",
                              borderRadius: "14px",
                              padding: "20px 24px",
                              cursor: "pointer",
                              transition: "all 0.3s ease"
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                              <strong style={{ color: isDone ? "#34d399" : "#3b82f6", fontSize: "1.1rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                                {isDone ? `✓ STEP ${sIdx + 1} COMPLETED` : `STEP ${sIdx + 1}`}
                              </strong>
                              <span style={{ fontSize: "0.8em", color: isDone ? "#34d399" : "#64748b", background: isDone ? "rgba(16,185,129,0.15)" : "rgba(51, 65, 85, 0.4)", padding: "3px 10px", borderRadius: "10px" }}>
                                {isDone ? "Done" : "Tap to complete"}
                              </span>
                            </div>
                            <p style={{ margin: 0, color: isDone ? "#94a3b8" : "#f8fafc", fontSize: "1.08rem", lineHeight: "1.6", textDecoration: isDone ? "line-through" : "none" }}>
                              {cStep}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Nutrition Card */}
                {r.nutrition && (
                  <div className="card daily-plan-card" style={{ padding: "25px", borderTop: "4px solid #a855f7" }}>
                    <h3 style={{ color: "#c084fc", marginTop: 0, marginBottom: "20px", fontSize: "1.25rem", display: "flex", alignItems: "center", gap: "10px" }}>
                      📊 Nutritional Values (per serving)
                    </h3>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "15px" }}>
                      <div style={{ background: "rgba(168, 85, 247, 0.1)", border: "1px solid rgba(168, 85, 247, 0.3)", padding: "16px", borderRadius: "12px", textAlign: "center" }}>
                        <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>Calories</div>
                        <div style={{ color: "#c084fc", fontSize: "1.3rem", fontWeight: "700", marginTop: "4px" }}>{r.nutrition.calories || "N/A"}</div>
                      </div>
                      <div style={{ background: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.3)", padding: "16px", borderRadius: "12px", textAlign: "center" }}>
                        <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>Protein</div>
                        <div style={{ color: "#38bdf8", fontSize: "1.3rem", fontWeight: "700", marginTop: "4px" }}>{r.nutrition.protein || "N/A"}</div>
                      </div>
                      <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.3)", padding: "16px", borderRadius: "12px", textAlign: "center" }}>
                        <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>Carbs</div>
                        <div style={{ color: "#f59e0b", fontSize: "1.3rem", fontWeight: "700", marginTop: "4px" }}>{r.nutrition.carbohydrates || "N/A"}</div>
                      </div>
                      <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", padding: "16px", borderRadius: "12px", textAlign: "center" }}>
                        <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>Fat</div>
                        <div style={{ color: "#fca5a5", fontSize: "1.3rem", fontWeight: "700", marginTop: "4px" }}>{r.nutrition.fat || "N/A"}</div>
                      </div>
                    </div>
                  </div>
                )}

              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}

export default Recipes;
