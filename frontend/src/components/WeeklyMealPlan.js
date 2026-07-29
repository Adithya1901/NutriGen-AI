import React,{useState} from "react";
import api from "../api";

function WeeklyMealPlan({familyId}){

const [plan,setPlan]=useState("");

const load = async()=>{

 const res = await api.get(
  `/families/${familyId}/weekly-plan`
 );

 setPlan(res.data.plan);
};

return(
<div className="card">

<button onClick={load}>
Generate Weekly Food Plan
</button>

<pre>{plan}</pre>

</div>
);
}

export default WeeklyMealPlan;