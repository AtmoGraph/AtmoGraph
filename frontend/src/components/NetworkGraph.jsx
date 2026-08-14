import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { networkLinks, networkNodes } from "../data/networkData";

const riskColours = {
  low: "#FEB909",
  medium: "#fe8309",
  high: "#832A1A",
};

function NetworkGraph({ selectedNode, onSelectNode }) {
  const svgRef = useRef(null);

  useEffect(() => {
    const width = 900;
    const height = 520;

    // Use copies because D3 adds position properties to the objects.
    const nodes = networkNodes.map((node) => ({ ...node }));
    const links = networkLinks.map((link) => ({ ...link }));

    const svg = d3.select(svgRef.current);

    svg.selectAll("*").remove();

    svg
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    const graphLayer = svg.append("g");

    const linkElements = graphLayer
      .append("g")
      .attr("class", "network-links")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "network-link");

    const nodeElements = graphLayer
      .append("g")
      .attr("class", "network-nodes")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("class", "network-node")
      .attr("tabindex", 0)
      .attr("role", "button")
      .attr("aria-label", (node) => `${node.name}, ${node.risk} risk`)
      .on("click", (_event, node) => {
        onSelectNode(node);
      })
      .on("keydown", (event, node) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelectNode(node);
        }
      });

    nodeElements
      .append("circle")
      .attr("class", "node-halo")
      .attr("r", (node) => (node.id === selectedNode?.id ? 29 : 24))
      .attr("stroke", (node) => riskColours[node.risk]);

    nodeElements
      .append("circle")
      .attr("class", "node-core")
      .attr("r", 14)
      .attr("fill", (node) => riskColours[node.risk]);

    nodeElements
      .append("text")
      .attr("class", "node-name")
      .attr("text-anchor", "middle")
      .attr("y", 42)
      .text((node) => node.name);

    nodeElements
      .append("text")
      .attr("class", "node-location")
      .attr("text-anchor", "middle")
      .attr("y", 58)
      .text((node) => node.location);

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((node) => node.id)
          .distance(145)
      )
      .force("charge", d3.forceManyBody().strength(-620))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(70));

    simulation.on("tick", () => {
  const horizontalPadding = 95;
  const verticalPadding = 75;

  nodes.forEach((node) => {
    node.x = Math.max(
      horizontalPadding,
      Math.min(width - horizontalPadding, node.x)
    );

    node.y = Math.max(
      verticalPadding,
      Math.min(height - verticalPadding, node.y)
    );
  });

  linkElements
    .attr("x1", (link) => link.source.x)
    .attr("y1", (link) => link.source.y)
    .attr("x2", (link) => link.target.x)
    .attr("y2", (link) => link.target.y);

  nodeElements.attr(
    "transform",
    (node) => `translate(${node.x}, ${node.y})`
  );
});

    return () => {
      simulation.stop();
    };
  }, [selectedNode, onSelectNode]);

  return (
    <div className="network-canvas">
      <svg
        ref={svgRef}
        className="network-svg"
        aria-label="Static global supply-chain network"
      />

      <div className="network-legend">
        <span>
          <i className="legend-dot low" />
          Stable
        </span>

        <span>
          <i className="legend-dot medium" />
          Watch
        </span>

        <span>
          <i className="legend-dot high" />
          Critical
        </span>
      </div>
    </div>
  );
}

export default NetworkGraph;