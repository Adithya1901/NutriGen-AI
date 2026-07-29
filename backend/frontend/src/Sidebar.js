import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="sidebar">
      <h2>NutriGen AI</h2>

      <Link to="/">Dashboard</Link>
      <Link to="/members">Members</Link>
      <Link to="/mealplan">Meal Plan</Link>
      <Link to="/grocery">Grocery</Link>
      <Link to="/recipes">Recipes</Link>
    </div>
  );
}

export default Sidebar;