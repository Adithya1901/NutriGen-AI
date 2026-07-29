import React, { useEffect, useState } from "react";
import api from "../api";
import MemberForm from "./MemberForm";
import EditMember from "./EditMember";
import WeeklyMealPlan from "./WeeklyMealPlan";
import GroceryList from "./GroceryList";

function FamilyList() {
    const [families, setFamilies] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadFamilies();
    }, []);

    const loadFamilies = async () => {
        try {
            const res = await api.get("/families/");
            setFamilies(res.data);
        } catch (error) {
            console.error("Error loading families:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <p>Loading families...</p>;
    }

    if (families.length === 0) {
        return <p>No families found. Create one above.</p>;
    }

    return (
        <div>
            {families.map((family) => (
                <div className="card" key={family.id}>
                    <h2>{family.name}</h2>

                    <h4>Members:</h4>

                    {family.members && family.members.length > 0 ? (
                        family.members.map((m) => (
                            <div
                                key={m.id}
                                style={{
                                    marginBottom: "15px",
                                    paddingBottom: "10px",
                                    borderBottom: "1px solid #ddd"
                                }}
                            >
                                <p>
                                    <strong>{m.name}</strong> ({m.age}) - {m.goal}
                                </p>

                                <p>
                                    Health: {m.health_condition || "None"}
                                </p>

                                <EditMember member={m} />
                            </div>
                        ))
                    ) : (
                        <p>No members added yet.</p>
                    )}

                    <MemberForm familyId={family.id} />

                    <hr style={{ margin: "20px 0" }} />

                    <WeeklyMealPlan familyId={family.id} />

                    <GroceryList familyId={family.id} />
                </div>
            ))}
        </div>
    );
}

export default FamilyList;