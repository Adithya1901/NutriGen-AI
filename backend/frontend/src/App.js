import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./Sidebar";

import Home from "./pages/Home";
import Members from "./pages/Members";
import MealPlanPage from "./pages/MealPlanPage";
import GroceryPage from "./pages/GroceryPage";
import Recipes from "./pages/Recipes";

function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />

        <div className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/members" element={<Members />} />
            <Route path="/mealplan" element={<MealPlanPage />} />
            <Route path="/grocery" element={<GroceryPage />} />
            <Route path="/recipes" element={<Recipes />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;