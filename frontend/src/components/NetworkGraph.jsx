import { useMemo, useState } from "react";
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

const LOCATION_COORDS = {
  rotterdam: [4.48, 51.92], netherlands: [5.29, 52.13], europe: [15, 50], london: [-0.13, 51.51],
  hamburg: [9.99, 53.55], shanghai: [121.47, 31.23], shenzhen: [114.06, 22.54], china: [104.2, 35.9],
  singapore: [103.82, 1.35], mumbai: [72.88, 19.08], india: [78.96, 20.59], tokyo: [139.69, 35.68],
  japan: [138.25, 36.2], dubai: [55.27, 25.2], sydney: [151.21, -33.87], australia: [133.78, -25.27],
  newyork: [-74.01, 40.71], "new york": [-74.01, 40.71], losangeles: [-118.24, 34.05],
  "los angeles": [-118.24, 34.05], usa: [-98.58, 39.83], america: [-98.58, 39.83],
  brazil: [-51.93, -14.24], sao: [-46.63, -23.55], cape: [18.42, -33.93], africa: [20, 2], kolkata: [88.36, 22.57],
};

const projection = geoNaturalEarth1().fitExtent([[28, 32], [972, 488]], { type: "Sphere" });
const mapPath = geoPath(projection);
const countries = feature(world, world.objects.countries).features;

function project(coordinates) { return projection(coordinates) || [500, 260]; }
function endpointId(endpoint) { return typeof endpoint === "object" ? endpoint.id : endpoint; }
function nodePoint(node, index, total) {
  const text = `${node.name || ""} ${node.location || ""} ${node.country || ""}`.toLowerCase();
  const match = Object.entries(LOCATION_COORDS).find(([key]) => text.includes(key));
  if (match) return project(match[1]);
  const angle = (index / Math.max(total, 1)) * Math.PI * 2 - Math.PI / 2;
  return [500 + Math.cos(angle) * 275, 250 + Math.sin(angle) * 145];
}

export default function NetworkGraph({ networkNodes = [], networkEdges = [], selectedNode, onSelectNode }) {
  const [zoom, setZoom] = useState(1);
  const points = useMemo(() => new Map(networkNodes.map((node, index) => [node.id, nodePoint(node, index, networkNodes.length)])), [networkNodes]);
  return (
    <div className="network-canvas geo-network">
      <div className="geo-controls" aria-label="Map zoom controls">
        <button type="button" onClick={() => setZoom((value) => Math.min(1.7, value + 0.15))} aria-label="Zoom in">+</button>
        <button type="button" onClick={() => setZoom((value) => Math.max(0.75, value - 0.15))} aria-label="Zoom out">−</button>
        <button type="button" onClick={() => setZoom(1)}>Reset</button>
      </div>
      <svg className="network-svg geo-map" viewBox="0 0 1000 520" role="img" aria-label="Geographic supply-chain network map">
        <defs><filter id="nodeGlow"><feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter><linearGradient id="oceanGlow"><stop stopColor="#17334c"/><stop offset="1" stopColor="#081727"/></linearGradient></defs>
        <rect width="1000" height="520" fill="url(#oceanGlow)" />
        <g className="geo-grid"><path d="M0 130H1000M0 260H1000M0 390H1000M250 0V520M500 0V520M750 0V520" /></g>
        <g style={{ transform: `translate(500px,260px) scale(${zoom}) translate(-500px,-260px)` }} className="geo-stage">
          <path className="geo-sphere" d={mapPath({ type: "Sphere" })} />
          <g className="geo-countries">{countries.map((country) => <path className="geo-country" d={mapPath(country)} key={country.id} />)}</g>
          <g>{networkEdges.map((edge, index) => {
            const source = points.get(endpointId(edge.source ?? edge.from ?? edge.start));
            const target = points.get(endpointId(edge.target ?? edge.to ?? edge.end));
            if (!source || !target) return null;
            const mx = (source[0] + target[0]) / 2;
            const my = Math.min(source[1], target[1]) - Math.max(28, Math.abs(target[0] - source[0]) * 0.13);
            return <path className="geo-route" d={`M${source[0]} ${source[1]} Q${mx} ${my} ${target[0]} ${target[1]}`} key={edge.id || index} />;
          })}</g>
          <g>{networkNodes.map((node) => {
            const [x, y] = points.get(node.id);
            const risk = String(node.predictionRisk || node.risk || "low").toLowerCase();
            const selected = selectedNode?.id === node.id;
            const select = () => onSelectNode?.(node);
            return <g className={`geo-node ${risk}${selected ? " selected" : ""}`} key={node.id} transform={`translate(${x} ${y})`} onClick={select} role="button" tabIndex="0" onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") select(); }}><circle className="node-pulse" r={selected ? 18 : 13}/><circle className="node-core" r={selected ? 7 : 5} filter="url(#nodeGlow)"/><text x="10" y="-9">{node.name || node.location || node.id}</text></g>;
          })}</g>
        </g>
      </svg>
      <div className="geo-legend"><span>Stable</span><span className="watch">Watch</span><span className="critical">Critical</span></div>
    </div>
  );
}
