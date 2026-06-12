import { create } from "zustand";
import client from "../api/client";

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem("user")) || null,
  token: localStorage.getItem("token") || null,
  isAuthenticated: !!localStorage.getItem("token"),
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      // OAuth2 password flow requires form data
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);
      
      const response = await client.post("/auth/login", params, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      
      const { access_token, user } = response.data;
      localStorage.setItem("token", access_token);
      localStorage.setItem("user", JSON.stringify(user));
      
      set({
        token: access_token,
        user,
        isAuthenticated: true,
        loading: false
      });
      return true;
    } catch (err) {
      set({
        error: err.response?.data?.detail || "Error al iniciar sesión",
        loading: false
      });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null
    });
  },

  clearError: () => set({ error: null })
}));

export default useAuthStore;
