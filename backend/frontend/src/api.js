import axios from "axios";

const api = axios.create({
  baseURL: "http://10.109.150.9:8000"
});

export default api;