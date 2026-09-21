import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";

function Home() {
  const [families, setFamilies] = useState([]);
  const [upcomingCount, setUpcomingCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const currentTime = new Date().toLocaleString();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const famRes = await api.get("/families/");
      const famData = famRes.data || [];
      setFamilies(famData);

      if (famData.length > 0) {
        let totalPlans = 0;
        for (const fam of famData) {
          try {
            const planRes = await api.get(`/families/${fam.id}/upcoming-plans`);
            totalPlans += (planRes.data.plans || []).length;
          } catch (e) {
            // Ignore single family plan fetch error
          }
        }
        setUpcomingCount(totalPlans);
      }
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page anim-fade-in" style={{ paddingBottom: "40px" }}>
      {/* Executive Hero Banner */}
      <div 
        style={{
          background: "linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(99, 102, 241, 0.15))",
          border: "1px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "16px",
          padding: "28px",
          marginBottom: "30px",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.3)",
          position: "relative",
          overflow: "hidden"
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "15px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <span style={{ background: "rgba(16, 185, 129, 0.2)", color: "#34d399", border: "1px solid rgba(16, 185, 129, 0.4)", padding: "4px 12px", borderRadius: "20px", fontSize: "0.8rem", fontWeight: "600" }}>
                ● NutriGen AI v2.0
              </span>
              <span style={{ color: "#94a3b8", fontSize: "0.85rem" }}>
                {currentTime}
              </span>
            </div>
            <h1 style={{ color: "#f8fafc", margin: "0 0 10px 0", fontSize: "2.2rem", fontWeight: "700", letterSpacing: "-0.5px" }}>
              NutriGen AI — Executive Dashboard
            </h1>
            <p style={{ color: "#cbd5e1", margin: 0, fontSize: "1.05rem", maxWidth: "720px", lineHeight: "1.6" }}>
              Precision Family Nutrition &amp; Flexible Multi-Day Meal OS. Automated health customization, budget INR optimization, and intelligent grocery aggregation.
            </p>
          </div>

          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <Link 
              to="/mealplan"
              className="btn"
              style={{
                background: "linear-gradient(135deg, #0ea5e9, #2563eb)",
                color: "#ffffff",
                padding: "12px 22px",
                borderRadius: "10px",
                textDecoration: "none",
                fontWeight: "700",
                boxShadow: "0 4px 14px rgba(14, 165, 233, 0.4)"
              }}
            >
              📅 Flexible Planner
            </Link>
            <Link 
              to="/members"
              className="btn"
              style={{
                background: "rgba(255, 255, 255, 0.08)",
                color: "#f8fafc",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                padding: "12px 22px",
                borderRadius: "10px",
                textDecoration: "none",
                fontWeight: "600"
              }}
            >
              👥 Manage Household
            </Link>
          </div>
        </div>
      </div>

      {/* Key Metrics Overview */}
      <div 
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "18px",
          marginBottom: "35px"
        }}
      >
        <div className="card" style={{ padding: "20px", borderLeft: "4px solid #38bdf8" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>Active Households</div>
          <div style={{ color: "#f8fafc", fontSize: "2rem", fontWeight: "700", marginTop: "6px" }}>
            {loading ? "..." : families.length}
          </div>
          <div style={{ color: "#38bdf8", fontSize: "0.8rem", marginTop: "4px" }}>Configured family profiles</div>
        </div>

        <div className="card" style={{ padding: "20px", borderLeft: "4px solid #34d399" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>Scheduled Multi-Day Meals</div>
          <div style={{ color: "#f8fafc", fontSize: "2rem", fontWeight: "700", marginTop: "6px" }}>
            {loading ? "..." : upcomingCount}
          </div>
          <div style={{ color: "#34d399", fontSize: "0.8rem", marginTop: "4px" }}>Active scheduled meals</div>
        </div>

        <div className="card" style={{ padding: "20px", borderLeft: "4px solid #fbbf24" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>AI Engine Status</div>
          <div style={{ color: "#f8fafc", fontSize: "1.3rem", fontWeight: "700", marginTop: "6px" }}>
            Groq gpt-oss-20b
          </div>
          <div style={{ color: "#fbbf24", fontSize: "0.8rem", marginTop: "4px" }}>Strict JSON Schema Active</div>
        </div>

        <div className="card" style={{ padding: "20px", borderLeft: "4px solid #f43f5e" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", fontWeight: "600" }}>Currency &amp; Budget</div>
          <div style={{ color: "#f8fafc", fontSize: "1.4rem", fontWeight: "700", marginTop: "6px" }}>
            INR (₹) Low / Med / High
          </div>
          <div style={{ color: "#f43f5e", fontSize: "0.8rem", marginTop: "4px" }}>Normalized Price Engine</div>
        </div>
      </div>

      {/* Main Professional Feature Grid */}
      <h2 style={{ color: "#f8fafc", marginBottom: "20px", display: "flex", alignItems: "center", gap: "10px" }}>
        <span>🚀 Flexible Family Nutrition Suite</span>
      </h2>

      <div className="grid" style={{ gap: "22px" }}>
        
        {/* Module 1: Flexible Multi-Day Planner */}
        <div 
          className="card" 
          style={{ 
            display: "flex", 
            flexDirection: "column", 
            justify: "space-between",
            background: "linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            padding: "24px"
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "1.8rem" }}>📅</span>
              <span style={{ background: "rgba(14, 165, 233, 0.2)", color: "#38bdf8", fontSize: "0.75rem", fontWeight: "700", padding: "4px 10px", borderRadius: "12px" }}>
                CORE PLANNER
              </span>
            </div>
            <h3 style={{ color: "#f8fafc", marginTop: 0, marginBottom: "8px", fontSize: "1.3rem" }}>
              Flexible Multi-Day Planner
            </h3>
            <p style={{ color: "#94a3b8", fontSize: "0.92rem", lineHeight: "1.6", margin: "0 0 16px 0" }}>
              Schedule customized multi-day meal plans for any dates. Select Breakfast, Lunch, Dinner, or Snacks with tailored INR budget controls.
            </p>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "20px" }}>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Flexible Dates
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Low/Med/High Budget
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • All 4 Meal Types
              </span>
            </div>
          </div>

          <Link 
            to="/mealplan" 
            style={{ 
              color: "#38bdf8", 
              textDecoration: "none", 
              fontWeight: "700", 
              fontSize: "0.95rem",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            Open Flexible Multi-Day Planner &rarr;
          </Link>
        </div>

        {/* Module 2: Family & Health Profiles */}
        <div 
          className="card" 
          style={{ 
            display: "flex", 
            flexDirection: "column", 
            justify: "space-between",
            background: "linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            border: "1px solid rgba(52, 211, 153, 0.3)",
            padding: "24px"
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "1.8rem" }}>👥</span>
              <span style={{ background: "rgba(16, 185, 129, 0.2)", color: "#34d399", fontSize: "0.75rem", fontWeight: "700", padding: "4px 10px", borderRadius: "12px" }}>
                HEALTH &amp; DIET
              </span>
            </div>
            <h3 style={{ color: "#f8fafc", marginTop: 0, marginBottom: "8px", fontSize: "1.3rem" }}>
              Family Health Profiles
            </h3>
            <p style={{ color: "#94a3b8", fontSize: "0.92rem", lineHeight: "1.6", margin: "0 0 16px 0" }}>
              Customize member profiles with specific medical conditions (Diabetes, BP, Thyroid), goals, and diet restrictions (Vegetarian, Non-Veg, Jain).
            </p>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "20px" }}>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Diabetes &amp; BP Rules
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Weight &amp; Muscle Goals
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Meal Preferences
              </span>
            </div>
          </div>

          <Link 
            to="/members" 
            style={{ 
              color: "#34d399", 
              textDecoration: "none", 
              fontWeight: "700", 
              fontSize: "0.95rem",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            Manage Family Profiles &rarr;
          </Link>
        </div>

        {/* Module 3: Flexible Grocery Engine */}
        <div 
          className="card" 
          style={{ 
            display: "flex", 
            flexDirection: "column", 
            justify: "space-between",
            background: "linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            border: "1px solid rgba(251, 191, 36, 0.3)",
            padding: "24px"
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "1.8rem" }}>🛒</span>
              <span style={{ background: "rgba(245, 158, 11, 0.2)", color: "#fbbf24", fontSize: "0.75rem", fontWeight: "700", padding: "4px 10px", borderRadius: "12px" }}>
                GROCERY ENGINE
              </span>
            </div>
            <h3 style={{ color: "#f8fafc", marginTop: 0, marginBottom: "8px", fontSize: "1.3rem" }}>
              Flexible Grocery Consolidation
            </h3>
            <p style={{ color: "#94a3b8", fontSize: "0.92rem", lineHeight: "1.6", margin: "0 0 16px 0" }}>
              Auto-aggregate all ingredients across your scheduled multi-day plans into a smart categorized shopping list with PDF export support.
            </p>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "20px" }}>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Auto-Aggregated Quantities
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • PDF Export List
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Category Grouping
              </span>
            </div>
          </div>

          <Link 
            to="/grocery" 
            style={{ 
              color: "#fbbf24", 
              textDecoration: "none", 
              fontWeight: "700", 
              fontSize: "0.95rem",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            View Flexible Grocery List &rarr;
          </Link>
        </div>

        {/* Module 4: AI Master Recipes */}
        <div 
          className="card" 
          style={{ 
            display: "flex", 
            flexDirection: "column", 
            justify: "space-between",
            background: "linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            padding: "24px"
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "1.8rem" }}>👩‍🍳</span>
              <span style={{ background: "rgba(244, 63, 94, 0.2)", color: "#f43f5e", fontSize: "0.75rem", fontWeight: "700", padding: "4px 10px", borderRadius: "12px" }}>
                AI RECIPES
              </span>
            </div>
            <h3 style={{ color: "#f8fafc", marginTop: 0, marginBottom: "8px", fontSize: "1.3rem" }}>
              AI Recipe &amp; YouTube Master
            </h3>
            <p style={{ color: "#94a3b8", fontSize: "0.92rem", lineHeight: "1.6", margin: "0 0 16px 0" }}>
              Step-by-step preparation and cooking instructions for every dish, detailed macro metrics, food images, and YouTube video tutorials.
            </p>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "20px" }}>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Step-by-Step Cooking
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • ▶ Watch Recipe YouTube
              </span>
              <span style={{ background: "#0f172a", color: "#cbd5e1", fontSize: "0.75rem", padding: "3px 9px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}>
                • Multi-Lingual Cooking
              </span>
            </div>
          </div>

          <Link 
            to="/recipes" 
            style={{ 
              color: "#f43f5e", 
              textDecoration: "none", 
              fontWeight: "700", 
              fontSize: "0.95rem",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            Generate AI Master Recipes &rarr;
          </Link>
        </div>

      </div>

      {/* Quick Workflow Guide */}
      <div className="card" style={{ marginTop: "35px", padding: "24px", background: "rgba(15, 23, 42, 0.6)" }}>
        <h3 style={{ color: "#f8fafc", margin: "0 0 16px 0", fontSize: "1.15rem" }}>
          💡 How NutriGen AI Works in 3 Simple Steps
        </h3>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
          <div style={{ background: "#1e293b", padding: "16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ color: "#38bdf8", fontWeight: "700", fontSize: "0.9rem" }}>1. Add Household Profiles</div>
            <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "6px 0 0 0", lineHeight: "1.5" }}>
              Enter family members, ages, medical conditions (e.g. Diabetes, BP), and diet preferences in <Link to="/members" style={{ color: "#38bdf8" }}>Members</Link>.
            </p>
          </div>

          <div style={{ background: "#1e293b", padding: "16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ color: "#34d399", fontWeight: "700", fontSize: "0.9rem" }}>2. Generate Flexible Plans</div>
            <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "6px 0 0 0", lineHeight: "1.5" }}>
              Pick any target dates, meal types (Breakfast, Lunch, Dinner, Snacks), and budget level in <Link to="/mealplan" style={{ color: "#34d399" }}>Meal Plan</Link>.
            </p>
          </div>

          <div style={{ background: "#1e293b", padding: "16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ color: "#fbbf24", fontWeight: "700", fontSize: "0.9rem" }}>3. Grocery &amp; Cooking Guides</div>
            <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "6px 0 0 0", lineHeight: "1.5" }}>
              View consolidated grocery items in <Link to="/grocery" style={{ color: "#fbbf24" }}>Grocery</Link> and step-by-step multi-lingual recipes in <Link to="/recipes" style={{ color: "#fbbf24" }}>Recipes</Link>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;