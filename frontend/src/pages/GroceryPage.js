import { useState, useEffect } from "react";
import api from "../api";
import jsPDF from "jspdf";

function GroceryPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [families, setFamilies] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState(null);

  useEffect(() => {
    loadFamilies();
  }, []);

  useEffect(() => {
    if (selectedFamily) {
      loadGrocery();
    }
  }, [selectedFamily]);

  const loadFamilies = async () => {
    const res = await api.get("/families/");
    setFamilies(res.data);
    if (res.data && res.data.length > 0) {
      setSelectedFamily(res.data[0].id);
    }
  };

  const loadGrocery = async () => {
    if (!selectedFamily) return;
    setLoading(true);
    try {
      // Pulling active groceries directly from the scheduled plans endpoint
      const res = await api.get(`/families/${selectedFamily}/upcoming-plans`);
      // Slicing to get only the latest active grocery list
      const allGroceries = res.data.groceries || [];
      setData(allGroceries.length > 0 ? allGroceries.slice(-1) : []);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const downloadPDF = (groceryText, datesArr) => {
    const doc = new jsPDF();
    
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor("#10b981");
    doc.text("NutriGen AI - Active Grocery List", 20, 20);
    
    doc.setFontSize(12);
    doc.setTextColor("#64748b");
    doc.text(`Scheduled Dates: ${datesArr.join(", ")}`, 20, 30);
    
    doc.setLineWidth(0.5);
    doc.line(20, 35, 190, 35);

    doc.setFont("helvetica", "normal");
    doc.setTextColor("#000000");
    
    const lines = doc.splitTextToSize(groceryText, 170);
    doc.text(lines, 20, 45);

    doc.save(`Groceries_${datesArr[0]}.pdf`);
  };

  const currentTime = new Date().toLocaleString();

  return (
    <div className="page anim-fade-in">
      <h1 style={{ color: "#10b981", textShadow: "0 0 10px rgba(16,185,129,0.3)" }}>
        All Scheduled Grocery Lists
      </h1>
      <p style={{color: "#64748b"}}>Current System Time: {currentTime}</p>
      
      {families.length > 0 && (
        <select 
          value={selectedFamily || ""} 
          onChange={e => setSelectedFamily(e.target.value)}
          className="date-picker"
          style={{ marginBottom: "20px", padding: '12px', borderRadius: '8px' }}
        >
          {families.map(f => (
            <option key={f.id} value={f.id}>{f.name}</option>
          ))}
        </select>
      )}

      {loading ? (
        <p>Loading active groceries...</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {data.length > 0 ? (
            data.map((groc, idx) => (
              <div key={idx} className="card anim-fade-in" style={{ borderTop: '4px solid #10b981', position: 'relative' }}>
                <h2 style={{ color: '#10b981', margin: '0 0 10px 0' }}>🛒 Provisions Checklist</h2>
                <span style={{ fontSize: '1.1em', color: '#94a3b8', display: 'block', marginBottom: '15px' }}>
                  Coverage Dates: {groc.dates.join(', ')}
                </span>
                
                <button 
                  onClick={() => downloadPDF(groc.grocery_list, groc.dates)}
                  style={{ position: 'absolute', top: '20px', right: '20px', background: '#ef4444', padding: '10px 18px' }}
                >
                  Download PDF
                </button>
                <div className="pre" style={{ background: '#0f172a', padding: '15px', borderRadius: '8px', color: '#e2e8f0' }}>
                  {groc.grocery_list}
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: "center", marginTop: "40px", color: "#64748b" }}>
              <h3>No Groceries Needed</h3>
              <p>Go to your Meal Plans tab and Generate meals schedule to automatically create linked groceries here!</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default GroceryPage;