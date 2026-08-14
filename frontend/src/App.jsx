import { useCallback, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bell,
  Boxes,
  LayoutDashboard,
  Network,
  Route,
  Search,
  Ship,
  Warehouse,
} from "lucide-react";

import NetworkGraph from "./components/NetworkGraph";
import { disruptions, networkNodes } from "./data/networkData";
import "./App.css";

const summaryCards = [
  {
    label: "Active nodes",
    value: "1,248",
    note: "+24 this month",
    icon: Boxes,
    tone: "blue",
  },
  {
    label: "At-risk nodes",
    value: "18",
    note: "6 require attention",
    icon: AlertTriangle,
    tone: "red",
  },
  {
    label: "Active routes",
    value: "386",
    note: "Across 42 countries",
    icon: Route,
    tone: "purple",
  },
  {
    label: "Network health",
    value: "Stable",
    note: "87% operational score",
    icon: Activity,
    tone: "green",
  },
];

const exposureData = [
  { label: "Ports", count: 8, percentage: 86 },
  { label: "Suppliers", count: 5, percentage: 58 },
  { label: "Factories", count: 3, percentage: 35 },
  { label: "Markets", count: 2, percentage: 23 },
];

function App() {
  const [selectedNode, setSelectedNode] = useState(
    () => networkNodes.find((node) => node.id === "port-rotterdam")
  );

  const [searchTerm, setSearchTerm] = useState("");

  const handleSelectNode = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  const matchedNodes = networkNodes.filter((node) => {
    const searchableText =
      `${node.name} ${node.location} ${node.type}`.toLowerCase();

    return searchableText.includes(searchTerm.toLowerCase());
  });

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">
            <Network size={21} />
          </span>

          <span>AtmoGraph</span>
        </div>

        <nav className="navigation" aria-label="Primary navigation">
          <a className="nav-link active" href="#overview">
            <LayoutDashboard size={18} />
            Overview
          </a>

          <a className="nav-link" href="#network">
            <Network size={18} />
            Network
          </a>

          <a className="nav-link" href="#disruptions">
            <AlertTriangle size={18} />
            Disruptions
            <span className="nav-badge">3</span>
          </a>

          <a className="nav-link" href="#exposure">
            <Warehouse size={18} />
            Suppliers
          </a>
        </nav>

        <div className="sidebar-footer">
          <p>
            <span className="status-dot" />
            Systems operational
          </p>

          <small>Static demonstration data</small>
          <small>Week 1 · v0.1.0</small>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <label className="search-box">
            <Search size={17} />

            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search nodes or locations"
              aria-label="Search nodes or locations"
            />
          </label>

          <button className="notification-button" aria-label="Notifications">
            <Bell size={17} />
            <span />
          </button>

          <div className="user-profile">
            <div className="avatar">SC</div>

            <div>
              <strong>Shreyasi</strong>
              <small>Project lead</small>
            </div>
          </div>
        </header>

        <div className="dashboard" id="overview">
          <section className="dashboard-heading">
            <div>
              <span className="eyebrow">Global control tower</span>
              <h1>Supply chain overview</h1>

              <p>
                Monitor the network, identify pressure points and understand
                operational exposure.
              </p>
            </div>

            <div className="live-status">
              <span className="status-dot" />
              Network live · Static Week 1 data
            </div>
          </section>

          <section className="summary-grid" aria-label="Network summary">
            {summaryCards.map((card) => {
              const CardIcon = card.icon;

              return (
                <article className="summary-card" key={card.label}>
                  <div className="summary-card-heading">
                    <span>{card.label}</span>

                    <span className={`summary-icon ${card.tone}`}>
                      <CardIcon size={16} />
                    </span>
                  </div>

                  <strong>{card.value}</strong>
                  <p>{card.note}</p>
                </article>
              );
            })}
          </section>

          <section className="dashboard-grid">
            <article className="panel network-panel" id="network">
              <div className="panel-heading">
                <div>
                  <h2>Global supply network</h2>
                  <p>Select a node to inspect its details</p>
                </div>

                <span className="demo-badge">Static topology</span>
              </div>

              <NetworkGraph
                selectedNode={selectedNode}
                onSelectNode={handleSelectNode}
              />

              <div className="selected-node">
                <span
                  className={`selected-node-marker ${selectedNode.risk}`}
                />

                <div>
                  <small>Selected {selectedNode.type}</small>
                  <strong>{selectedNode.name}</strong>

                  <p>
                    {selectedNode.location} · Capacity:{" "}
                    {selectedNode.capacity}
                  </p>
                </div>

                <span className={`risk-badge ${selectedNode.risk}`}>
                  {selectedNode.risk} risk
                </span>
              </div>
            </article>

            <div className="side-panels">
              <article className="panel disruptions-panel" id="disruptions">
                <div className="panel-heading">
                  <div>
                    <h2>Active disruptions</h2>
                    <p>Signals affecting the sample network</p>
                  </div>

                  <span className="open-badge">3 open</span>
                </div>

                <div className="disruption-list">
                  {disruptions.map((disruption) => (
                    <article
                      className={`disruption-item ${
                        disruption.severity === "Critical"
                          ? "critical"
                          : "warning"
                      }`}
                      key={disruption.id}
                    >
                      <span className="disruption-icon">
                        {disruption.severity === "Critical" ? (
                          <AlertTriangle size={16} />
                        ) : (
                          <Ship size={16} />
                        )}
                      </span>

                      <div>
                        <div className="disruption-meta">
                          <span>{disruption.severity}</span>
                          <time>{disruption.time}</time>
                        </div>

                        <h3>{disruption.title}</h3>
                        <p>{disruption.description}</p>
                        <small>Impact: {disruption.impact}</small>
                      </div>
                    </article>
                  ))}
                </div>
              </article>

              <article className="panel exposure-panel" id="exposure">
                <div className="panel-heading">
                  <div>
                    <h2>Exposure by type</h2>
                    <p>Nodes currently under watch</p>
                  </div>
                </div>

                <div className="exposure-list">
                  {exposureData.map((item) => (
                    <div className="exposure-row" key={item.label}>
                      <span>{item.label}</span>

                      <div className="exposure-track">
                        <span style={{ width: `${item.percentage}%` }} />
                      </div>

                      <strong>{item.count}</strong>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </section>

          {searchTerm && (
            <section className="search-results">
              <strong>
                {matchedNodes.length} matching node
                {matchedNodes.length === 1 ? "" : "s"}
              </strong>

              <div>
                {matchedNodes.map((node) => (
                  <button
                    type="button"
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                  >
                    {node.name}
                    <span>{node.location}</span>
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;