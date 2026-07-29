import React, { useState } from "react";
import api from "../api";

function EditMember({ member }) {
    const [name, setName] = useState(member.name);

    const save = async () => {
        await api.put(`/members/${member.id}`, {
            ...member,
            name
        });

        window.location.reload();
    };

    const del = async () => {
        await api.delete(`/members/${member.id}`);
        window.location.reload();
    };

    return (
        <div>
            <input
                value={name}
                onChange={(e) =>
                    setName(e.target.value)
                }
            />

            <button onClick={save}>Save</button>
            <button onClick={del}>Delete</button>
        </div>
    );
}

export default EditMember;