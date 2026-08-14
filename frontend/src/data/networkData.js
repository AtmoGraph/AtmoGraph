export const networkNodes = [
  {
    id: "supplier-sweden",
    name: "Nordic Minerals",
    type: "Supplier",
    location: "Kiruna, Sweden",
    risk: "medium",
    capacity: "82%",
  },
  {
    id: "port-rotterdam",
    name: "Port of Rotterdam",
    type: "Port",
    location: "Rotterdam, Netherlands",
    risk: "high",
    capacity: "54%",
  },
  {
    id: "supplier-taiwan",
    name: "Silica Systems",
    type: "Supplier",
    location: "Hsinchu, Taiwan",
    risk: "low",
    capacity: "94%",
  },
  {
    id: "factory-india",
    name: "Atlas Assembly",
    type: "Factory",
    location: "Pune, India",
    risk: "medium",
    capacity: "76%",
  },
  {
    id: "port-singapore",
    name: "Port of Singapore",
    type: "Port",
    location: "Singapore",
    risk: "low",
    capacity: "91%",
  },
  {
    id: "distribution-usa",
    name: "North America DC",
    type: "Distribution Centre",
    location: "Chicago, USA",
    risk: "medium",
    capacity: "73%",
  },
  {
    id: "market-europe",
    name: "European Market",
    type: "Market",
    location: "Berlin, Germany",
    risk: "high",
    capacity: "61%",
  },
];

export const networkLinks = [
  { source: "supplier-sweden", target: "port-rotterdam" },
  { source: "port-rotterdam", target: "factory-india" },
  { source: "supplier-taiwan", target: "factory-india" },
  { source: "factory-india", target: "port-singapore" },
  { source: "factory-india", target: "market-europe" },
  { source: "port-singapore", target: "distribution-usa" },
  { source: "port-rotterdam", target: "market-europe" },
];

export const disruptions = [
  {
    id: 1,
    severity: "Critical",
    title: "Port congestion escalating",
    description:
      "Rotterdam terminals are reporting a severe vessel backlog.",
    time: "12 min ago",
    impact: "4 routes · 7 nodes",
  },
  {
    id: 2,
    severity: "Warning",
    title: "Rail capacity reduced",
    description:
      "Central European freight capacity has decreased by 18%.",
    time: "1 hr ago",
    impact: "2 routes · 3 nodes",
  },
  {
    id: 3,
    severity: "Warning",
    title: "Supplier lead-time variance",
    description:
      "Nordic metals lead time has exceeded its normal range.",
    time: "3 hrs ago",
    impact: "1 route · 2 nodes",
  },
];