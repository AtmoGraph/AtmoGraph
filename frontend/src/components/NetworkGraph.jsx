import { useEffect, useRef } from "react";
import * as d3 from "d3";

const riskColours = {
  low: "#FEB909",
  medium: "#fe8309",
  high: "#832A1A",
};

function getRisk(node) {
  const riskScore = Number(node.properties?.risk_score ?? 0);

  if (riskScore >= 0.25) {
    return "high";
  }

  if (riskScore >= 0.15) {
    return "medium";
  }

  return "low";
}

function getLocation(node) {
  return (
    node.properties?.country ||
    node.properties?.region ||
    "Unknown"
  );
}

function getShortName(name = "") {
  const maxLength = 22;

  if (name.length <= maxLength) {
    return name;
  }

  return `${name.slice(0, maxLength - 3)}...`;
}

function NetworkGraph({
  selectedNode,
  onSelectNode,
  networkNodes = [],
  networkEdges = [],
}) {
  const svgRef = useRef(null);

  useEffect(() => {
    const width = 900;
    const height = 520;

    if (!networkNodes.length) {
      return;
    }

    const nodes = networkNodes.map((node) => ({
      ...node,
      risk: getRisk(node),
      location: getLocation(node),
      shortName: getShortName(node.name),
    }));

    const nodeIds = new Set(nodes.map((node) => node.id));

    const links = networkEdges
      .filter(
        (edge) =>
          nodeIds.has(edge.source) &&
          nodeIds.has(edge.target)
      )
      .map((edge) => ({ ...edge }));

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
      .attr(
        "aria-label",
        (node) => `${node.name}, ${node.risk} risk`
      )
      .on("click", (_event, node) => {
        onSelectNode(node);
      })
      .on("keydown", (event, node) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelectNode(node);
        }
      })
      .call(
        d3
          .drag()
          .on("start", (event, node) => {
            if (!event.active) {
              simulation.alphaTarget(0.3).restart();
            }

            node.fx = node.x;
            node.fy = node.y;
          })
          .on("drag", (event, node) => {
            node.fx = event.x;
            node.fy = event.y;
          })
          .on("end", (event, node) => {
            if (!event.active) {
              simulation.alphaTarget(0);
            }

            node.fx = null;
            node.fy = null;
          })
      );

    nodeElements
      .append("title")
      .text(
        (node) =>
          `${node.name}\n${node.type}\n${node.location}\n${node.risk} risk`
      );

    nodeElements
      .append("circle")
      .attr("class", "node-halo")
      .attr("r", (node) =>
        node.id === selectedNode?.id ? 29 : 24
      )
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
      .text((node) => node.shortName);

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
          .distance(175)
          .strength(0.7)
      )
      .force(
        "charge",
        d3.forceManyBody().strength(-900)
      )
      .force(
        "center",
        d3.forceCenter(width / 2, height / 2)
      )
      .force(
        "collision",
        d3.forceCollide().radius(82).strength(1)
      )
      .force(
        "x",
        d3.forceX(width / 2).strength(0.025)
      )
      .force(
        "y",
        d3.forceY(height / 2).strength(0.025)
      );

    simulation.on("tick", () => {
      const horizontalPadding = 105;
      const verticalPadding = 70;

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
  }, [
    networkNodes,
    networkEdges,
    selectedNode,
    onSelectNode,
  ]);

  return (
    <div className="network-canvas">
      <svg
        ref={svgRef}
        className="network-svg"
        aria-label="Global supply-chain network"
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