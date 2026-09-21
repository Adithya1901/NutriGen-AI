import { useState, useEffect } from "react";
import api from "../api";
import jsPDF from "jspdf";

function GroceryPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [families, setFamilies] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState(null);
  const [checkedItems, setCheckedItems] = useState({});
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadFamilies();
  }, []);

  useEffect(() => {
    if (selectedFamily) {
      loadGrocery();
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

  const loadGrocery = async () => {
    if (!selectedFamily) return;
    setLoading(true);
    try {
      const res = await api.get(`/families/${selectedFamily}/upcoming-plans`);
      const allGroceries = res.data.groceries || [];
      setData(allGroceries.length > 0 ? allGroceries.slice(-1) : []);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const regenerateGrocery = async () => {
    if (!selectedFamily) return;
    setLoading(true);
    try {
      await api.post(`/families/${selectedFamily}/generate-grocery`);
      await loadGrocery();
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Failed to regenerate grocery list. Make sure you have active meal plans.");
    }
    setLoading(false);
  };

  const toggleCheck = (id) => {
    setCheckedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const parseGroceryList = (rawText) => {
    if (!rawText) return { categories: [], totalCost: null, totalItemCount: 0 };

    let cleanText = rawText
      .replace(/<think>[\s\S]*?<\/think>/gi, '')
      .replace(/<think>[\s\S]*/gi, '')
      .replace(/\*Re\s*reading[\s\S]*?\*/gi, '')
      .replace(/Deconstruct the Meal Plan[\s\S]*?:/gi, '')
      .trim();

    const lines = cleanText.split('\n').map(l => l.trim()).filter(Boolean);
    const categories = [];
    let currentCategory = null;
    let totalCost = null;
    let totalItemCount = 0;

    const isThinkingLine = (l) => {
      const lower = l.toLowerCase();
      return lower.startsWith('think') || 
             lower.includes('deconstruct') || 
             lower.includes('prompt saying') || 
             lower.includes('input carefully') ||
             lower.includes('only one day is actually') ||
             lower.includes('analysis of meals') ||
             lower.includes('day meal plan') ||
             lower.startsWith("let's analyze") ||
             lower.startsWith('first, i need to') ||
             lower.startsWith('day ') ||
             lower.startsWith('breakfast:') ||
             lower.startsWith('lunch:') ||
             lower.startsWith('dinner:') ||
             lower.startsWith('snacks:') ||
             lower.startsWith('snack:') ||
             lower.startsWith('>') ||
             lower.startsWith('in or ') ||
             lower.includes('approx ') ||
             lower.includes('raw per person') ||
             lower.includes("let's say") ||
             lower === '`' ||
             lower.startsWith('```');
    };

    const categoryIcons = {
      'vegetable': '🥬',
      'herb': '🌿',
      'protein': '🍗',
      'meat': '🥩',
      'fish': '🐟',
      'seafood': '🍤',
      'dairy': '🥛',
      'egg': '🥚',
      'grain': '🌾',
      'flour': '🍞',
      'rice': '🍚',
      'spice': '🧂',
      'pantry': '🫙',
      'oil': '🛢️',
      'fruit': '🍎',
      'snack': '🥨',
      'beverage': '🧃'
    };

    const getCategoryIcon = (name) => {
      const lower = name.toLowerCase();
      for (const [key, icon] of Object.entries(categoryIcons)) {
        if (lower.includes(key)) return icon;
      }
      return '🛒';
    };

    lines.forEach((line, index) => {
      if (isThinkingLine(line)) return;

      if (line.toLowerCase().includes('total cost') || line.toLowerCase().includes('estimated total')) {
        const parts = line.split(':');
        if (parts.length > 1) {
          totalCost = parts.slice(1).join(':').replace(/\*\*/g, '').trim();
        } else {
          totalCost = line.replace(/\*\*/g, '').trim();
        }
        return;
      }

      let cleanLine = line.replace(/^[\-\*\•]\s*/, '').trim();
      const isHeader = (cleanLine.startsWith('**') && cleanLine.endsWith('**')) || 
                       (cleanLine.endsWith(':') && !cleanLine.includes('₹') && !cleanLine.match(/-\s*\d+/));
      const hasPrice = cleanLine.includes('₹') || cleanLine.match(/-\s*\d+/);

      if (isHeader && !hasPrice) {
        let catName = cleanLine.replace(/\*\*/g, '').replace(/:$/, '').trim();
        if (isThinkingLine(catName)) return;

        currentCategory = {
          name: catName,
          icon: getCategoryIcon(catName),
          items: []
        };
        categories.push(currentCategory);
        return;
      }

      let itemText = cleanLine.replace(/\*\*/g, '');
      let parts = itemText.split(/\s*-\s*/);

      let name = itemText;
      let quantity = '';
      let price = '';

      if (parts.length >= 3) {
        name = parts[0].trim();
        quantity = parts[1].trim();
        price = parts[2].trim();
      } else if (parts.length === 2) {
        name = parts[0].trim();
        if (parts[1].includes('₹')) {
          price = parts[1].trim();
        } else {
          quantity = parts[1].trim();
        }
      } else {
        const priceMatch = itemText.match(/(₹\s*\d+|Rs\.?\s*\d+)/i);
        if (priceMatch) {
          price = priceMatch[0];
          name = itemText.replace(priceMatch[0], '').replace(/[-–:]/g, '').trim();
        }
      }

      if (!name || isThinkingLine(name)) return;

      if (!currentCategory) {
        currentCategory = {
          name: 'General Provisions',
          icon: '🛒',
          items: []
        };
        categories.push(currentCategory);
      }

      const itemId = `item-${index}-${name.replace(/\s+/g, '-').toLowerCase()}`;
      totalItemCount++;

      currentCategory.items.push({
        id: itemId,
        name: name,
        quantity: quantity,
        price: price,
        raw: line
      });
    });

    const validCategories = categories.filter(c => c.items.length > 0);

    return { categories: validCategories, totalCost, totalItemCount };
  };

  const downloadPDF = (groceryText, datesArr) => {
    const doc = new jsPDF();
    
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor("#10b981");
    doc.text("NutriGen AI - Active Grocery List", 20, 20);
    
    const displayDates = datesArr.includes("all_upcoming") ? "All Scheduled Meal Plans" : datesArr.join(", ");
    doc.setFontSize(12);
    doc.setTextColor("#64748b");
    doc.text(`Coverage: ${displayDates}`, 20, 30);
    
    doc.setLineWidth(0.5);
    doc.line(20, 35, 190, 35);

    doc.setFont("helvetica", "normal");
    doc.setTextColor("#000000");
    
    const cleanText = groceryText.replace(/\*\*/g, '');
    const lines = doc.splitTextToSize(cleanText, 170);
    doc.text(lines, 20, 45);

    const fileNameDate = datesArr.includes("all_upcoming") ? "All_Scheduled" : datesArr[0];
    doc.save(`Groceries_${fileNameDate}.pdf`);
  };

  const currentTime = new Date().toLocaleString();

  return (
    <div className="page anim-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '15px' }}>
        <div>
          <h1 style={{ color: "#10b981", textShadow: "0 0 10px rgba(16,185,129,0.3)", margin: 0 }}>
            🛒 Provisions & Grocery Checklist
          </h1>
          <p style={{ color: "#64748b", marginTop: "5px" }}>Current System Time: {currentTime}</p>
        </div>

        {families.length > 0 && (
          <select 
            value={selectedFamily || ""} 
            onChange={e => setSelectedFamily(e.target.value)}
            className="date-picker"
            style={{ padding: '12px 18px', borderRadius: '12px', maxWidth: '240px' }}
          >
            {families.map(f => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', margin: '50px 0', color: '#94a3b8' }}>
          <h3>Loading active groceries...</h3>
        </div>
      ) : (
        <div>
          {data.length > 0 ? (
            data.map((groc, idx) => {
              const { categories, totalCost, totalItemCount } = parseGroceryList(groc.grocery_list);
              const checkedCount = Object.values(checkedItems).filter(Boolean).length;
              const displayCoverage = groc.dates.includes("all_upcoming") 
                ? "All Active Scheduled Meal Plans" 
                : groc.dates.join(', ');

              return (
                <div key={idx} style={{ marginTop: '20px' }}>
                  {/* Top Stats Banner */}
                  <div className="card anim-fade-in" style={{ borderTop: '4px solid #10b981', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '20px', padding: '20px 25px' }}>
                    <div>
                      <span style={{ fontSize: '0.85em', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '600', display: 'block' }}>
                        Coverage Window
                      </span>
                      <h3 style={{ margin: '5px 0 0 0', color: '#f8fafc', fontSize: '1.25rem' }}>
                        🗓️ {displayCoverage}
                      </h3>
                    </div>

                    <div style={{ display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'wrap' }}>
                      {totalCost && (
                        <div style={{ background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '10px 18px', borderRadius: '12px', textAlign: 'center' }}>
                          <span style={{ fontSize: '0.75em', color: '#10b981', textTransform: 'uppercase', fontWeight: 'bold', display: 'block' }}>Estimated Total</span>
                          <strong style={{ fontSize: '1.3rem', color: '#34d399' }}>{totalCost}</strong>
                        </div>
                      )}

                      <div style={{ background: 'rgba(51, 65, 85, 0.4)', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '10px 18px', borderRadius: '12px', textAlign: 'center' }}>
                        <span style={{ fontSize: '0.75em', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', display: 'block' }}>Progress</span>
                        <strong style={{ fontSize: '1.1rem', color: '#f8fafc' }}>{checkedCount} / {totalItemCount} Checked</strong>
                      </div>

                      <button 
                        onClick={regenerateGrocery}
                        title="Regenerate grocery list from current meal plans"
                        style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)', boxShadow: '0 4px 15px rgba(14, 165, 233, 0.3)', padding: '12px 20px', fontSize: '0.95rem', fontWeight: 'bold', marginTop: 0 }}
                      >
                        🔄 Refresh Grocery List
                      </button>

                      <button 
                        onClick={() => downloadPDF(groc.grocery_list, groc.dates)}
                        style={{ background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 4px 15px rgba(16, 185, 129, 0.3)', padding: '12px 20px', fontSize: '0.95rem', fontWeight: 'bold', marginTop: 0 }}
                      >
                        📄 Download PDF
                      </button>
                    </div>
                  </div>

                  {/* Search Bar */}
                  <div style={{ margin: '20px 0' }}>
                    <input 
                      type="text" 
                      placeholder="🔍 Search items in your grocery list..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{ width: '100%', maxWidth: '100%', padding: '14px 20px', borderRadius: '14px', background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
                    />
                  </div>

                  {/* Categories Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '25px' }}>
                    {categories.map((cat, cIdx) => {
                      const filteredItems = cat.items.filter(item => 
                        item.name.toLowerCase().includes(searchQuery.toLowerCase())
                      );

                      if (filteredItems.length === 0 && searchQuery) return null;

                      return (
                        <div key={cIdx} className="card daily-plan-card" style={{ padding: '22px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '12px' }}>
                            <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <span style={{ fontSize: '1.3em' }}>{cat.icon}</span>
                              {cat.name}
                            </h3>
                            <span style={{ background: 'rgba(51, 65, 85, 0.6)', color: '#94a3b8', fontSize: '0.8em', padding: '4px 10px', borderRadius: '10px', fontWeight: '600' }}>
                              {filteredItems.length} items
                            </span>
                          </div>

                          <div>
                            {filteredItems.map(item => {
                              const isChecked = !!checkedItems[item.id];
                              return (
                                <div 
                                  key={item.id} 
                                  className={`grocery-item-row ${isChecked ? 'checked' : ''}`}
                                  onClick={() => toggleCheck(item.id)}
                                  style={{ cursor: 'pointer' }}
                                >
                                  <div style={{ display: 'flex', alignItems: 'center', flex: 1, overflow: 'hidden' }}>
                                    <input 
                                      type="checkbox" 
                                      checked={isChecked}
                                      onChange={() => {}} 
                                      className="custom-checkbox"
                                    />
                                    <span className="item-name" style={{ color: isChecked ? '#64748b' : '#f8fafc', fontWeight: '500', fontSize: '1rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                      {item.name}
                                    </span>
                                  </div>

                                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginLeft: '10px' }}>
                                    {item.quantity && (
                                      <span className="qty-badge">
                                        {item.quantity}
                                      </span>
                                    )}
                                    {item.price && (
                                      <span className="price-badge">
                                        {item.price}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })
          ) : (
            <div style={{ textAlign: "center", marginTop: "50px", color: "#64748b" }}>
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