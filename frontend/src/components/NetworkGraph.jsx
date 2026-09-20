import { useMemo, useState } from "react";
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

import { globalReferencePorts } from "../data/globalReferencePorts";


const projection = geoNaturalEarth1().fitExtent(
  [[28, 32], [972, 488]],
  { type: "Sphere" }
);
const mapPath = geoPath(projection);
const countries = feature(
  world,
  world.objects.countries
).features;


function endpointId(endpoint) {
  return typeof endpoint === "object"
    ? endpoint?.id
    : endpoint;
}


function edgeType(edge) {
  return edge.type ?? edge.relationship_type;
}


function coordinatesFor(node) {
  const latitude = Number(
    node.latitude ?? node.properties?.latitude
  );
  const longitude = Number(
    node.longitude ?? node.properties?.longitude
  );

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    latitude < -90 ||
    latitude > 90 ||
    longitude < -180 ||
    longitude > 180
  ) {
    return null;
  }

  return [longitude, latitude];
}


function nodePoint(node) {
  const coordinates = coordinatesFor(node);
  return coordinates ? projection(coordinates) : null;
}


function buildShippingRoutes(
  networkNodes,
  networkEdges,
  points
) {
  const routeNodeIds = new Set(
    networkNodes
      .filter((node) => node.type === "ShippingRoute")
      .map((node) => node.id)
  );
  const routeEndpoints = new Map();

  networkEdges.forEach((edge) => {
    const type = edgeType(edge);

    if (type !== "FROM" && type !== "TO") {
      return;
    }

    const sourceId = endpointId(
      edge.source ?? edge.from ?? edge.start
    );
    const targetId = endpointId(
      edge.target ?? edge.to ?? edge.end
    );
    const routeId = routeNodeIds.has(sourceId)
      ? sourceId
      : routeNodeIds.has(targetId)
        ? targetId
        : null;
    const portId = routeId === sourceId
      ? targetId
      : sourceId;

    if (!routeId || !points.has(portId)) {
      return;
    }

    const endpoints = routeEndpoints.get(routeId) ?? {};
    endpoints[type.toLowerCase()] = portId;
    routeEndpoints.set(routeId, endpoints);
  });

  return Array.from(routeEndpoints, ([routeId, endpoints]) => ({
    id: routeId,
    source: endpoints.from
      ? points.get(endpoints.from)
      : null,
    target: endpoints.to
      ? points.get(endpoints.to)
      : null,
  })).filter((route) => route.source && route.target);
}


function routePath(source, target) {
  const middleX = (source[0] + target[0]) / 2;
  const middleY =
    Math.min(source[1], target[1]) -
    Math.max(28, Math.abs(target[0] - source[0]) * 0.13);

  return (
    `M${source[0]} ${source[1]} ` +
    `Q${middleX} ${middleY} ${target[0]} ${target[1]}`
  );
}


export default function NetworkGraph({
  networkNodes = [],
  networkEdges = [],
  selectedNode,
  onSelectNode,
}) {
  const [zoom, setZoom] = useState(1);

  const geographicNodes = useMemo(
    () => networkNodes
      .map((node) => ({ node, point: nodePoint(node) }))
      .filter(({ point }) => point),
    [networkNodes]
  );

  const points = useMemo(
    () => new Map(
      geographicNodes.map(({ node, point }) => [
        node.id,
        point,
      ])
    ),
    [geographicNodes]
  );

  const referencePorts = useMemo(
    () => globalReferencePorts.map((port) => ({
      ...port,
      point: nodePoint(port),
    })),
    []
  );

  const shippingRoutes = useMemo(
    () => buildShippingRoutes(
      networkNodes,
      networkEdges,
      points
    ),
    [networkNodes, networkEdges, points]
  );

  return (
    <div className="network-canvas geo-network">
      <div
        className="geo-controls"
        aria-label="Map zoom controls"
      >
        <button
          type="button"
          onClick={() => setZoom((value) =>
            Math.min(1.7, value + 0.15)
          )}
          aria-label="Zoom in"
        >
          +
        </button>
        <button
          type="button"
          onClick={() => setZoom((value) =>
            Math.max(0.75, value - 0.15)
          )}
          aria-label="Zoom out"
        >
          −
        </button>
        <button type="button" onClick={() => setZoom(1)}>
          Reset
        </button>
      </div>

      <svg
        className="network-svg geo-map"
        viewBox="0 0 1000 520"
        role="img"
        aria-label="Geographic supply-chain port network map"
      >
        <defs>
          <filter id="nodeGlow">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <linearGradient id="oceanGlow">
            <stop stopColor="#17334c" />
            <stop offset="1" stopColor="#081727" />
          </linearGradient>
        </defs>

        <rect
          width="1000"
          height="520"
          fill="url(#oceanGlow)"
        />
        <g className="geo-grid">
          <path d="M0 130H1000M0 260H1000M0 390H1000M250 0V520M500 0V520M750 0V520" />
        </g>
        <g
          style={{
            transform:
              `translate(500px,260px) scale(${zoom}) ` +
              "translate(-500px,-260px)",
          }}
          className="geo-stage"
        >
          <path
            className="geo-sphere"
            d={mapPath({ type: "Sphere" })}
          />
          <g className="geo-countries">
            {countries.map((country) => (
              <path
                className="geo-country"
                d={mapPath(country)}
                key={country.id}
              />
            ))}
          </g>

          <g className="geo-reference-ports">
            {referencePorts.map((port) => {
              const [x, y] = port.point;

              return (
                <g
                  className="geo-reference-port"
                  key={port.id}
                  transform={`translate(${x} ${y})`}
                  role="img"
                  tabIndex="0"
                  aria-label={`${port.name}, ${port.country}; reference port`}
                >
                  <circle r="2.8" />
                  <text x="7" y="-5">
                    {port.name}
                  </text>
                </g>
              );
            })}
          </g>

          <g className="geo-shipping-routes">
            {shippingRoutes.map((route) => (
              <path
                className="geo-route"
                d={routePath(route.source, route.target)}
                key={route.id}
              />
            ))}
          </g>

          <g className="geo-operational-ports">
            {geographicNodes.map(({ node, point }) => {
              const [x, y] = point;
              const risk = String(
                node.predictionRisk ??
                node.properties?.risk ??
                node.risk ??
                "low"
              ).toLowerCase();
              const selected = selectedNode?.id === node.id;
              const select = () => onSelectNode?.(node);

              return (
                <g
                  className={
                    `geo-node ${risk}` +
                    (selected ? " selected" : "")
                  }
                  key={node.id}
                  transform={`translate(${x} ${y})`}
                  onClick={select}
                  role="button"
                  tabIndex="0"
                  aria-label={`${node.name || node.id}; operational port`}
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" ||
                      event.key === " "
                    ) {
                      event.preventDefault();
                      select();
                    }
                  }}
                >
                  <circle
                    className="node-pulse"
                    r={selected ? 18 : 13}
                  />
                  <circle
                    className="node-core"
                    r={selected ? 7 : 5}
                    filter="url(#nodeGlow)"
                  />
                  <text x="10" y="-9">
                    {node.name || node.id}
                  </text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>

      <div className="geo-legend">
        <span>Operational port</span>
        <span className="reference">Reference port</span>
        <span className="route">Shipping route</span>
        <span className="watch">Watch</span>
        <span className="critical">Critical</span>
      </div>
    </div>
  );
}
