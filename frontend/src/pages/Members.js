import { useEffect, useState } from "react";
import api from "../api";

function Members() {
  const [families, setFamilies] = useState([]);
  const [familyName, setFamilyName] = useState("");

  const [forms, setForms] = useState({});

  const loadFamilies = async () => {
    const res = await api.get("/families/");
    setFamilies(res.data);
  };

  useEffect(() => {
    loadFamilies();
  }, []);

  const addFamily = async () => {
    if (!familyName.trim()) return;

    await api.post("/families/", {
      name: familyName
    });

    setFamilyName("");
    loadFamilies();
  };

  const updateForm = (id, field, value) => {
    setForms({
      ...forms,
      [id]: {
        ...forms[id],
        [field]: value
      }
    });
  };

  const addMember = async (familyId) => {
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

    alert("Member registered successfully!");

    setForms({
      ...forms,
      [familyId]: {}
    });

    loadFamilies();
  };

  const deleteFamily = async (id) => {
    await api.delete(`/families/${id}`);
    loadFamilies();
  };

  const deleteMember = async (id) => {
    await api.delete(`/members/${id}`);
    loadFamilies();
  };

  return (
    <div>
      <h1>Family Members</h1>

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

      {families.map((family) => {
        const form = forms[family.id] || {};

        return (
          <div className="card" key={family.id}>
            <h2>{family.name}</h2>

            <button
              onClick={() =>
                deleteFamily(family.id)
              }
            >
              Delete Family
            </button>

            <h3>Add Member</h3>

            <input
              placeholder="Member Name"
              value={form.name || ""}
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
              value={form.age || ""}
              onChange={(e) =>
                updateForm(
                  family.id,
                  "age",
                  e.target.value
                )
              }
            />

            <select
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
            </select>

            <select
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
            </select>

            <select
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
                  className="member-box"
                >
                  <b>{m.name}</b> ({m.age})
                  <br />
                  {m.goal}
                  <br />
                  {m.health_condition}
                  <br />
                  {m.diet}
                  <br />

                  <button
                    onClick={() =>
                      deleteMember(m.id)
                    }
                  >
                    Delete Member
                  </button>
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