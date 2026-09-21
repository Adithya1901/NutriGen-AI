import { useEffect, useState } from "react";
import api from "../api";

function Members() {
  const [families, setFamilies] = useState([]);
  const [familyName, setFamilyName] = useState("");
  const [forms, setForms] = useState({});
  const [loading, setLoading] = useState(false);
  const [submittingFamily, setSubmittingFamily] = useState(false);
  const [submittingMembers, setSubmittingMembers] = useState({});
  const [error, setError] = useState("");

  const loadFamilies = async () => {
    setLoading(true);
    try {
      const res = await api.get("/families/");
      setFamilies(res.data || []);
      setError("");
    } catch (err) {
      console.error("Error loading families:", err);
      setError(err.response?.data?.detail || err.message || "Failed to load families. Ensure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFamilies();
  }, []);

  const addFamily = async () => {
    if (!familyName.trim()) {
      setError("Please enter a family name.");
      return;
    }

    setSubmittingFamily(true);
    setError("");

    try {
      await api.post("/families/", {
        name: familyName.trim()
      });

      setFamilyName("");
      await loadFamilies();
    } catch (err) {
      console.error("Error adding family:", err);
      const detail = err.response?.data?.detail || err.message || "Failed to add family.";
      setError(detail);
    } finally {
      setSubmittingFamily(false);
    }
  };

  const updateForm = (id, field, value) => {
    setForms((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [field]: value
      }
    }));
  };

  const addMember = async (familyId) => {
    const form = forms[familyId] || {};

    if (!form.name || !form.age) {
      setError("Please enter member name and age.");
      return;
    }

    setSubmittingMembers((prev) => ({ ...prev, [familyId]: true }));
    setError("");

    try {
      const payload = {
        name: form.name.trim(),
        age: parseInt(form.age, 10) || 0,
        goal: form.goal || "Weight Loss",
        health_condition: form.health_condition || "None",
        diet: form.diet || "Vegetarian"
      };

      await api.post(`/families/${familyId}/members`, payload);

      setForms((prev) => ({
        ...prev,
        [familyId]: {}
      }));

      await loadFamilies();
    } catch (err) {
      console.error(`Error adding member for family ${familyId}:`, err);
      const detail = err.response?.data?.detail || err.message || "Failed to add member.";
      setError(detail);
    } finally {
      setSubmittingMembers((prev) => ({ ...prev, [familyId]: false }));
    }
  };

  const deleteFamily = async (id) => {
    if (!window.confirm("Are you sure you want to delete this family?")) return;
    setError("");
    try {
      await api.delete(`/families/${id}`);
      await loadFamilies();
    } catch (err) {
      console.error(`Error deleting family ${id}:`, err);
      setError(err.response?.data?.detail || err.message || "Failed to delete family.");
    }
  };

  const deleteMember = async (id) => {
    if (!window.confirm("Are you sure you want to delete this member?")) return;
    setError("");
    try {
      await api.delete(`/members/${id}`);
      await loadFamilies();
    } catch (err) {
      console.error(`Error deleting member ${id}:`, err);
      setError(err.response?.data?.detail || err.message || "Failed to delete member.");
    }
  };

  return (
    <div className="page anim-fade-in">
      <h1>Family Members</h1>

      {error && (
        <div style={{ margin: "15px 0", padding: "12px 18px", background: "rgba(239, 68, 68, 0.12)", borderLeft: "4px solid #ef4444", color: "#fca5a5", borderRadius: "8px" }}>
          {error}
        </div>
      )}

      <div className="card">
        <h3>Create Family</h3>

        <input
          placeholder="Family Name"
          value={familyName}
          onChange={(e) => setFamilyName(e.target.value)}
          disabled={submittingFamily}
        />

        <button onClick={addFamily} disabled={submittingFamily}>
          {submittingFamily ? "Adding..." : "Add Family"}
        </button>
      </div>

      {loading ? (
        <p style={{ color: "#94a3b8" }}>Loading families...</p>
      ) : (
        families.map((family) => {
          const form = forms[family.id] || {};
          const isMemberSubmitting = !!submittingMembers[family.id];

          return (
            <div className="card" key={family.id}>
              <h2>{family.name}</h2>

              <button onClick={() => deleteFamily(family.id)}>
                Delete Family
              </button>

              <h3>Add Member</h3>

              <input
                placeholder="Member Name"
                value={form.name || ""}
                onChange={(e) => updateForm(family.id, "name", e.target.value)}
                disabled={isMemberSubmitting}
              />

              <input
                placeholder="Age"
                type="number"
                value={form.age || ""}
                onChange={(e) => updateForm(family.id, "age", e.target.value)}
                disabled={isMemberSubmitting}
              />

              <select
                value={form.goal || "Weight Loss"}
                onChange={(e) => updateForm(family.id, "goal", e.target.value)}
                disabled={isMemberSubmitting}
              >
                <option>Weight Loss</option>
                <option>Weight Gain</option>
                <option>Maintain Weight</option>
                <option>Muscle Gain</option>
              </select>

              <select
                value={form.health_condition || "None"}
                onChange={(e) => updateForm(family.id, "health_condition", e.target.value)}
                disabled={isMemberSubmitting}
              >
                <option>None</option>
                <option>Diabetes</option>
                <option>BP</option>
                <option>Thyroid</option>
              </select>

              <select
                value={form.diet || "Vegetarian"}
                onChange={(e) => updateForm(family.id, "diet", e.target.value)}
                disabled={isMemberSubmitting}
              >
                <option>Vegetarian</option>
                <option>Non Vegetarian</option>
                <option>Vegan</option>
              </select>

              <button
                onClick={() => addMember(family.id)}
                disabled={isMemberSubmitting}
              >
                {isMemberSubmitting ? "Adding Member..." : "Add Member"}
              </button>

              <hr />

              <h3>Registered Members</h3>

              {family.members && family.members.length > 0 ? (
                family.members.map((m) => (
                  <div key={m.id} className="member-box">
                    <b>{m.name}</b> ({m.age} yrs)
                    <br />
                    Goal: {m.goal}
                    <br />
                    Condition: {m.health_condition}
                    <br />
                    Diet: {m.diet}
                    <br />

                    <button onClick={() => deleteMember(m.id)}>
                      Delete Member
                    </button>
                  </div>
                ))
              ) : (
                <p>No members added yet.</p>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}

export default Members;