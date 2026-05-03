import { useState, useEffect } from "react";
import "./App.css";
import Dashboard from "./components/Dashboard.jsx";
import HomePage from "./components/HomePage.jsx";

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

function App() {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    fetch("/api/check_auth", {
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 200) {
          setAuthenticated(true);
        } else {
          setAuthenticated(false);
        }
      })
      .catch(() => setAuthenticated(false))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Home */}
        <Route
          path="/"
          element={
            authenticated ? <Navigate to="/main" /> : <HomePage />
          }
        />

        {/* Dashboard */}
        <Route
          path="/main"
          element={
            authenticated ? <Dashboard /> : <Navigate to="/" />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;