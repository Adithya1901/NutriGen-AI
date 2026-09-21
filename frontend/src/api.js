import axios from "axios";

// Central API configuration for local dev and GitHub Pages production
const API_BASE_URL =
  process.env.REACT_APP_API_URL ||
  (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:8000"
    : "http://localhost:8000");

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

export { API_BASE_URL };
export default api;