import {
  useCallback,
  useEffect,
  useRef,
} from "react";
import * as d3 from "d3";


const riskColours = {
  low: "#FEB909",
  medium: "#fe8309",
  high: "#832A1A",
};


function getRisk(node) {
  const score = Number(node.properties?.risk_score ?? 0);

  if (score >= 0.25) return "high";
  if (score >= 0.15) return "medium";
  return "low";
}


function LargeNetworkCanvas({
  selectedNode,
  onSelectNode,
  networkNodes = [],
  networkEdges = [],
}) {
  const canvasRef = useRef(null);
  const zoomRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;

    if (!canvas || !networkNodes.length) {
      return undefined;
    }

    const context = canvas.getContext("2d");
    const columns = Math.ceil(
      Math.sqrt(networkNodes.length)
    );

    const nodes = networkNodes.map((node, index) => ({
      ...node,
      risk: getRisk(node),
      x:
        Number.isFinite(node.x)
          ? node.x
          : 60 + (index % columns) * 72,
      y:
        Number.isFinite(node.y)
          ? node.y
          : 60 + Math.floor(index / columns) * 72,
    }));

    const nodesById = new Map(
      nodes.map((node) => [node.id, node])
    );

    const links = networkEdges
      .map((edge) => ({
        source: nodesById.get(
          typeof edge.source === "object"
            ? edge.source.id
            : edge.source
        ),
        target: nodesById.get(
          typeof edge.target === "object"
            ? edge.target.id
            : edge.target
        ),
      }))
      .filter((edge) => edge.source && edge.target);

    let width = 900;
    const height = 520;
    let currentTransform = d3.zoomIdentity;

    const draw = () => {
      const pixelRatio = window.devicePixelRatio || 1;

      context.setTransform(
        pixelRatio,
        0,
        0,
        pixelRatio,
        0,
        0
      );
      context.clearRect(0, 0, width, height);
      context.save();

      context.translate(
        currentTransform.x,
        currentTransform.y
      );
      context.scale(
        currentTransform.k,
        currentTransform.k
      );

      context.beginPath();

      links.forEach((link) => {
        context.moveTo(link.source.x, link.source.y);
        context.lineTo(link.target.x, link.target.y);
      });

      context.strokeStyle = "rgba(131, 166, 206, 0.35)";
      context.lineWidth = 1 / currentTransform.k;
      context.stroke();

      nodes.forEach((node) => {
        context.beginPath();
        context.arc(node.x, node.y, 7, 0, Math.PI * 2);
        context.fillStyle = riskColours[node.risk];
        context.fill();

        if (node.id === selectedNode?.id) {
          context.strokeStyle = "#e5c9d7";
          context.lineWidth = 3 / currentTransform.k;
          context.stroke();
        }
      });

      context.restore();
    };

    const resizeCanvas = () => {
      const pixelRatio = window.devicePixelRatio || 1;

      width = canvas.clientWidth || 900;
      canvas.width = Math.round(width * pixelRatio);
      canvas.height = Math.round(height * pixelRatio);

      draw();
    };

    const maxX = d3.max(nodes, (node) => node.x) ?? width;
    const maxY = d3.max(nodes, (node) => node.y) ?? height;
    const minX = d3.min(nodes, (node) => node.x) ?? 0;
    const minY = d3.min(nodes, (node) => node.y) ?? 0;

    const graphWidth = Math.max(1, maxX - minX);
    const graphHeight = Math.max(1, maxY - minY);

    const canvasSelection = d3.select(canvas);

    const zoomBehaviour = d3
      .zoom()
      .scaleExtent([0.05, 8])
      .on("zoom", (event) => {
        currentTransform = event.transform;
        draw();
      });

    zoomRef.current = {
      selection: canvasSelection,
      behaviour: zoomBehaviour,
    };

    resizeCanvas();

    const initialScale = Math.min(
      1,
      (width - 40) / graphWidth,
      (height - 40) / graphHeight
    );

    const initialTransform = d3.zoomIdentity
      .translate(
        width / 2 -
          ((minX + maxX) / 2) * initialScale,
        height / 2 -
          ((minY + maxY) / 2) * initialScale
      )
      .scale(initialScale);

    canvasSelection.call(zoomBehaviour);

    zoomRef.current.initialTransform = initialTransform;

    canvasSelection.call(
      zoomBehaviour.transform,
      initialTransform
    );

    canvasSelection.on("click.node-selection", (event) => {
      const [pointerX, pointerY] = d3.pointer(
        event,
        canvas
      );

      const [graphX, graphY] =
        currentTransform.invert([
          pointerX,
          pointerY,
        ]);

      const hitRadius = 12 / currentTransform.k;
      let nearestNode = null;
      let nearestDistance = hitRadius * hitRadius;

      nodes.forEach((node) => {
        const horizontalDistance = node.x - graphX;
        const verticalDistance = node.y - graphY;
        const distance =
          horizontalDistance * horizontalDistance +
          verticalDistance * verticalDistance;

        if (distance <= nearestDistance) {
          nearestNode = node;
          nearestDistance = distance;
        }
      });

      if (nearestNode) {
        onSelectNode(nearestNode);
      }
    });

    const resizeObserver = new ResizeObserver(
      resizeCanvas
    );
    resizeObserver.observe(canvas);

    return () => {
      resizeObserver.disconnect();
      canvasSelection.on(".zoom", null);
      canvasSelection.on(".node-selection", null);
      zoomRef.current = null;
    };
  }, [
    networkNodes,
    networkEdges,
    selectedNode,
    onSelectNode,
  ]);

  const zoomBy = useCallback((factor) => {
    const zoom = zoomRef.current;

    if (!zoom) return;

    zoom.selection
      .transition()
      .duration(150)
      .call(zoom.behaviour.scaleBy, factor);
  }, []);

  const resetZoom = useCallback(() => {
  const zoom = zoomRef.current;
  if (!zoom) return;

  zoom.selection
    .transition()
    .duration(150)
    .call(
      zoom.behaviour.transform,
      zoom.initialTransform ?? d3.zoomIdentity
    );
}, []);

  return (
    <div className="network-canvas">
      <div className="network-controls">
        <button
          type="button"
          onClick={() => zoomBy(1.25)}
          aria-label="Zoom in"
        >
          +
        </button>

        <button
          type="button"
          onClick={() => zoomBy(0.8)}
          aria-label="Zoom out"
        >
          −
        </button>

        <button type="button" onClick={resetZoom}>
          Reset
        </button>
      </div>

      <canvas
        ref={canvasRef}
        className="network-svg"
        style={{
          display: "block",
          width: "100%",
          height: "520px",
        }}
        aria-label="Large supply-chain network rendered with Canvas"
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


export default LargeNetworkCanvas;