# CodeTwin + ChaosLab + AI - Architecture Overview.

> Version: 0.1 
> Status: In Development
> Project Type: Hackathon
> Team: Alam Garcia and Elias Novas

---
## 1. Project Overview

CodeTwin + ChaosLab + IA is an experimental platform that combines:

- Digital Twins
- Chaos Engineering
- System Simulation
- Graph-based dependency analysis
- Artificial Intelligence

The platform creates a digital representation of a software system and allows users to run controlled failure experiments against that representaion.

The system then analyzes how the failure propagates through the architecture and uses AI to identify possible root causes, evaluate impact, and recommend strategies.

## Core concept

Understand the system
        ↓
Create its Digital Twing
        ↓
Introduce controlled failures
        ↓
Simulate the consequences
        ↓
Analyze failure propagation
        ↓
Use AI to explain the results
        ↓
Recommend improvements
        ↓
Run the experiment again
        ↓
Compare BEFORE vs AFTER

--
## 2. Main Objective

The main objective of CodeTwin is to provide a visual and intelligent environment where developeres can understand how their system behave under failure conditions.

The platform should answer questions such as:

- What happens if this service fails?
- Which components are affected?
- How does a failure propagate?
- What is the most likely root cause?
- Which component represents the highest risk?
- How could the system be improved?
- Does the system become more resilient after applying a mitigation?

--
## 3. Core Components.

The system is divided into five main components:

┌─────────────────────┐
│      Frontend       │
│   React + TypeScript│
└──────────┬──────────┘
           │
       REST / WS
           │
           ▼
┌─────────────────────┐
│       Backend       │
│   Python + FastAPI  │
└──────────┬──────────┘
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
 CodeTwin ChaosLab AI
 Engine   Engine Analyzer
     │     │     │
     └─────┼─────┘
           ▼
      Simulation
        Engine
           │
           ▼
        Database

--
## 4. Frontend

The frontend is responsible for the user experience and visualization of the system.

Main responsibilities:
- Dashboard
- Digital Twin visualization
- System graph visualization
- Experiment configuration
- Simulation visualization
- Real-time events
- Simulation replay
- AI analysis visualization
- Before/After comparison

Technologies:
- React
- TypeScript
- Vite
- React Flow
- Tailwind CSS
- Owner

Elias — Frontend Lead

--
## 5. Backend

The backend contains the main application logic.

Main responsibilities:
- API
- Project management
- Digital Twin management
- Chaos experiments
- Simulation execution
- Failure propagation
- Event generation
- AI integration
- Database communication

Technologies:
- Python
- FastAPI
- Pydantic
- SQLite for initial development
- PostgreSQL as a future production option
- Owner

Samil — Backend/Core Lead

--
## 6. CodeTwin Engine

The CodeTwin Engine is responsible for representing a software system as a Dygital Twin.

A Digital Twin is represented as a graph containing:

- Nodes
- Edges
- Properties
- Health states
- Dependencies

Example:

API Gateway
     │
     ▼
Orders Service
     │
     ▼
Database

Internally, the system represents this as structured data.

Node
{
  "id": "orders",
  "name": "Orders Service",
  "type": "service",
  "status": "healthy"
}


Edge
{
  "source": "orders",
  "target": "database",
  "type": "depends_on"
}

Initial node types:
- service
- database
- api
- queue
- external

--
## 7. ChaosLab Engine

ChaosLab is responsible for creating controlled failure scenarios.

The initial version will support a limited number of experiment types.

Initial experiments:

Latency
Introduces artificial latency into a component.

latency_ms: 2000

Service Failure
Simulates a service becoming unavailable.

service_down: true

Traffic Spike
Simulates a sudden increase in requests.

requests_multiplier: 5

Resource Stress
Simulates resource degradation.

resource_level: 0.8

The initial implementation will be simulated rather than attacking real infrastructure.

--
## 8. Simulation Engine

The Simulation Engine executes experiments against the Digital Twin.

Example:

Experiment
    │
    ▼
Target: Database
    │
    ▼
Failure Injection
    │
    ▼
System State Changes
    │
    ▼
Propagation Analysis
    │
    ▼
Simulation Results

The simulation must be deterministic whenever possible.

The AI should not control the simulation.

The simulation engine determines what happens.

The AI analyzes what happened.

--
## 9. Failure Propagation

Failure propagation is based on the dependency graph.

Example:

API
 │
 ▼
Orders
 │
 ▼
Database


If the database fails:

Database  🔴 1.0
    ↑
Orders    🟠 0.7
    ↑
API       🟡 0.4


The system assigns an impact value between:

0.0 = Healthy
0.25 = Low impact
0.50 = Degraded
0.75 = Critical
1.00 = Failed

The propagation engine calculates the impact based on system dependencies.

--
## 10. Event System

During a simulation, the backend generates events.

Example:
{
  "timestamp": 12.4,
  "node_id": "database",
  "event_type": "latency_increased",
  "severity": 0.8
}

Events can later be used for:

- Real-time visualization
- Simulation replay
- Timeline visualization
- AI analysis
- Experiment reports

