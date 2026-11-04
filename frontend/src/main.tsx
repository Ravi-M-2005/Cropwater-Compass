import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Register Service Worker for offline asset caching
if ("serviceWorker" in navigator && !import.meta.env.DEV) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((reg) => console.log("Service Worker registered for offline caching:", reg.scope))
      .catch((err) => console.warn("Service Worker registration failed:", err));
  });
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
