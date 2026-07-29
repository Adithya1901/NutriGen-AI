import React, { useState, useEffect } from "react";
import api from "../api";

function Recipes() {
  const [families, setFamilies] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState(null);
  
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedMealType, setSelectedMealType] = useState("Breakfast");
  const [selectedLanguage, setSelectedLanguage] = useState("English");
  const [servings, setServings] = useState(4);
  
  const [recipe, setRecipe] = useState("");
  const [mealDescription, setMealDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snacks"];
  const LANGUAGES = ["English", "Hindi", "Kannada", "Tamil", "Telugu", "Marathi", "Bengali", "Gujarati", "Malayalam", "Punjabi", "Urdu"];

  useEffect(() => {
    loadFamilies();
    
    // Set default date to today
    const today = new Date().toISOString().split("T")[0];
    setSelectedDate(today);
  }, []);

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

  const loadRecipe = async () => {
    if (!selectedFamily || !selectedDate || !selectedMealType) return;
    
    setLoading(true);
    setRecipe("");
    setMealDescription("");
    setError("");

    try {
      const res = await api.get(`/families/${selectedFamily}/recipe`, {
        params: {
          date: selectedDate,
          meal_type: selectedMealType,
          language: selectedLanguage,
          servings: servings
        }
      });
      setRecipe(res.data.recipe);
      setMealDescription(res.data.meal_description);
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to fetch recipe. Make sure the meal plan is generated for this date and time.");
      }
    }
    
    setLoading(false);
  };

  return (
    <div className="page anim-fade-in">
      <h1 style={{ color: "#10b981", textShadow: "0 0 10px rgba(16,185,129,0.3)" }}>
        👩‍🍳 AI Recipe Generator
      </h1>
      <p style={{color: "#64748b", marginBottom: "30px"}}>
        Select a date and meal time to generate step-by-step cooking procedures for your generated meals.
      </p>

      <div className="card anim-fade-in" style={{ borderTop: "4px solid #3b82f6", display: "flex", flexWrap: "wrap", gap: "15px", alignItems: "flex-end" }}>
        
        {families.length > 0 && (
          <div style={{ flex: "1 1 200px" }}>
            <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8" }}>Select Family</label>
            <select
              value={selectedFamily || ""}
              onChange={e => setSelectedFamily(e.target.value)}
              className="date-picker"
              style={{ width: "100%", padding: "10px", borderRadius: "8px" }}
            >
              {families.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </div>
        )}

        <div style={{ flex: "1 1 200px" }}>
          <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8" }}>Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="date-picker"
            style={{ width: "100%", padding: "10px", borderRadius: "8px" }}
          />
        </div>

        <div style={{ flex: "1 1 200px" }}>
          <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8" }}>Meal Time</label>
          <select
            value={selectedMealType}
            onChange={(e) => setSelectedMealType(e.target.value)}
            className="date-picker"
            style={{ width: "100%", padding: "10px", borderRadius: "8px" }}
          >
            {MEAL_TYPES.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        <div style={{ flex: "1 1 200px" }}>
          <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8" }}>Language</label>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="date-picker"
            style={{ width: "100%", padding: "10px", borderRadius: "8px" }}
          >
            {LANGUAGES.map(lang => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>
        </div>

        <div style={{ flex: "1 1 120px" }}>
          <label style={{ display: "block", marginBottom: "8px", color: "#94a3b8" }}>Serving Size</label>
          <input
            type="number"
            min="1"
            max="20"
            value={servings}
            onChange={(e) => setServings(parseInt(e.target.value) || 1)}
            className="date-picker"
            style={{ width: "100%", padding: "10px", borderRadius: "8px" }}
          />
        </div>

        <div style={{ flex: "1 1 200px" }}>
          <button 
            onClick={loadRecipe} 
            disabled={loading}
            style={{ 
              width: "100%", 
              background: loading ? "#64748b" : "#3b82f6", 
              padding: "12px",
              marginTop: "auto"
            }}
          >
            {loading ? "Generating..." : "Generate AI Recipe"}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ marginTop: "20px", padding: "15px", background: "rgba(239, 68, 68, 0.1)", borderLeft: "4px solid #ef4444", color: "#ef4444", borderRadius: "4px" }}>
          {error}
        </div>
      )}

      {recipe && (
        <div style={{ marginTop: "30px", display: "flex", flexWrap: "wrap", gap: "20px" }}>
          
          <div className="card anim-fade-in" style={{ flex: "1 1 100%", borderTop: "4px solid #10b981" }}>
            <h2 style={{ color: "#10b981", margin: "0 0 15px 0" }}>🍲 Detailed Cooking Procedure</h2>
            <div style={{ padding: "10px", borderRadius: "8px", color: "#e2e8f0", lineHeight: "1.6" }}>
              {recipe.split('\n').map((line, idx) => {
                const stepMatch = line.match(/^(Step\s+\d+:?)\s*(.*)/i);
                if (stepMatch) {
                   const stepLabel = stepMatch[1];
                   const stepDetail = stepMatch[2];
                   return (
                     <div key={idx} style={{ marginBottom: "15px", background: "#1e293b", padding: "15px", borderLeft: "4px solid #3b82f6", borderRadius: "0 8px 8px 0" }}>
                       <strong style={{ color: "#3b82f6", display: "block", marginBottom: "5px", fontSize: "1.1em" }}>{stepLabel}</strong>
                       <p style={{ margin: "0", fontSize: "1.05em" }}>{stepDetail}</p>
                     </div>
                   );
                 }

                 const ytMatch = line.match(/^YouTube Video Search Link:\s*(https?:\/\/[^\s]+)/i);
                 if (ytMatch) {
                    return (
                      <div key={idx} style={{ marginTop: "15px", marginBottom: "25px" }}>
                        <a href={ytMatch[1]} target="_blank" rel="noreferrer" style={{ display: "inline-flex", alignItems: "center", background: "#ef4444", color: "white", padding: "10px 20px", borderRadius: "8px", textDecoration: "none", fontWeight: "bold", boxShadow: "0 4px 6px rgba(239, 68, 68, 0.4)" }}>
                          ▶️ Watch on YouTube ({selectedLanguage})
                        </a>
                      </div>
                    );
                 }

                 const mealItemMatch = line.match(/^Meal Item Name:\s*(.*)/i);
                 if (mealItemMatch) {
                     const itemName = mealItemMatch[1];
                     const imagePrompt = `Photorealistic delicious finished dish of ${itemName}, professional food photography, brightly lit, appetizing`;
                     return (
                       <div key={idx} style={{ marginTop: "40px" }}>
                         <h3 style={{ color: "#3b82f6", borderBottom: "2px solid #3b82f6", paddingBottom: "10px", fontSize: "1.5em", marginBottom: "20px" }}>
                           🍽️ {itemName}
                         </h3>
                         <div style={{ borderRadius: "12px", overflow: "hidden", maxWidth: "400px", boxShadow: "0 4px 6px rgba(0,0,0,0.2)", marginBottom: "20px" }}>
                           <img 
                             src={`https://image.pollinations.ai/prompt/${encodeURIComponent(imagePrompt)}?width=400&height=300&nologo=true`} 
                             alt={itemName}
                             style={{ width: "100%", height: "auto", display: "block" }}
                           />
                         </div>
                       </div>
                     );
                 }

                 if (line.trim() === "") return <div key={idx} style={{ height: "1em" }} />;
                 // For bolding headers like Ingredients:
                 if (line.match(/^[\w\s-]+:/)) {
                    return <strong key={idx} style={{ display: "block", marginTop: "15px", color: "#f59e0b", fontSize: "1.1em" }}>{line}</strong>;
                }
                return <div key={idx} style={{ marginBottom: "5px", paddingLeft: "10px" }}>{line}</div>;
              })}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}

export default Recipes;
