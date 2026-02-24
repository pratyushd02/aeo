import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:5000/api",
  headers: {
    Authorization: `Bearer sk-dddeec5e68bc4ae6aee77679a7d88c35`,
  },
});

export default API;