import React, { useState } from "react";
import api from "../api";

function FamilyForm() {
    const [name, setName] = useState("");

    const submit = async () => {
        await api.post("/families/", { name });
        window.location.reload();
    };

    return (
        <div className="card">
            <h2>Create Family</h2>

            <input
                placeholder="Family Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />

            <button onClick={submit}>Create</button>
        </div>
    );
}

export default FamilyForm;