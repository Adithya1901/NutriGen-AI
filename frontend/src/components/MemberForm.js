import React, { useState } from "react";
import api from "../api";

function MemberForm({ familyId }) {
    const [form, setForm] = useState({
        name: "",
        age: "",
        goal: "",
        diet: "Vegetarian",
        allergies: "",
        health_condition: "None"
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");

    const submit = async () => {
        if (!form.name || !form.age) {
            setError("Member name and age are required.");
            return;
        }

        setSubmitting(true);
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
            window.location.reload();
        } catch (err) {
            console.error("MemberForm submit error:", err);
            setError(err.response?.data?.detail || err.message || "Failed to add member.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div>
            {error && (
                <div style={{ color: "#fca5a5", marginBottom: "10px", fontSize: "0.9em" }}>
                    {error}
                </div>
            )}

            <input
                placeholder="Name"
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                disabled={submitting}
            />

            <input
                placeholder="Age"
                type="number"
                value={form.age}
                onChange={e => setForm({ ...form, age: e.target.value })}
                disabled={submitting}
            />

            <input
                placeholder="Goal"
                value={form.goal}
                onChange={e => setForm({ ...form, goal: e.target.value })}
                disabled={submitting}
            />

            <select
                value={form.health_condition}
                onChange={e => setForm({ ...form, health_condition: e.target.value })}
                disabled={submitting}
            >
                <option>None</option>
                <option>Diabetes</option>
                <option>Hypertension</option>
                <option>PCOS</option>
                <option>Heart Disease</option>
                <option>Obesity</option>
                <option>Iron Deficiency</option>
            </select>

            <select
                value={form.diet}
                onChange={e => setForm({ ...form, diet: e.target.value })}
                disabled={submitting}
            >
                <option>Vegetarian</option>
                <option>Non Vegetarian</option>
                <option>Vegan</option>
            </select>

            <button onClick={submit} disabled={submitting}>
                {submitting ? "Adding Member..." : "Add Member"}
            </button>
        </div>
    );
}

export default MemberForm;