import React, { useState } from "react";
import api from "../api";

function FamilyForm() {
    const [name, setName] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");

    const submit = async () => {
        if (!name.trim()) {
            setError("Family name cannot be empty.");
            return;
        }

        setSubmitting(true);
        setError("");
        try {
            await api.post("/families/", { name: name.trim() });
            window.location.reload();
        } catch (err) {
            console.error("FamilyForm submit error:", err);
            setError(err.response?.data?.detail || err.message || "Failed to create family.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="card">
            <h2>Create Family</h2>

            {error && (
                <div style={{ color: "#fca5a5", marginBottom: "10px", fontSize: "0.9em" }}>
                    {error}
                </div>
            )}

            <input
                placeholder="Family Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={submitting}
            />

            <button onClick={submit} disabled={submitting}>
                {submitting ? "Creating..." : "Create"}
            </button>
        </div>
    );
}

export default FamilyForm;