import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import GraphBenchmark from "./GraphBenchmark.jsx";
import { AuthProvider } from "./Auth.jsx";
import "./index.css";

const parameters = new URLSearchParams(window.location.search);
const benchmarkValue = parameters.get("benchmark");
const benchmarkNodeCount = Number(benchmarkValue);
const useBenchmark = benchmarkValue !== null && Number.isInteger(benchmarkNodeCount) && benchmarkNodeCount >= 1 && benchmarkNodeCount <= 5000;

createRoot(document.getElementById("root")).render(
  useBenchmark ? <GraphBenchmark nodeCount={benchmarkNodeCount} /> : <StrictMode><AuthProvider><App /></AuthProvider></StrictMode>
);
