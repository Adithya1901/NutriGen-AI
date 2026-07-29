import { useEffect, useState } from "react";
import api from "../api";

function Members() {
  const [families, setFamilies] = useState([]);
  const [familyName, setFamilyName] = useState("");

  // separate form state for each family
  const [forms, setForms] = useState({});

  // -------------------------
  // LOAD FAMILIES
  // -------------------------
  const loadFamilies = async () => {
    try {
      const res = await api.get("/families/");
      setFamilies(res.data);
    } catch (error) {
      console.log(error);
      alert("Failed to load families");
    }
  };

  useEffect(() => {
    loadFamilies();
  }, []);

  // -------------------------
  // ADD FAMILY
  // -------------------------
  const addFamily = async () => {
    try {
      if (!familyName.trim()) {
        alert("Enter family name");
        return;
      }

      await api.post("/families/", {
        name: familyName.trim()
      });

      setFamilyName("");
      loadFamilies();

    } catch (error) {
      console.log(error.response?.data || error);
      alert("Failed to add family");
    }
  };

  // -------------------------
  // UPDATE MEMBER FORM
  // -------------------------
  const updateForm = (familyId, field, value) => {
    setForms((prev) => ({
      ...prev,
      [familyId]: {
        ...prev[familyId],
        [field]: value
      }
    }));
  };

  // -------------------------
  // ADD MEMBER
  // -------------------------
  const addMember = async (familyId) => {
    try {
      const form = forms[familyId] || {};

      if (!form.name || !form.age) {
        alert("Enter member name and age");
        return;
      }

      await api.post(`/families/${familyId}/members`, {
        name: form.name,
        age: parseInt(form.age),
        goal: form.goal || "Weight Loss",
        health_condition:
          form.health_condition || "None",
        diet: form.diet || "Vegetarian"
      });

      // clear only selected family form
      setForms((prev) => ({
        ...prev,
        [familyId]: {
          name: "",
          age: "",
          goal: "Weight Loss",
          health_condition: "None",
          diet: "Vegetarian"
        }
      }));

      loadFamilies();

    } catch (error) {
      console.log(error.response?.data || error);
      alert("Failed to add member");
    }
  };

  return (
    <div>
      <h1>Family Members</h1>

      {/* ADD FAMILY */}
      <div className="card">
        <h3>Create Family</h3>

        <input
          placeholder="Family Name"
          value={familyName}
          onChange={(e) =>
            setFamilyName(e.target.value)
          }
        />

        <button onClick={addFamily}>
          Add Family
        </button>
      </div>

      {/* FAMILY LIST */}
      {families.map((family) => {
        const form = forms[family.id] || {
          name: "",
          age: "",
          goal: "Weight Loss",
          health_condition: "None",
          diet: "Vegetarian"
        };

        return (
          <div className="card" key={family.id}>
            <h2>{family.name}</h2>

            <h3>Add Member</h3>

            <input
              placeholder="Member Name"
              value={form.name}
              onChange={(e) =>
                updateForm(
                  family.id,
                  "name",
                  e.target.value
                )
              }
            />

            <input
              placeholder="Age"
              type="number"
              value={form.age}
              onChange={(e) =>
                updateForm(
                  family.id,
                  "age",
                  e.target.value
                )
              }
            />

            <select
              value={form.goal}
              onChange={(e) =>
                updateForm(
                  family.id,
                  "goal",
                  e.target.value
                )
              }
            >
              <option>Weight Loss</option>
              <option>Weight Gain</option>
              <option>Maintain Weight</option>
              <option>Muscle Gain</option>
              <option>Diabetic Control</option>
            </select>

            <select
              value={form.health_condition}
              onChange={(e) =>
                updateForm(
                  family.id,
                  "health_condition",
                  e.target.value
                )
              }
            >
              <option>None</option>
              <option>Diabetes</option>
              <option>BP</option>
              <option>Thyroid</option>
              <option>Heart Disease</option>
              <option>PCOS</option>
            </select>

            <select
              value={form.diet}
              onChange={(e) =>
                updateForm(
                  family.id,
                  "diet",
                  e.target.value
                )
              }
            >
              <option>Vegetarian</option>
              <option>Non Vegetarian</option>
              <option>Vegan</option>
              <option>Eggetarian</option>
            </select>

            <button
              onClick={() =>
                addMember(family.id)
              }
            >
              Add Member
            </button>

            <hr />

            <h3>Registered Members</h3>

            {family.members &&
            family.members.length > 0 ? (
              family.members.map((m) => (
                <div
                  key={m.id}
                  style={{
                    padding: "10px",
                    marginBottom: "10px",
                    background: "#1e293b",
                    borderRadius: "10px"
                  }}
                >
                  <strong>{m.name}</strong> ({m.age})
                  <br />
                  Goal: {m.goal}
                  <br />
                  Condition: {m.health_condition}
                  <br />
                  Diet: {m.diet}
                </div>
              ))
            ) : (
              <p>No members added yet.</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default Members;