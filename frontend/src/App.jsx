import { useState, useEffect } from "react";
import "./App.css";
import Dashboard from "./components/Dashboard.jsx";
import HomePage from "./components/HomePage.jsx";

function App() {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    fetch("https://recmailsense.onrender.com/check_auth", {
      credentials: "include"
    })
      .then(res => {
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

  return authenticated ? <Dashboard /> : <HomePage />;
}

export default App;