import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import NetworkGraph from "./components/NetworkGraph";
import { generateBenchmarkGraph } from "./data/generateBenchmarkGraph";
import "./App.css";


function GraphBenchmark({ nodeCount }) {
  const graph = useMemo(
    () => generateBenchmarkGraph(nodeCount),
    [nodeCount]
  );

  const renderStartedAt = useRef(performance.now());
  const [selectedNode, setSelectedNode] = useState(null);
  const [metrics, setMetrics] = useState({
    initialRenderMs: null,
    eventLoopDelayMs: null,
    svgElements: null,
  });

  const handleSelectNode = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  useEffect(() => {
    let secondFrame;
    const timerStartedAt = performance.now();

    const firstFrame = requestAnimationFrame(() => {
      secondFrame = requestAnimationFrame(() => {
        const initialRenderMs =
          performance.now() - renderStartedAt.current;

        const graphElement = document.querySelector(
  ".network-svg"
);

const svgElements =
  graphElement?.tagName === "CANVAS"
    ? 1
    : graphElement?.querySelectorAll("*").length ?? 0;

        setMetrics((current) => ({
          ...current,
          initialRenderMs,
          svgElements,
        }));
      });
    });

    const delayTimer = window.setTimeout(() => {
      const actualDelay = performance.now() - timerStartedAt;

      setMetrics((current) => ({
        ...current,
        eventLoopDelayMs: Math.max(0, actualDelay - 1000),
      }));
    }, 1000);

    return () => {
      cancelAnimationFrame(firstFrame);

      if (secondFrame) {
        cancelAnimationFrame(secondFrame);
      }

      clearTimeout(delayTimer);
    };
  }, [nodeCount]);

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "24px",
        background: "#0b1b32",
        color: "#e5c9d7",
      }}
    >
      <h1>AtmoGraph visualization benchmark</h1>

      <p>
        Testing the production NetworkGraph component with
        deterministic synthetic data.
      </p>

      <nav
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "10px",
          marginBottom: "18px",
        }}
      >
        {[100, 1000, 2000, 5000].map((size) => (
          <a
            key={size}
            href={`?benchmark=${size}`}
            style={{
              padding: "8px 12px",
              border: "1px solid #83a6ce",
              borderRadius: "6px",
              color: "#e5c9d7",
            }}
          >
            {size} nodes
          </a>
        ))}
      </nav>

      <section
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px",
          marginBottom: "18px",
        }}
      >
        <Metric
          label="Nodes"
          value={graph.metadata.nodeCount}
        />
        <Metric
          label="Edges"
          value={graph.metadata.edgeCount}
        />
        <Metric
          label="Initial render"
          value={
            metrics.initialRenderMs === null
              ? "Measuring..."
              : `${metrics.initialRenderMs.toFixed(1)} ms`
          }
        />
        <Metric
          label="Event-loop delay"
          value={
            metrics.eventLoopDelayMs === null
              ? "Measuring..."
              : `${metrics.eventLoopDelayMs.toFixed(1)} ms`
          }
        />
        <Metric
          label="Graph elements"
          value={metrics.svgElements ?? "Measuring..."}
        />
      </section>

      <section
        style={{
          minHeight: "620px",
          border: "1px solid #26415e",
          borderRadius: "12px",
          overflow: "hidden",
        }}
      >
        <NetworkGraph
          selectedNode={selectedNode}
          onSelectNode={handleSelectNode}
          networkNodes={graph.nodes}
          networkEdges={graph.edges}
        />
      </section>

      <p>
        Selected node: {selectedNode?.name ?? "None"}
      </p>
    </main>
  );
}


function Metric({ label, value }) {
  return (
    <article
      style={{
        padding: "12px",
        border: "1px solid #26415e",
        borderRadius: "8px",
        background: "#0d1e4c",
      }}
    >
      <strong>{label}</strong>
      <div>{value}</div>
    </article>
  );
}


export default GraphBenchmark;