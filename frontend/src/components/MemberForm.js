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

    const submit = async () => {
        const payload = {
            ...form,
            age: parseInt(form.age) || 0
        };
        await api.post(`/families/${familyId}/members`, payload);

        window.location.reload();
    };

    return (
        <div>

            <input placeholder="Name"
                onChange={e => setForm({ ...form, name: e.target.value })}
            />

            <input placeholder="Age"
                onChange={e => setForm({ ...form, age: e.target.value })}
            />

            <input placeholder="Goal"
                onChange={e => setForm({ ...form, goal: e.target.value })}
            />

            <select
                onChange={e => setForm({ ...form, health_condition: e.target.value })}
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
            >
                <option>Vegetarian</option>
                <option>Non Vegetarian</option>
                <option>Vegan</option>
            </select>

            <button onClick={submit}>
                Add Member
            </button>

        </div>
    );
}

export default MemberForm;