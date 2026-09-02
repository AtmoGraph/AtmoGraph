import { useEffect, useMemo, useState } from "react";
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
} from "d3";

const WIDTH = 1000;
const HEIGHT = 520;

function nodeRisk(node) {
  return (
    node.predictionRisk ||
    node.properties?.risk ||
    node.risk ||
    "low"
  ).toLowerCase();
}

function TopologyGraph({
  networkNodes,
  networkEdges,
  selectedNode,
  onSelectNode,
}) {
  const graph = useMemo(() => {
    const nodes = networkNodes.map((node, index) => {
      const angle = (index / Math.max(1, networkNodes.length)) * Math.PI * 2;
      return {
        ...node,
        x: WIDTH / 2 + Math.cos(angle) * 180,
        y: HEIGHT / 2 + Math.sin(angle) * 180,
      };
    });
    const links = networkEdges.map((edge) => ({ ...edge }));
    return { nodes, links };
  }, [networkNodes, networkEdges]);

  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!graph.nodes.length) return undefined;

    const simulation = forceSimulation(graph.nodes)
      .force(
        "link",
        forceLink(graph.links)
          .id((node) => node.id)
          .distance(115)
          .strength(0.7)
      )
      .force("charge", forceManyBody().strength(-430))
      .force("center", forceCenter(WIDTH / 2, HEIGHT / 2))
      .force("collision", forceCollide(34))
      .alpha(1)
      .alphaDecay(0.035)
      .on("tick", () => setTick((value) => value + 1));

    return () => simulation.stop();
  }, [graph]);

  void tick;

  if (!graph.nodes.length) {
    return <div className="topology-empty">No graph data available.</div>;
  }

  return (
    <div className="topology-wrap">
      <svg
        className="topology-graph"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label="Force-directed supply chain topology"
      >
        <g className="topology-links">
          {graph.links.map((link, index) => (
            <line
              key={`${link.source?.id || link.source}-${link.target?.id || link.target}-${index}`}
              x1={link.source?.x || 0}
              y1={link.source?.y || 0}
              x2={link.target?.x || 0}
              y2={link.target?.y || 0}
            />
          ))}
        </g>

        <g className="topology-nodes">
          {graph.nodes.map((node) => (
            <g
              className={`topology-node risk-${nodeRisk(node)} ${
                selectedNode?.id === node.id ? "selected" : ""
              }`}
              key={node.id}
              transform={`translate(${node.x || 0}, ${node.y || 0})`}
              role="button"
              tabIndex="0"
              aria-label={`Select ${node.name}`}
              onClick={() => onSelectNode(node)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectNode(node);
                }
              }}
            >
              <circle r={selectedNode?.id === node.id ? 14 : 11} />
              <text y="-18" textAnchor="middle">
                {node.name}
              </text>
              <text className="topology-node-type" y="25" textAnchor="middle">
                {node.type}
              </text>
            </g>
          ))}
        </g>
      </svg>

      <div className="topology-legend" aria-label="Topology risk legend">
        <span><i className="low" />Stable</span>
        <span><i className="medium" />Watch</span>
        <span><i className="high" />Critical</span>
      </div>
    </div>
  );
}

export default TopologyGraph;
