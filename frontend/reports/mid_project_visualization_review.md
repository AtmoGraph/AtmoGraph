# Mid-Project Visualization Validation

## Objective

Demonstrate that the AtmoGraph frontend can render thousands of
interconnected supply-chain nodes without freezing the browser.

## Test environment

- React
- Vite
- D3.js
- HTML Canvas
- Local development server
- Deterministic synthetic graph generator

## Rendering strategy

The original SVG force-directed renderer creates several DOM elements
for every node and relationship. This becomes expensive for large
graphs and causes prolonged force-simulation movement.

The benchmark therefore uses an HTML Canvas renderer for graphs with
100 or more nodes. Nodes use deterministic precomputed positions, so
the graph remains stationary while supporting zooming, panning,
resetting, and node selection.

## Results

| Nodes | Edges | Initial render | Event-loop delay | Graph elements |
|------:|------:|---------------:|-----------------:|---------------:|
| 100 | 189 | 25.9 ms | 5.7 ms | 1 |
| 1,000 | 1,967 | 98.1 ms | 4.3 ms | 1 |
| 2,000 | 3,954 | 46.6 ms | 1.7 ms | 1 |
| 5,000 | 9,928 | 49.0 ms | 1.7 ms | 1 |

Individual browser timing measurements vary because of caching,
JavaScript JIT compilation, system load, and measurement noise.

## Interaction validation

The following interactions were manually verified:

- Zoom in and zoom out
- Canvas panning
- Reset to fitted view
- Node selection
- Rendering without continuous force-simulation movement

Node selection was successfully demonstrated on the 5,000-node graph.

## Conclusion

AtmoGraph successfully rendered a synthetic network containing 5,000
nodes and 9,928 relationships using one Canvas element without
browser freezing. This satisfies the mid-project visualization
validation requirement within the tested local environment.

## Limitations

- The benchmark uses deterministic synthetic graph data.
- Results are single-run browser measurements, not a statistical
  performance study.
- Labels are omitted at the fully zoomed-out scale to avoid visual
  clutter.
- Performance may differ across browsers and hardware.