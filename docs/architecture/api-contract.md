# CodeTwin + ChaosLab + AI — API Contract

> Version: 0.1
> Status: Draft
> Backend: Python + FastAPI
> Frontend: React + TypeScript

---

# 1. Purpose

This document defines the communication contract between the CodeTwin backend and frontend.

The goal is to establish:

- Available API endpoints
- Request formats
- Response formats
- Data models
- Error formats
- Simulation states
- AI analysis structure

The backend and frontend must follow this contract.

---

# 2. Communication

The frontend communicates with the backend using HTTP REST APIs.

Future real-time simulation updates will use WebSockets.

```text
Frontend
   │
   │ HTTP REST
   ▼
FastAPI Backend
   │
   ├── Projects
   ├── Systems
   ├── Experiments
   ├── Simulations
   └── AI

--
# 3. Base URL

Development:

http://localhost:8000

API prefix:

/api

Example:

http://localhost:8000/api/projects

--
# 4. Standard Response Format

Successful responses should return structured JSON.

Example:
{
  "success": true,
  "data": {},
  "error": null
}

For errors:
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found."
  }
}

--
# 5. Project

A project represents a software system being analyzed.

Create Project
POST /api/projects

Request:
{
  "name": "E-Commerce Demo",
  "description": "Demo system for CodeTwin"
}

Response:
{
  "success": true,
  "data": {
    "id": "project-001",
    "name": "E-Commerce Demo",
    "description": "Demo system for CodeTwin",
    "created_at": "2026-08-09T12:00:00Z"
  },
  "error": null
}

--
# 6. List Projects

GET /api/projects

Response:
{
  "success": true,
  "data": [
    {
      "id": "project-001",
      "name": "E-Commerce Demo",
      "description": "Demo system for CodeTwin"
    }
  ],
  "error": null
}

--
# 7. Digital Twin

A Digital Twin represents the architecture of a software system as a graph.

The graph contains:
- Nodes
- Edges

--
# 8. Node Model

A node represents a component of the system.

{
  "id": "orders",
  "name": "Orders Service",
  "type": "service",
  "status": "healthy",
  "impact": 0.0
}

Node types:
- service
- database
- api
- queue
- external

Node statuses:
- healthy
- degraded
- critical
- failed
- recovering

Impact:
Impact is represented as a value between:

0.0 = Healthy
0.25 = Low impact
0.50 = Degraded
0.75 = Critical
1.00 = Failed

--
# 9. Edge Model

An edge represents a dependency between two nodes.

{
  "source": "orders",
  "target": "database",
  "type": "depends_on"
}

Initial edge types:

- depends_on
- communicates_with

--
#10. System Model

A complete Digital Twin system:

{
  "id": "system-001",
  "project_id": "project-001",
  "name": "E-Commerce System",
  "nodes": [
    {
      "id": "api",
      "name": "API Gateway",
      "type": "api",
      "status": "healthy",
      "impact": 0.0
    },
    {
      "id": "orders",
      "name": "Orders Service",
      "type": "service",
      "status": "healthy",
      "impact": 0.0
    },
    {
      "id": "database",
      "name": "Database",
      "type": "database",
      "status": "healthy",
      "impact": 0.0
    }
  ],
  "edges": [
    {
      "source": "api",
      "target": "orders",
      "type": "depends_on"
    },
    {
      "source": "orders",
      "target": "database",
      "type": "depends_on"
    }
  ]
}

--
# 11. Create System
POST /api/systems

Request:
{
  "project_id": "project-001",
  "name": "E-Commerce System"
}

Response:
{
  "success": true,
  "data": {
    "id": "system-001",
    "project_id": "project-001",
    "name": "E-Commerce System",
    "nodes": [],
    "edges": []
  },
  "error": null
}

--
# 12. Get System
GET /api/systems/{system_id}

Response:
{
  "success": true,
  "data": {
    "id": "system-001",
    "project_id": "project-001",
    "name": "E-Commerce System",
    "nodes": [],
    "edges": []
  },
  "error": null
}

--
# 13. Chaos Experiment

An experiment represents a controlled failure scenario.

Example:
{
  "id": "experiment-001",
  "system_id": "system-001",
  "target_node": "database",
  "type": "latency",
  "parameters": {
    "latency_ms": 2000,
    "duration_seconds": 30
  }
}

--
# 14. Experiment Types

Initial supported experiments:

- latency
- service_down
- traffic_spike
- resource_stress

--
#15. Create Experiment
POST /api/experiments

Request:
{
  "system_id": "system-001",
  "target_node": "database",
  "type": "latency",
  "parameters": {
    "latency_ms": 2000,
    "duration_seconds": 30
  }
}

Response:
{
  "success": true,
  "data": {
    "id": "experiment-001",
    "system_id": "system-001",
    "target_node": "database",
    "type": "latency",
    "parameters": {
      "latency_ms": 2000,
      "duration_seconds": 30
    }
  },
  "error": null
}

--
# 16. Run Experiment
POST /api/experiments/{experiment_id}/run

Response:
{
  "success": true,
  "data": {
    "run_id": "run-001",
    "status": "running"
  },
  "error": null
}

--
# 17. Simulation Run

A simulation run represents one execution of a chaos experiment.

Possible states:

- pending
- running
- completed
- failed
- cancelled

Example:
{
  "run_id": "run-001",
  "experiment_id": "experiment-001",
  "status": "completed",
  "duration_seconds": 30
}

--
# 18. Simulation Results
GET /api/runs/{run_id}

Example response:
{
  "success": true,
  "data": {
    "run_id": "run-001",
    "status": "completed",
    "duration_seconds": 30,
    "affected_nodes": [
      {
        "node_id": "database",
        "impact": 1.0
      },
      {
        "node_id": "orders",
        "impact": 0.7
      },
      {
        "node_id": "api",
        "impact": 0.4
      }
    ]
  },
  "error": null
}

--
# 19. Simulation Events

Events describe changes that occurred during a simulation.

Example:
{
  "timestamp": 12.4,
  "node_id": "database",
  "event_type": "latency_increased",
  "severity": 0.8
}

Possible event types:

- latency_increased
- service_failed
- traffic_increased
- resource_degraded
- dependency_degraded
- node_recovered
- simulation_completed

--
20. Get Simulation Events
GET /api/runs/{run_id}/events

Response:
{
  "success": true,
  "data": [
    {
      "timestamp": 12.4,
      "node_id": "database",
      "event_type": "latency_increased",
      "severity": 0.8
    },
    {
      "timestamp": 14.1,
      "node_id": "orders",
      "event_type": "dependency_degraded",
      "severity": 0.6
    }
  ],
  "error": null
}

--
# 21. AI Analysis

The AI Analyzer receives simulation data and produces structured analysis.

Endpoint:

POST /api/ai/analyze/{run_id}

--
# 22. AI Analysis Response

Example:
{
  "success": true,
  "data": {
    "run_id": "run-001",
    "root_cause": "Database latency",
    "severity": "high",
    "affected_components": [
      "database",
      "orders",
      "api"
    ],
    "explanation": "Database latency caused increased response times in the Orders service.",
    "recommendations": [
      "Implement connection pooling",
      "Introduce request timeouts",
      "Consider circuit breaker protection"
    ]
  },
  "error": null
}

--
# 23. AI Severity

The AI may classify severity as:

- low
- medium
- high
- critical

--
24. AI Recommendations

Recommendations should be actionable.

Bad:
Improve the database.

Good:
Introduce connection pooling to reduce database connection overhead.

--
# 25. Before / After Comparison

The system should eventually support comparison between two simulation runs.

Example:
{
  "before": {
    "failure_rate": 0.42,
    "affected_nodes": 4
  },
  "after": {
    "failure_rate": 0.12,
    "affected_nodes": 2
  }
}

This allows the frontend to visualize resilience improvements.

--
# 26. WebSocket

Real-time communication will be introduced after the REST API is functional.

Planned endpoint:

WS /api/runs/{run_id}/stream

Example event:
{
  "timestamp": 12.4,
  "node_id": "database",
  "event_type": "latency_increased",
  "severity": 0.8
}

The frontend will use these events to animate the Digital Twin.

--
# 27. Frontend Responsibilities

The frontend should:

- Display data
- Collect user input
- Call API endpoints
- Display simulation states
- Visualize nodes and edges
- Display events
- Display AI analysis
- Display recommendations

The frontend should NOT:

- Calculate failure propagation
- Execute simulations
- Determine root causes
- Contain database logic
- Contain AI credentials

--
# 28. Backend Responsibilities

The backend should:

- Validate requests
- Manage projects
- Manage Digital Twins
- Execute simulations
- Calculate failure propagation
- Generate events
- Store results
- Communicate with AI services

--
29. AI Responsibilities

The AI should:

- Analyze simulation results
- Identify possible root causes
- Explain system behavior
- Identify risks
- Recommend mitigations

The AI should NOT:

-Directly modify the Digital Twin
-Execute chaos experiments
-Control the simulation engine
-Access frontend code

--
#30. Error Handling

The API should use standard HTTP status codes.

- 200 OK
- 201 Created
- 400 Bad Request
- 404 Not Found
- 422 Validation Error
- 500 Internal Server Error

Example:
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_EXPERIMENT",
    "message": "The selected experiment type is not supported."
  }
}

--
# 31. API Versioning

The initial API version is:

/api

Future versions may use:

/api/v1
/api/v2

Versioning will only be introduced when necessary.

--
# 32. Contract Rules

- Backend responses must follow the documented structure.
- Frontend must not depend on undocumented fields.
- Breaking API changes must be documented.
- New endpoints should be added to this document.
- Data models should remain consistent.
- Core business logic belongs to the backend.
- Visualization logic belongs to the frontend.
- AI analysis belongs to the AI layer.

--
# 33. Development Status

Current status:

- API Contract: Draft
- Backend: Not implemented
- Frontend: Not implemented
- Digital Twin: Not implemented
- ChaosLab: Not implemented
- AI Analyzer: Not implemented
- WebSocket: Planned