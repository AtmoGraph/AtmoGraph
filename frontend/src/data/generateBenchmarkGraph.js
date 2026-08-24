const NODE_TYPES = [
  "Supplier",
  "Factory",
  "Port",
  "DistributionCentre",
  "Market",
];

const COUNTRIES = [
  "Sweden",
  "India",
  "Netherlands",
  "Singapore",
  "United States",
  "Taiwan",
  "Germany",
];

function validateNodeCount(nodeCount) {
  const parsedCount = Number(nodeCount);

  if (
    !Number.isInteger(parsedCount) ||
    parsedCount < 1 ||
    parsedCount > 5000
  ) {
    throw new RangeError(
      "Benchmark node count must be between 1 and 5000"
    );
  }

  return parsedCount;
}

export function generateBenchmarkGraph(nodeCount = 1000) {
  const count = validateNodeCount(nodeCount);
  const columns = Math.ceil(Math.sqrt(count));
  const spacing = 72;
  const margin = 60;

  const nodes = Array.from({ length: count }, (_, index) => {
    const column = index % columns;
    const row = Math.floor(index / columns);
    const riskScore = (index % 10) / 10;

    return {
      id: `benchmark-node-${index}`,
      name: `Benchmark Node ${index + 1}`,
      type: NODE_TYPES[index % NODE_TYPES.length],
      x: margin + column * spacing,
      y: margin + row * spacing,
      properties: {
        risk_score: riskScore,
        country: COUNTRIES[index % COUNTRIES.length],
        capacity: 50 + (index % 51),
        benchmark: true,
      },
    };
  });

  const edges = [];

  for (let index = 0; index < count; index += 1) {
    if (index + 1 < count) {
      edges.push({
        source: `benchmark-node-${index}`,
        target: `benchmark-node-${index + 1}`,
        type: "SHIPS_TO",
        properties: {
          benchmark: true,
        },
      });
    }

    if (index + columns < count) {
      edges.push({
        source: `benchmark-node-${index}`,
        target: `benchmark-node-${index + columns}`,
        type: "SUPPLIES",
        properties: {
          benchmark: true,
        },
      });
    }
  }

  return {
    nodes,
    edges,
    metadata: {
      nodeCount: nodes.length,
      edgeCount: edges.length,
      columns,
      width: margin * 2 + columns * spacing,
      height:
        margin * 2 +
        Math.ceil(count / columns) * spacing,
    },
  };
}