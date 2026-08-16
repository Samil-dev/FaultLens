# FaultLens

**AI-Powered Chaos Engineering & Resilience Intelligence**

FaultLens is a platform for simulating failures in distributed systems, understanding how they propagate, and using AI to explain the results — before those failures happen in production.

FaultLens combines:

- Digital Twins
- Chaos Engineering
- Failure Simulation
- Resilience Analysis
- System Dependency Analysis
- Metrics
- AI-Powered Insights
- Risk Assessment
- Recovery Analysis

## How it works

A system is modeled as a **Digital Twin**: services as nodes, dependencies as edges. A **chaos experiment** injects a controlled failure into one node — a service outage, a latency spike, resource exhaustion, or a traffic spike. The simulation engine propagates that failure through the dependency graph, and the resilience engine turns the result into a blast radius, a resilience score, a risk level, and a set of recovery metrics. An AI layer interprets that data into a root cause, a risk explanation, and concrete recommendations.

## Project Structure

```
FaultLens/
├── Backend/     FastAPI service — digital twin, chaos engine, resilience analysis, AI pipeline
└── Frontend/    React + TypeScript dashboard — Digital Twin graph, experiment controls, resilience panel
```

## Running locally

**Backend**

```
cd Backend
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**Frontend**

```
cd Frontend
npm run dev
```

Then open `http://localhost:3000`.

On Windows, `start.bat` in the repository root launches both and opens the dashboard automatically.
