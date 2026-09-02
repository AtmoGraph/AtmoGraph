import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
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
import { apiFetch, useAuth } from "./auth";
import "./App.css";
import "./ControlRoom.css";

const exposureData = [
  { label: "Ports", count: 8, percentage: 86 },
  { label: "Suppliers", count: 5, percentage: 58 },
  { label: "Factories", count: 3, percentage: 35 },
  { label: "Markets", count: 2, percentage: 23 },
];

function formatCapacity(value) {
  if (value === undefined || value === null) {
    return "N/A";
  }

  const number = Number(value);

  if (number >= 1_000_000) {
    return `${(number / 1_000_000).toFixed(1)}M`;
  }

  if (number >= 1_000) {
    return `${(number / 1_000).toFixed(1)}K`;
  }

  return String(number);
}

function getDisruptionSeverity(severity) {
  const value = Number(severity);

  if (value >= 0.8) {
    return "Critical";
  }

  if (value >= 0.5) {
    return "Warning";
  }

  return "Watch";
}

function formatDisruptionTime(disruption) {
  if (disruption.status) {
    return disruption.status;
  }

  return "Active";
}

function App() {
  const { user, logout } = useAuth();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [networkNodes, setNetworkNodes] = useState([]);
  const [networkEdges, setNetworkEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [disruptions, setDisruptions] = useState([]);
  const [disruptionsLoading, setDisruptionsLoading] = useState(true);
  const [disruptionsError, setDisruptionsError] = useState("");
  const [predictions, setPredictions] = useState([]);
  const [predictionLoading, setPredictionLoading] = useState(true);
  const [predictionError, setPredictionError] = useState("");
  const [previewHorizon, setPreviewHorizon] = useState(30);
  const [realtimeStatus, setRealtimeStatus] = useState("connecting");
  const [lastRealtimeEvent, setLastRealtimeEvent] = useState(null);
  const [predictionScenario, setPredictionScenario] = useState(null);
  const [livePublishing, setLivePublishing] = useState(false);
  const latestEventId = useRef(0);

  const predictionByNodeId = useMemo(
  () =>
    new Map(
      predictions.map((item) => [
        item.node_id,
        Number(item.prediction),
      ])
    ),
  [predictions]
);

const overlayNetworkNodes = useMemo(
  () =>
    networkNodes.map((node) => {
      const predictionScore = predictionByNodeId.get(
        node.id
      );

      if (!Number.isFinite(predictionScore)) {
        return node;
      }

      let predictionRisk = "low";

      if (predictionScore >= 0.3) {
        predictionRisk = "high";
      } else if (predictionScore >= 0.2) {
        predictionRisk = "medium";
      }

      return {
        ...node,
        predictionScore,
        predictionRisk,
      };
    }),
  [networkNodes, predictionByNodeId]
);

  const activeNodes = networkNodes.length;

  const atRiskNodes = networkNodes.filter((node) => {
    const riskScore = Number(node.properties?.risk_score ?? 0);
    return riskScore >= 0.2;
  }).length;

  const activeRoutes = networkNodes.filter(
    (node) => node.type === "ShippingRoute"
  ).length;

  const networkHealth =
    activeNodes > 0 ? "Operational" : "Unavailable";

  const summaryCards = [
    {
      label: "Active nodes",
      value: activeNodes,
      note: "From Neo4j graph",
      icon: Boxes,
      tone: "blue",
    },
    {
      label: "At-risk nodes",
      value: atRiskNodes,
      note: "Risk Score ≥ 0.20",
      icon: AlertTriangle,
      tone: "red",
    },
    {
      label: "Active routes",
      value: activeRoutes,
      note: "Shipping routes in graph",
      icon: Route,
      tone: "purple",
    },
    {
      label: "Network health",
      value: networkHealth,
      note: `${networkEdges.length} relationships`,
      icon: Activity,
      tone: "green",
    },
  ];

  const loadBackendData = useCallback(async () => {
      try {
        const healthResponse = await apiFetch("/api/health");

        if (!healthResponse.ok) {
          throw new Error("Backend health check failed");
        }

        const graphResponse = await apiFetch("/api/graph");

        if (!graphResponse.ok) {
          throw new Error("Graph API request failed");
        }

        const graphData = await graphResponse.json();

        setNetworkNodes(graphData.nodes || []);
        setNetworkEdges(graphData.edges || []);

        const defaultNode = (graphData.nodes || []).find(
          (node) => node.id === "PORT003"
        );

        setSelectedNode(
          defaultNode || graphData.nodes?.[0] || null
        );
      } catch (error) {
        console.error("Backend connection error:", error);
      }
  }, []);

  const loadDisruptions = useCallback(async () => {
      try {
        setDisruptionsLoading(true);
        setDisruptionsError("");

        const response = await apiFetch("/api/disruptions");

        if (!response.ok) {
          throw new Error("Disruptions API request failed");
        }

        const data = await response.json();

        setDisruptions(data.disruptions || []);
      } catch (error) {
        console.error("Disruptions API error:", error);
        setDisruptionsError("Unable to load disruptions");
        setDisruptions([]);
      } finally {
        setDisruptionsLoading(false);
      }
  }, []);

  const applyPredictionData = useCallback((data) => {
    setPredictions(
      (data.top_impacted_nodes || []).filter(
        (item) => item.node_type !== "Disruption"
      )
    );
    setPredictionScenario(data.scenario || null);
  }, []);

  const loadPredictions = useCallback(async (
    horizonDays,
    scenario = {
      disrupted_port_id: "PORT003",
      disruption_type: "PORT_CLOSURE",
      severity: 0.95,
    }
  ) => {
      try {
        setPredictionLoading(true);
        setPredictionError("");

        const response = await apiFetch(
          "/api/predictions",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              disrupted_port_id: scenario.disrupted_port_id,
              disruption_type: scenario.disruption_type,
              severity: scenario.severity,
              horizon_days: horizonDays,
            }),
          }
        );

        if (!response.ok) {
          throw new Error("Prediction API request failed");
        }

        const data = await response.json();

        applyPredictionData(data);
      } catch (error) {
        console.error("Prediction API error:", error);
        setPredictionError("Unable to load AI predictions");
        setPredictions([]);
      } finally {
        setPredictionLoading(false);
      }
  }, [applyPredictionData]);

  useEffect(() => {
    loadBackendData();
    loadDisruptions();
  }, [loadBackendData, loadDisruptions]);

  useEffect(() => {
    loadPredictions(previewHorizon);
  }, [loadPredictions, previewHorizon]);

  useEffect(() => {
    const controller = new AbortController();
    let reconnectTimer;

    const connect = async () => {
      try {
        setRealtimeStatus("connecting");
        const response = await apiFetch("/api/realtime/events", {
          headers: {
            Accept: "text/event-stream",
            ...(latestEventId.current
              ? { "Last-Event-ID": String(latestEventId.current) }
              : {}),
          },
          signal: controller.signal,
        });

        if (!response.ok || !response.body) {
          throw new Error("Real-time stream unavailable");
        }

        setRealtimeStatus("live");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!controller.signal.aborted) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let boundary = buffer.indexOf("\n\n");
          while (boundary !== -1) {
            const block = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            boundary = buffer.indexOf("\n\n");

            const dataLine = block
              .split("\n")
              .find((line) => line.startsWith("data: "));
            if (!dataLine) continue;

            const event = JSON.parse(dataLine.slice(6));
            latestEventId.current = event.id;
            setLastRealtimeEvent(event.created_at);

            if (event.type === "prediction.updated") {
              const data = event.payload?.prediction;
              if (data?.scenario?.horizon_days === previewHorizon) {
                applyPredictionData(data);
              }
            }

            if (event.type === "disruption.ingested") {
              await Promise.all([
                loadBackendData(),
                loadDisruptions(),
              ]);
              const liveScenario = event.payload?.prediction?.scenario;
              if (liveScenario) {
                await loadPredictions(previewHorizon, liveScenario);
              }
            }
          }
        }

        if (!controller.signal.aborted) {
          throw new Error("Real-time stream ended");
        }
      } catch (error) {
        if (controller.signal.aborted) return;
        console.error("Real-time stream error:", error);
        setRealtimeStatus("reconnecting");
        reconnectTimer = window.setTimeout(connect, 3000);
      }
    };

    connect();
    return () => {
      controller.abort();
      window.clearTimeout(reconnectTimer);
    };
  }, [
    applyPredictionData,
    loadBackendData,
    loadDisruptions,
    loadPredictions,
    previewHorizon,
  ]);

  const publishLiveScenario = async () => {
    try {
      setLivePublishing(true);
      setPredictionError("");
      const response = await apiFetch("/api/realtime/scenarios", {
        method: "POST",
        body: JSON.stringify({
          disrupted_port_id: "PORT003",
          disruption_type: "PORT_CLOSURE",
          severity: 0.95,
          horizon_days: previewHorizon,
        }),
      });
      if (!response.ok) {
        throw new Error("Could not publish live scenario");
      }
    } catch (error) {
      console.error("Live scenario error:", error);
      setPredictionError("Unable to publish live scenario");
    } finally {
      setLivePublishing(false);
    }
  };

  const handleSelectNode = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  const matchedNodes = networkNodes.filter((node) => {
    const searchableText = [
      node.name,
      node.properties?.country,
      node.properties?.region,
      node.type,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

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
            <span className="nav-badge">
              {disruptions.length}
            </span>
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

          <small>Real-time: {realtimeStatus}</small>
          <small>
            {lastRealtimeEvent
              ? `Last event ${new Date(lastRealtimeEvent).toLocaleTimeString()}`
              : "Waiting for live events"}
          </small>
          <small>AtmoGraph  v0.1.0</small>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="control-room-title">
            <span className="status-dot" />
            <div>
              <strong>Operational control room</strong>
            </div>
          </div>

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

          <div className="timeline-control" aria-label="Prediction horizon preview">
            <div className="timeline-control-heading">
              <span>Timeline</span>
              <small>Projection</small>
            </div>

            <div className="timeline-options">
              {[30, 60, 90].map((days) => (
                <button
                  type="button"
                  className={previewHorizon === days ? "active" : ""}
                  key={days}
                  onClick={() => setPreviewHorizon(days)}
                  aria-pressed={previewHorizon === days}
                >
                  {days}d
                </button>
              ))}
            </div>
          </div>

          <div className="account-menu-wrap">
            <button className="user-profile account-button" type="button" onClick={() => setAccountMenuOpen((open) => !open)} aria-expanded={accountMenuOpen} aria-haspopup="menu">
              <div className="avatar">{user.name.slice(0, 2).toUpperCase()}</div>

              <div>
                <strong>{user.name}</strong>
                <small>{user.email}</small>
              </div>
            </button>

            {accountMenuOpen && (
              <div className="account-menu" role="menu">
                <div className="account-menu-user">
                  <strong>{user.name}</strong>
                  <span>{user.email}</span>
                </div>
                <button type="button" role="menuitem" onClick={logout}>Log out</button>
              </div>
            )}
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

          <section
            className="dashboard-grid control-room-grid"
            data-preview-horizon={previewHorizon}
          >
            <article className="panel network-panel" id="network">
              <div className="panel-heading">
                <div>
                  <h2>Global supply network</h2>
                  <p>
                    {networkNodes.length} nodes · {networkEdges.length}{" "}
                    relationships
                  </p>
                </div>

                <span className="demo-badge">Neo4j live data</span>
              </div>

              <NetworkGraph
                selectedNode={selectedNode}
                onSelectNode={handleSelectNode}
                networkNodes={overlayNetworkNodes}
                networkEdges={networkEdges}
              />

              <div className="supplier-details-panel">
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Node details</span>
                    <h2>
                      {selectedNode?.type === "Supplier"
                        ? "Supplier Details"
                        : `${selectedNode?.type || "Node"} Details`}
                    </h2>
                  </div>

                  {selectedNode && (
  <span
    className={`risk-badge ${
      selectedNode.predictionRisk ||
      selectedNode.properties?.risk ||
      selectedNode.risk ||
      "low"
    }`}
  >
    {Number.isFinite(selectedNode.predictionScore)
      ? "ML "
      : ""}
    {selectedNode.predictionRisk ||
      selectedNode.properties?.risk ||
      selectedNode.risk ||
      "unknown"}{" "}
    risk
  </span>
)}
                </div>

                {selectedNode ? (
                  <div className="details-grid">
                    <div className="detail-item">
                      <span>Name</span>
                      <strong>{selectedNode.name || "N/A"}</strong>
                    </div>

                    <div className="detail-item">
                      <span>Node Type</span>
                      <strong>{selectedNode.type || "N/A"}</strong>
                    </div>

                    <div className="detail-item">
                      <span>Node ID</span>
                      <strong>{selectedNode.id || "N/A"}</strong>
                    </div>

                    <div className="detail-item">
                      <span>Country</span>
                      <strong>
                        {selectedNode.properties?.country ||
                          selectedNode.properties?.region ||
                          "N/A"}
                      </strong>
                    </div>

                    <div className="detail-item">
  <span>Risk Score</span>
  <strong>
    {selectedNode.properties?.risk_score ?? "N/A"}
  </strong>
</div>

{Number.isFinite(selectedNode.predictionScore) && (
  <div className="detail-item">
    <span>ML Impact</span>
    <strong>
      {(selectedNode.predictionScore * 100).toFixed(2)}%
    </strong>
  </div>
)}

<div className="detail-item">
  <span>Capacity</span>
  <strong>
    {formatCapacity(selectedNode.properties?.capacity)}
  </strong>
</div>
                  </div>
                ) : (
                  <div className="empty-details">
                    Click a node in the graph to view details.
                  </div>
                )}
              </div>
            </article>

            <div className="side-panels">
              <article className="panel disruptions-panel" id="disruptions">
                <div className="panel-heading">
                  <div>
                    <h2>Active disruptions</h2>
                    <p>Live signals from Neo4j</p>
                  </div>

                  <span className="open-badge">
                    {disruptions.length} open
                  </span>
                </div>

                <div className="disruption-list">
                  {disruptionsLoading && (
                    <p>Loading disruptions...</p>
                  )}

                  {!disruptionsLoading && disruptionsError && (
                    <p>{disruptionsError}</p>
                  )}

                  {!disruptionsLoading &&
                    !disruptionsError &&
                    disruptions.length === 0 && (
                      <p>No active disruptions.</p>
                    )}

                  {!disruptionsLoading &&
                    !disruptionsError &&
                    disruptions.map((disruption) => {
                      const severity = getDisruptionSeverity(
                        disruption.severity
                      );

                      return (
                        <article
                          className={`disruption-item ${severity === "Critical"
                              ? "critical"
                              : "warning"
                            }`}
                          key={disruption.id}
                        >
                          <span className="disruption-icon">
                            {severity === "Critical" ? (
                              <AlertTriangle size={16} />
                            ) : (
                              <Ship size={16} />
                            )}
                          </span>

                          <div>
                            <div className="disruption-meta">
                              <span>{severity}</span>
                              <time>
                                {formatDisruptionTime(disruption)}
                              </time>
                            </div>

                            <h3>{disruption.name}</h3>

                            <p>
                              {disruption.type?.replaceAll("_", " ")}
                              {" · "}
                              {disruption.port_name}
                            </p>

                            <small>
                              Expected delay:{" "}
                              {disruption.expected_delay_days ?? "N/A"}{" "}
                              days
                            </small>
                          </div>
                        </article>
                      );
                    })}
                </div>
              </article>

              <article className="panel prediction-panel" id="predictions">
                <div className="panel-heading">
                  <div>
                    <h2>AI impact prediction</h2>
                    <p>
                      GNN projection · {previewHorizon}-day horizon
                    </p>
                  </div>

                  <div className="prediction-live-actions">
                    <span className={`stream-badge ${realtimeStatus}`}>
                      <span />
                      {realtimeStatus}
                    </span>
                    <button
                      className="live-action"
                      type="button"
                      onClick={publishLiveScenario}
                      disabled={livePublishing || realtimeStatus !== "live"}
                    >
                      {livePublishing ? "Publishing…" : "Simulate live"}
                    </button>
                  </div>
                </div>

                <div className="prediction-scenario">
                  <div className="prediction-scenario-main">
                    <span className="prediction-eyebrow">Scenario</span>
                    <strong>
                      {predictionScenario?.disrupted_port_id || "PORT003"}
                      {" · Rotterdam Port"}
                    </strong>
                  </div>

                  <span className="prediction-severity">
                    <span>Severity</span>
                    {Math.round(
                      Number(predictionScenario?.severity ?? 0.95) * 100
                    )}%
                  </span>
                </div>

                <div className="prediction-list">
                  {predictionLoading && (
                    <div className="prediction-state">
                      <span className="prediction-state-dot" />
                      Loading AI predictions...
                    </div>
                  )}

                  {!predictionLoading && predictionError && (
                    <div className="prediction-state prediction-state-error">
                      {predictionError}
                    </div>
                  )}

                  {!predictionLoading &&
                    !predictionError &&
                    predictions.slice(0, 6).map((item, index) => {
                      const percentage = Math.min(
                        100,
                        Math.max(0, Number(item.prediction) * 100)
                      );

                      return (
                        <div
                          className="prediction-row"
                          key={item.node_id}
                        >
                          <div className="prediction-rank">
                            {String(index + 1).padStart(2, "0")}
                          </div>

                          <div className="prediction-info">
                            <strong>{item.node_name}</strong>
                            <small>{item.node_type}</small>

                            <div className="prediction-progress">
                              <span style={{ width: `${percentage}%` }} />
                            </div>
                          </div>

                          <div className="prediction-score">
                            <strong>{percentage.toFixed(2)}%</strong>
                            <small>impact</small>
                          </div>
                        </div>
                      );
                    })}

                  {!predictionLoading &&
                    !predictionError &&
                    predictions.length === 0 && (
                      <div className="prediction-state">
                        No predictions available.
                      </div>
                    )}
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
                        <span
                          style={{
                            width: `${item.percentage}%`,
                          }}
                        />
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
                    <span>
                      {node.properties?.country ||
                        node.properties?.region ||
                        "Unknown"}
                    </span>
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
