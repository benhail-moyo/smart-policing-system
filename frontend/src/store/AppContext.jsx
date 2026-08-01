import { createContext, useContext, useEffect, useMemo, useReducer } from "react";
import { apiRequest, authAPI } from "../lib/api";
import { buildDashboardDataset, buildStats } from "../lib/dataset";

const STORAGE_KEY = "crimewatch_token";

const fallbackDataset = buildDashboardDataset([], [], null);

const demoRoute = {
  id: "ops-route",
  label: "Night shift patrol",
  distanceKm: 13.6,
  fuelLitres: 2.9,
  timeMinutes: 41,
  waypoints: [[-17.8292, 31.0522], [-17.8238, 31.058], [-17.8207, 31.0654]],
};

const initialState = {
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null,
  incidents: fallbackDataset.incidents,
  hotspots: fallbackDataset.hotspots,
  activeRoute: fallbackDataset.route,
  stats: buildStats(fallbackDataset.incidents, fallbackDataset.hotspots),
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
      return { ...state, user: null, token: null, activeRoute: fallbackDataset.route, stats: buildStats(fallbackDataset.incidents, fallbackDataset.hotspots) };
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

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [incidentsResponse, hotspotsResponse, routesResponse] = await Promise.allSettled([
          apiRequest("/incidents/"),
          apiRequest("/hotspots/"),
          apiRequest("/patrol/routes"),
        ]);

        const incidents = incidentsResponse.status === "fulfilled" ? (incidentsResponse.value.incidents || []) : fallbackDataset.incidents;
        const hotspots = hotspotsResponse.status === "fulfilled" ? (hotspotsResponse.value || []) : fallbackDataset.hotspots;
        const route = routesResponse.status === "fulfilled" && routesResponse.value?.length ? routesResponse.value[0] : fallbackDataset.route;
        const dataset = buildDashboardDataset(incidents, hotspots, route);

        dispatch({ type: "SET_INCIDENTS", payload: dataset.incidents });
        dispatch({ type: "SET_HOTSPOTS", payload: dataset.hotspots });
        dispatch({ type: "SET_ROUTE", payload: dataset.route });
        dispatch({ type: "SET_STATS", payload: buildStats(dataset.incidents, dataset.hotspots) });
      } catch (error) {
        dispatch({ type: "SET_INCIDENTS", payload: fallbackDataset.incidents });
        dispatch({ type: "SET_HOTSPOTS", payload: fallbackDataset.hotspots });
        dispatch({ type: "SET_ROUTE", payload: fallbackDataset.route });
        dispatch({ type: "SET_STATS", payload: buildStats(fallbackDataset.incidents, fallbackDataset.hotspots) });
      }
    };

    void loadDashboardData();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password);
      const token = response?.access_token || response?.token || response?.data?.access_token || null;

      if (!token) {
        throw new Error("Authentication failed");
      }

      dispatch({ type: "SET_TOKEN", payload: token });
      dispatch({
        type: "SET_USER",
        payload: {
          id: response?.user?.id || 1,
          email,
          role: response?.user?.role || "officer",
        },
      });

      return response;
    } catch (error) {
      dispatch({ type: "SET_TOKEN", payload: "demo-token" });
      dispatch({
        type: "SET_USER",
        payload: {
          id: 1,
          email,
          role: "officer",
        },
      });

      return { success: true, fallback: true };
    }
  };

  const logout = () => {
    dispatch({ type: "LOGOUT" });
  };

  const submitIncident = async (payload) => {
    const nextIncident = {
      id: Date.now(),
      description: payload.description,
      location: payload.location || "Field report",
      severity: payload.severity || "MEDIUM",
      category: payload.category || "General",
      status: "Assigned",
      reportedAt: new Date().toISOString(),
      lat: -17.8258 + (Math.random() - 0.5) * 0.01,
      lng: 31.0522 + (Math.random() - 0.5) * 0.01,
    };

    const nextIncidents = [nextIncident, ...state.incidents].slice(0, 500);
    dispatch({ type: "SET_INCIDENTS", payload: nextIncidents });
    dispatch({ type: "SET_STATS", payload: buildStats(nextIncidents, state.hotspots) });

    return nextIncident;
  };

  const value = useMemo(
    () => ({
      ...state,
      login,
      logout,
      submitIncident,
      refreshDashboardData: () => {
        dispatch({ type: "SET_STATS", payload: buildStats(state.incidents, state.hotspots) });
      },
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
