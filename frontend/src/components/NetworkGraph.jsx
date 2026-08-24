import { useEffect, useRef } from "react";
import * as d3 from "d3";
import LargeNetworkCanvas from "./LargeNetworkCanvas";

const riskColours = {
  low: "#FEB909",
  medium: "#fe8309",
  high: "#832A1A",
};

function getRisk(node) {
  const riskScore = Number(node.properties?.risk_score ?? 0);

  if (riskScore >= 0.25) return "high";
  if (riskScore >= 0.15) return "medium";
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

function SvgNetworkGraph({
  selectedNode,
  onSelectNode,
  networkNodes = [],
  networkEdges = [],
}) {
  const svgRef = useRef(null);
  const zoomRef = useRef(null);

  useEffect(() => {
    const width = 900;
    const height = 520;

    if (!networkNodes.length) return;

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

    const graphLayer = svg
      .append("g")
      .attr("class", "graph-layer");

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
        (node) =>
          `${node.name}, ${node.type}, ${node.risk} risk`
      )
      .on("click", (event, node) => {
        event.stopPropagation();
        onSelectNode(node);
      })
      .on("keydown", (event, node) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelectNode(node);
        }
      });

    nodeElements
      .append("title")
      .text(
        (node) =>
          `${node.name}\nType: ${node.type}\nLocation: ${node.location}\nRisk: ${node.risk}`
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

    nodeElements.call(
      d3
        .drag()
        .on("start", (event, node) => {
          event.sourceEvent.stopPropagation();

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

    const zoomBehavior = d3
      .zoom()
      .scaleExtent([0.45, 2.5])
      .on("zoom", (event) => {
        graphLayer.attr("transform", event.transform);
      });

    zoomRef.current = zoomBehavior;

    svg.call(zoomBehavior);

    // Keep node clicks from being treated as double-click zoom.
    svg.on("dblclick.zoom", null);

    return () => {
      simulation.stop();
      svg.on(".zoom", null);
      zoomRef.current = null;
    };
  }, [
    networkNodes,
    networkEdges,
    selectedNode,
    onSelectNode,
  ]);

  const zoomBy = (factor) => {
    if (!svgRef.current || !zoomRef.current) return;

    d3.select(svgRef.current)
      .transition()
      .duration(200)
      .call(zoomRef.current.scaleBy, factor);
  };

  const resetZoom = () => {
    if (!svgRef.current || !zoomRef.current) return;

    d3.select(svgRef.current)
      .transition()
      .duration(250)
      .call(
        zoomRef.current.transform,
        d3.zoomIdentity
      );
  };

  return (
    <div className="network-canvas">
      <div className="network-controls">
        <button
          type="button"
          onClick={() => zoomBy(1.2)}
          aria-label="Zoom in"
          title="Zoom in"
        >
          +
        </button>

        <button
          type="button"
          onClick={() => zoomBy(0.8)}
          aria-label="Zoom out"
          title="Zoom out"
        >
          −
        </button>

        <button
          type="button"
          onClick={resetZoom}
          title="Reset graph view"
        >
          Reset
        </button>
      </div>

      <svg
        ref={svgRef}
        className="network-svg"
        aria-label="Interactive global supply-chain network"
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

      <div className="network-help">
        Scroll to zoom · Drag empty space to pan · Drag node to move · Click node for details
      </div>
    </div>
  );
}

function NetworkGraph(props) {
  const nodeCount = props.networkNodes?.length ?? 0;

  if (nodeCount >= 100) {
    return <LargeNetworkCanvas {...props} />;
  }

  return <SvgNetworkGraph {...props} />;
}


export default NetworkGraph;