--
## 11. AI Analyzer

The AI Analyzer is responsible for analyzing simulation results.

The AI receives structured information about:

- System topology
- Experiment configuration
- Simulation events
- Affected components
- Impact levels
- System behavior

The AI produces structured analysis.

Expected output
{
  "root_cause": "Database latency",
  "severity": "high",
  "affected_components": [
    "database",
    "orders",
    "api"
  ],
  "explanation": "Database latency caused request delays...",
  "recommendations": [
    "Implement connection pooling",
    "Introduce request timeouts",
    "Add circuit breaker protection"
  ]
}

The AI should explain the simulation results rather than control the simulation itself.

--
## 12. Database

The initial version will use SQLite to simplify development.

The system is expected to contain the following logical entities:

Project
System
Node
Edge
Experiment
Simulation Run
Event
AI Analysis

Relationships:

Project
   │
   ▼
System
   │
   ├── Nodes
   ├── Edges
   │
   └── Experiments
          │
          ▼
     Simulation Run
          │
          ├── Events
          │
          └── AI Analysis

PostgreSQL may be introduced later if required.

--
## 13. Communication

The frontend and backend communicate through APIs.

REST

REST will be used for:

Creating projects
Retrieving systems
Creating experiments
Starting simulations
Retrieving results
Requesting AI analysis

WebSocket

WebSocket will be introduced after the basic REST communication works.

It will be used for:

Real-time simulation events
Live system state
Simulation progress
Replay data

--
## 14. API Philosophy

The backend must return structured data.

The frontend is responsible for presentation.

The AI is responsible for analysis.

The responsibilities should remain separated.

Backend
   ↓
Structured Data
   ↓
Frontend
   ↓
Visualization

The frontend should not contain core simulation logic.

The AI should not directly control the frontend.

The simulation engine should not depend on AI decisions.

--
## 15. MVP

The Minimum Viable Product will contain:

 - Create project
 - Create Digital Twin
 - Display system graph
 - Create chaos experiment
 - Execute simulation
 - Calculate failure propagation
 - Generate simulation events
 - Display simulation results
 - AI root-cause analysis
 - AI recommendations
 - Before/After comparison

The MVP should demonstrate the complete product loop:

Digital Twin
     ↓
Chaos Experiment
     ↓
Simulation
     ↓
Failure Propagation
     ↓
AI Analysis
     ↓
Recommendation
     ↓
Re-run
     ↓
Before vs After

--
## 16. Team Responsibilities
Alam Garcia
Core / Backend / AI Lead

Responsible for:

Python
FastAPI
CodeTwin Engine
ChaosLab Engine
Simulation Engine
Failure Propagation
Database
AI Analyzer
Backend testing

Elias Novas
Frontend / UX Lead

Responsible for:

React
TypeScript
Dashboard
Digital Twin visualization
Experiment interface
Simulation interface
Real-time visualization
Replay
AI results interface
UI/UX

--
## 17. Development Philosophy

The team is composed of developers who are still learning how to build large-scale software projects.

This is not considered a limitation.

The project will be developed using an incremental approach.

Learn
  ↓
Build a small version
  ↓
Test
  ↓
Understand
  ↓
Improve
  ↓
Integrate

Complex technologies should only be introduced when they solve an actual problem.

The project should prioritize:

Functionality
Understanding
Stability
Architecture
Visual quality
Advanced features

--
## 18. Development Principles

Keep it simple
Do not introduce unnecessary infrastructure.

Build incrementally
Every feature should have a small working version before being expanded.

Separate responsibilities
Frontend, backend, simulation and AI should remain independent.

Document important decisions
Important architectural decisions should be documented.

Test before integrating
Features should be tested before merging into the main development branch.

Learn while building
Documentation and AI tools may be used as learning and development assistants.

Do not blindly copy AI-generated code
Every important piece of generated code must be understood by at least one team member before becoming part of the core system.

--
## 19. Git Strategy

The repository uses:

main
  │
  ▼
develop
  │
  ├── samil/*
  │
  └── elias/*

main
Stable version intended for demonstrations and releases.

develop
Integration branch for completed features.

Feature branches
Used for individual features.

Examples:

alam/codetwin
alam/chaoslab
alam/simulation
alam/ai

elias/dashboard
elias/twin-view
elias/experiments
elias/replay

Features should be merged into develop before reaching main.

## 20. Current Development Phase

Current phase:
Architecture and Project Setup

Next objectives:

- Create repository documentation.
- Configure Git workflow.
- Create backend skeleton.
- Create frontend skeleton.
- Implement first API endpoint.
- Connect frontend to backend.
- Implement the first Digital Twin model.

--
## 21. Long-Term Vision

The long-term vision is to evolve CodeTwin into an intelligent resilience platform capable of:

- Automatically discovering system architectures
- Creating Digital Twins from real projects
- Running advanced chaos experiments
- Predicting failure propagation
- Identifying critical dependencies
- Providing AI-powered root-cause analysis
- Recommending resilience improvements
- Comparing system resilience before and after changes

The hackathon MVP will focus on proving the core concept rather than implementing the entire long-term vision.