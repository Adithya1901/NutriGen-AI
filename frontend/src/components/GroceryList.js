import React,{useState} from "react";
import api from "../api";

function GroceryList({familyId}){

const [items,setItems]=useState("");

const load = async()=>{

 const res = await api.get(
   `/families/${familyId}/weekly-grocery`
 );

 setItems(res.data.items);
};

return(
<div className="card">

<button onClick={load}>
Generate Weekly Grocery
</button>

<pre>{items}</pre>

</div>
);
}

export default GroceryList;