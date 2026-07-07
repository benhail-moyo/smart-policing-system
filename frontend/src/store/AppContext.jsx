import { createContext, useContext, useEffect, useMemo, useReducer } from "react";
import { authAPI } from "../lib/api";

const STORAGE_KEY = "crimewatch_token";

const initialState = {
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null,
  incidents: [],
  hotspots: [],
  activeRoute: null,
  stats: null,
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_USER":
      return { ...state, user: action.payload };
    case "SET_TOKEN":
      return { ...state, token: action.payload };
    case "SET_INCIDENTS":
      return { ...state, incidents: action.payload };
    case "SET_HOTSPOTS":
      return { ...state, hotspots: action.payload };
    case "SET_ROUTE":
      return { ...state, activeRoute: action.payload };
    case "SET_STATS":
      return { ...state, stats: action.payload };
    case "LOGOUT":
      return { ...state, user: null, token: null, activeRoute: null, stats: null };
    default:
      return state;
  }
}

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    if (state.token) {
      localStorage.setItem(STORAGE_KEY, state.token);
      return;
    }

    localStorage.removeItem(STORAGE_KEY);
  }, [state.token]);

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    const token = response?.data?.token || response?.data?.access_token || null;

    if (!token) {
      throw new Error("Authentication failed");
    }

    dispatch({ type: "SET_TOKEN", payload: token });
    dispatch({
      type: "SET_USER",
      payload: {
        id: response?.data?.user?.id || 1,
        email,
        role: response?.data?.user?.role || "officer",
      },
    });

    return response;
  };

  const logout = () => {
    dispatch({ type: "LOGOUT" });
  };

  const value = useMemo(
    () => ({
      ...state,
      login,
      logout,
      setIncidents: (payload) => dispatch({ type: "SET_INCIDENTS", payload }),
      setHotspots: (payload) => dispatch({ type: "SET_HOTSPOTS", payload }),
      setRoute: (payload) => dispatch({ type: "SET_ROUTE", payload }),
      setStats: (payload) => dispatch({ type: "SET_STATS", payload }),
    }),
    [state],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  return useContext(AppContext);
}
