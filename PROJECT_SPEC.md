# Roller Coaster Simulator Project Specification

## 1. Project Overview

### 1.1 Purpose

This project is a professional roller coaster simulation platform for ride development, engineering analysis, and operational logic testing.

The system shall support:

1. 3D visualization of coaster tracks and animated trains or ride vehicles moving along the track.
2. Physics-based simulation of speed, acceleration, train movement, and equipment effects using a Python backend.
3. Interactive editing of tracks, trains, equipment, and ride control logic.
4. Multi-station, multi-train, branched track layouts including maintenance bay routing.
5. A ride control system supporting both visual rules and Python scripting.

### 1.2 Primary Users

1. Ride development engineers
2. Mechanical and systems engineers
3. Controls engineers
4. Ride designers and layout planners
5. Operators or analysts testing dispatch and routing logic

### 1.3 Product Goals

1. Allow engineers to model realistic coaster layouts from 3D track coordinates.
2. Let users define train composition, loading conditions, and operational devices.
3. Simulate physical behavior with sufficient realism for engineering iteration.
4. Simulate ride operations with multiple trains, blocks, switches, and stations.
5. Provide a visual and editable environment for ride control logic.
6. Persist the full project in a reusable file format.

## 2. Frozen Requirements

The following requirements are fixed for Version 1:

1. Bank angle is part of the input data and remains editable.
2. Pneumatic brakes must support both fail-safe modes.
3. Launch and brake devices are modeled using force curves rather than target-speed shortcuts.
4. Ride control must support both visual rule configuration and Python scripting.
5. Multiple stations, maintenance branches, and switched track routing are required in the first release.

## 3. Recommended Technology Stack

### 3.1 Backend

1. `Python 3.12+`
2. `FastAPI` for API and WebSocket services
3. `Pydantic` for schemas and validation
4. `NumPy` for vectorized numerical calculations
5. `SciPy` for interpolation and numerical methods
6. `Numba` for optimizing heavy simulation loops
7. `NetworkX` for track topology and routing graph logic
8. `PostgreSQL` for persistent storage

### 3.2 Frontend

1. `React`
2. `TypeScript`
3. `Three.js`
4. `react-three-fiber`
5. `Mantine` for UI components
6. `Plotly` for engineering plots and analysis panels
7. `Monaco Editor` for Python control scripting
8. `Zustand` for frontend state management

### 3.3 Data and Transport

1. REST endpoints for project CRUD and configuration
2. WebSockets for simulation playback, live telemetry, and control-state updates
3. JSON-based project file format with future export/import compatibility

## 4. High-Level System Architecture

The application shall be divided into the following major subsystems:

1. Track Geometry Engine
2. Track Topology and Routing Engine
3. Train and Vehicle Model
4. Equipment Model
5. Physics Simulation Engine
6. Ride Control System
7. Project Persistence Layer
8. 3D Visualization and Editing UI
9. Analysis and Reporting Layer

### 4.1 Architectural Principle

The simulator should use a constrained-motion model as the initial engineering foundation.

This means:

1. Trains follow the track centerline rather than full unconstrained rigid-body spatial dynamics.
2. Motion is parameterized by distance along the track, typically denoted by `s`.
3. Forces are applied primarily along the local track tangent.
4. Curvature, slope, and bank angle are used to calculate engineering outputs such as tangential acceleration, lateral acceleration, and normal acceleration.

This approach balances realism, maintainability, and development speed.

## 5. Engineering Scope and Modeling Assumptions

### 5.1 Included in Version 1

1. Gravity effects along sloped track
2. Rolling resistance
3. Aerodynamic drag
4. Equipment-driven propulsion and braking
5. Loaded and unloaded train mass cases
6. Multi-car train occupancy across multiple track sections
7. Curvature-based acceleration and g-force outputs
8. Multiple trains on a branched track network
9. Block logic, switch routing, and multi-station operations

### 5.2 Explicitly Out of Scope for Version 1

1. Full rigid-body multibody bogie dynamics
2. Wheel-rail contact mechanics at detailed mechanical resolution
3. Finite element structural analysis of the track
4. Advanced passenger biomechanical modeling
5. Electrical power system simulation of motors and drives in full detail

### 5.3 Core Assumptions

1. The train follows the centerline of the track.
2. Track geometry is represented by smooth spline-based paths.
3. Bank angle is defined at input points and interpolated between them.
4. Equipment forces act along the path tangent unless otherwise specified.
5. Switches can only change alignment when their controlled region is unoccupied.
6. Stations, hold zones, launch zones, brake zones, and maintenance zones are operational designations layered on top of track geometry.

## 6. Domain Terminology

### 6.1 Track Geometry Terms

1. `Point`: An input control point containing `x`, `y`, `z`, and `bank_deg`.
2. `Path`: A continuous spline-based section of track geometry.
3. `Arc length`: Distance measured along the track centerline.
4. `Curvature`: Rate at which the track direction changes with distance.
5. `Slope`: Rate of change in elevation with respect to arc length.
6. `Bank angle`: Rotation of the local track frame around the tangent axis.

### 6.2 Operational Terms

1. `Section`: A user-defined operational segment of track.
2. `Zone`: A type assigned to a section such as load, unload, launch, brake, hold, free, or maintenance.
3. `Block`: A safety or routing occupancy region.
4. `Station`: A defined area for loading, unloading, transfer, or holding.
5. `Route`: The selected downstream path through the topology graph.
6. `Switch`: A controllable routing element changing the downstream path.

### 6.3 Train Position Terms

1. `Train front`: The foremost point of the train along its route.
2. `Train rear`: The rearmost point of the train along its route.
3. `Vehicle interval`: The occupied span of each ride vehicle along the track.
4. `Occupied interval`: The total path distance range covered by the train.

## 7. Functional Requirements

### 7.1 Track Input and Editing

The system shall:

1. Accept track geometry as lists of 3D points with bank angle.
2. Allow users to create multiple connected paths rather than a single loop only.
3. Support editing operations:
   1. Add point
   2. Delete point
   3. Move point
   4. Adjust bank angle
   5. Split path
   6. Merge path
4. Support assignment of section types and operational zones.
5. Validate geometric continuity and path connectivity.

### 7.2 Train and Vehicle Definition

The system shall:

1. Support a train composed of multiple ride vehicles.
2. Allow users to specify:
   1. Vehicle length
   2. Vehicle dry mass
   3. Capacity
   4. Passenger mass assumptions
3. Support at least loaded and unloaded operating conditions.
4. Compute total train length and total train mass automatically from vehicle composition.

### 7.3 Track Equipment

The system shall allow users to place, edit, and remove:

1. LSM launch systems
2. Lift systems
3. Pneumatic brakes
4. Trim brakes
5. Boosters
6. Track switches

### 7.4 Multi-Train Operation

The system shall:

1. Support multiple trains on the same ride network.
2. Support multiple stations.
3. Support branches to maintenance bay or alternate routing.
4. Enforce occupancy and routing constraints.
5. Track block states and train positions continuously.

### 7.5 Ride Control System

The system shall:

1. Provide a visual rule configuration interface.
2. Provide Python scripting for advanced control logic.
3. Expose train positions, timers, equipment states, block occupancy, and switch states to the control layer.
4. Support command outputs such as:
   1. Dispatch permit
   2. Brake activation
   3. Launch enable
   4. Booster drive or brake commands
   5. Switch alignment
5. Enforce safety interlocks independent of user-authored logic.

### 7.6 Visualization

The system shall:

1. Render track geometry in 3D.
2. Animate trains moving along the track.
3. Show equipment placement visually.
4. Show operational sections with distinct visual coding.
5. Provide engineering plots of speed, acceleration, and related outputs.

### 7.7 Persistence

The system shall:

1. Save a project configuration.
2. Reload a project without loss of geometry, logic, topology, or equipment metadata.
3. Store all relevant engineering and operational settings in a structured schema.

## 8. Track Geometry Model

### 8.1 Input Point Schema

Each editable geometry point shall contain:

```json
{
  "id": "pt_001",
  "x": 0.0,
  "y": 0.0,
  "z": 0.0,
  "bank_deg": 0.0,
  "editable": true
}
```

### 8.2 Coordinate System

Recommended default convention:

1. Units: meters
2. Time: seconds
3. Mass: kilograms
4. Force: newtons
5. Speed: meters per second
6. Angle: degrees in UI, radians internally as needed

Recommended axis convention:

1. `x`: horizontal axis
2. `y`: horizontal axis orthogonal to `x`
3. `z`: elevation axis

This convention should be fixed across backend, frontend, and persisted data.

### 8.3 Geometry Representation

Each path shall be represented as:

1. Raw editable points
2. Interpolated spline centerline
3. Interpolated bank profile
4. Derived arc length parameterization
5. Derived local frames:
   1. tangent
   2. normal
   3. binormal

### 8.4 Derived Quantities

For each sampled location along a path, the system should compute:

1. Position
2. Tangent vector
3. Local bank angle
4. Slope angle
5. Curvature
6. Radius of curvature where applicable
7. Local frame basis for vehicle orientation and g-force analysis

### 8.5 Geometry Quality Validation

The system should detect and warn about:

1. Sharp curvature spikes
2. Non-smooth banking transitions
3. Discontinuous path tangents
4. Invalid path joins
5. Self-intersection risk, optionally as a warning

## 9. Track Topology and Routing Model

### 9.1 Core Concept

The ride layout shall be modeled as a directed graph.

### 9.2 Graph Elements

1. `TrackPath`
   1. A continuous geometric path
   2. Has a spline, sampled length, and endpoints

2. `Junction`
   1. A topological connection between paths
   2. May be passive or controlled

3. `Switch`
   1. A controlled junction with one active outgoing route
   2. Has occupancy constraints and actuation time

4. `Block`
   1. A safety or operational occupancy region
   2. Used for dispatch and routing logic

5. `Station`
   1. A named operational region used for load, unload, hold, transfer, or dispatch

### 9.3 Routing Rules

The system shall:

1. Maintain a selected route for each train.
2. Prevent invalid switch alignment changes while the switch zone is occupied.
3. Associate each train with a current and future route across the graph.
4. Support routing to:
   1. Mainline
   2. Additional station
   3. Maintenance bay
   4. Storage or bypass path if later added

## 10. Section and Zone Model

Before equipment placement, users shall define operational sections.

### 10.1 Required Zone Types

1. `load`
2. `unload`
3. `launch`
4. `brake`
5. `hold`
6. `free`
7. `maintenance`

### 10.2 Section Metadata

Each section shall contain:

1. Unique identifier
2. Parent path identifier
3. Start distance on path
4. End distance on path
5. Zone type
6. User label
7. Equipment placement constraints

### 10.3 Section Validation

The system should validate:

1. No illegal overlaps for mutually exclusive zone types
2. Equipment placement compatibility with the section type
3. Section extents are within path bounds

## 11. Train and Vehicle Model

### 11.1 Vehicle Schema

Each vehicle should define:

1. `id`
2. `length_m`
3. `dry_mass_kg`
4. `capacity`
5. `passenger_mass_per_person_kg`
6. Optional metadata such as vehicle type or bogie spacing

### 11.2 Train Schema

Each train should define:

1. `id`
2. Ordered list of vehicles
3. Coupling gaps, if modeled
4. Route assignment
5. Current state
6. Load case

### 11.3 Derived Train Properties

The simulator should compute:

1. Total train length
2. Total dry mass
3. Total loaded mass
4. Occupied intervals on the track
5. Vehicle-by-vehicle location spans

### 11.4 Load Cases

At minimum, support:

1. Empty train
2. Fully loaded train
3. Custom occupancy factor, if practical for Version 1

## 12. Equipment Definitions and Simulation Model

Each equipment type must have:

1. Placement metadata
2. Parameter schema
3. Control state
4. Force or routing behavior
5. Placement rules and validation logic

### 12.1 LSM Launch System

#### Purpose

Actively accelerate the train along a launch section.

#### Model

The launch applies a controllable longitudinal force along the track tangent.

#### Required Parameters

1. `id`
2. `path_id`
3. `start_s`
4. `end_s`
5. `stator_count`
6. `magnetic_field_strength`
7. `max_force_n`
8. `force_curve`
9. `enabled`

#### Recommended Force Curve Inputs

The force curve may depend on:

1. Local distance within the launch
2. Train speed
3. Enable or control state

Example conceptual interface:

```text
F_launch = f(local_s, v, control_state)
```

#### Placement Rules

1. Prefer straight or near-straight sections
2. Should be restricted by configurable curvature limits
3. Should only be placeable in appropriate launch or free zones according to project rules

### 12.2 Lift System

#### Purpose

Pull the train uphill to a release point.

#### Model

The lift is a constrained engagement device with a nominal lift speed and a maximum pull force.

#### Required Parameters

1. `id`
2. `path_id`
3. `start_s`
4. `end_s`
5. `lift_speed_mps`
6. `max_pull_force_n`
7. `engagement_point_s`
8. `release_point_s`
9. `enabled`

#### Placement Rules

1. Should be on a straight or nearly straight sloped segment
2. Must be compatible with lift or designated uphill zones

### 12.3 Pneumatic Brake

#### Purpose

Provide strong deceleration or stopping capability in normal or emergency conditions.

#### Model

A controllable braking force curve with explicit fail-safe behavior.

#### Required Parameters

1. `id`
2. `path_id`
3. `start_s`
4. `end_s`
5. `max_brake_force_n`
6. `response_time_s`
7. `air_pressure`
8. `fail_safe_mode`
9. `force_curve`
10. `state`

#### Allowed Fail-Safe Modes

1. `normally_open`
2. `normally_closed`

#### State Examples

1. `open`
2. `closed`
3. `emergency_stop`

### 12.4 Trim Brake

#### Purpose

Reduce train speed without necessarily bringing the train to a full stop.

#### Model

A controlled speed-trim braking force over a defined interval.

#### Required Parameters

1. `id`
2. `path_id`
3. `start_s`
4. `end_s`
5. `max_trim_force_n`
6. `force_curve`
7. `enabled`

#### Intended Use

1. Mid-course speed adjustment
2. Section-to-section speed control
3. Scenario testing for variable braking intensity

### 12.5 Booster

#### Purpose

Drive the train at low speed in station, hold, maintenance, transfer, or similar zones.

#### Model

A tire-driven propulsion device that may also apply resistive braking when motor braking is active.

#### Required Parameters

1. `id`
2. `path_id`
3. `start_s`
4. `end_s`
5. `wheel_count`
6. `max_drive_force_n`
7. `max_drive_speed_mps`
8. `brake_friction_force_n`
9. `mode`

#### Allowed Modes

1. `drive`
2. `brake`
3. `idle`

### 12.6 Track Switch

#### Purpose

Route the train to one of multiple downstream paths.

#### Model

A controlled topological device, not a direct force device.

#### Required Parameters

1. `id`
2. `junction_id`
3. `incoming_path_id`
4. `outgoing_path_ids`
5. `current_alignment`
6. `actuation_time_s`
7. `locked_when_occupied`

#### Rules

1. Must not change while occupied
2. Must honor route interlocks
3. Must integrate with the ride control system

## 13. Physics Engine Specification

### 13.1 Physics Strategy

The physics engine shall simulate train motion over time using distance along the route and path-local geometry.

Each simulation step should update:

1. Position
2. Speed
3. Tangential acceleration
4. Occupied intervals
5. Route progression across paths and switches

### 13.2 Longitudinal Forces

The total force along the track may include:

1. Gravity component along slope
2. Rolling resistance
3. Aerodynamic drag
4. Launch force
5. Lift engagement force
6. Brake force
7. Booster force

Conceptually:

```text
F_total = F_gravity_tangent
        + F_launch
        + F_lift
        + F_booster
        - F_drag
        - F_rolling
        - F_brake
```

Then:

```text
a_tangent = F_total / m_total
```

### 13.3 Curvature-Based Outputs

The engine should also compute:

1. Normal acceleration due to curvature
2. Lateral acceleration relative to bank angle
3. Vertical acceleration estimate from local frame decomposition
4. G-force metrics for analysis plots

### 13.4 Train-Length Effects

Because trains span multiple sections at once, the engine must support:

1. Front and rear of train being in different zones
2. Multiple vehicles crossing different devices simultaneously
3. Aggregation of distributed forces over occupied train intervals

This is a critical requirement and should not be simplified away.

### 13.5 Integration Method

Recommended initial method:

1. Fixed-step explicit integration for MVP
2. Optionally semi-implicit update for improved stability

Suggested configurable simulation time step:

1. `0.01 s` to `0.05 s` for interactive mode
2. Higher accuracy mode may be supported later

### 13.6 Simulation Modes

1. Interactive playback mode
2. Faster-than-real-time analysis mode
3. Scenario replay mode

## 14. Block, Occupancy, and Safety Model

### 14.1 Block Model

Each block shall have:

1. `id`
2. Associated path intervals
3. Occupancy state
4. Reservation state if used
5. Linked station or control metadata if applicable

### 14.2 Occupancy Rules

The system shall:

1. Mark a block occupied when any part of a train overlaps it
2. Release a block only when the full train has cleared it
3. Expose occupancy to the ride control system

### 14.3 Safety Interlocks

System-level interlocks should override user-authored rules when necessary.

Examples:

1. Prevent switch movement while occupied
2. Prevent dispatch if required downstream path is blocked
3. Prevent conflicting route commands
4. Prevent incompatible equipment states in the same zone if configured

## 15. Ride Control System

### 15.1 Core Design

The ride control system shall be event-driven and support two authoring modes:

1. Visual rule authoring
2. Python scripting

Both authoring modes should compile or feed into one common execution model.

### 15.2 Observable Inputs

The control layer shall be able to read:

1. Train front and rear positions
2. Vehicle intervals
3. Current route and destination
4. Switch states
5. Section and block occupancy
6. Equipment states
7. Timers
8. Station ready states
9. Load and unload completion flags
10. Emergency state

### 15.3 Controllable Outputs

The control layer shall be able to command:

1. Dispatch permit
2. Launch enable or disable
3. Pneumatic brake state changes
4. Trim brake enable or setting changes
5. Booster mode changes
6. Switch alignment requests
7. Hold and release logic at stations or hold zones

### 15.4 Visual Rules

The visual rule system should support:

1. Conditions
2. Actions
3. Timers
4. Logical combinations
5. Event triggers

Example rule concepts:

1. If block ahead is clear and station load complete, allow dispatch
2. If train front enters launch zone and route is valid, enable LSM
3. If emergency stop is active, close all configured emergency brakes
4. If maintenance route selected, align switch to maintenance branch when safe

### 15.5 Python Scripting

Python scripting should be:

1. Sandboxed
2. Restricted to a controlled API
3. Deterministic where possible

Example script API concepts:

1. `get_train("train_1").front_s`
2. `is_block_clear("block_A")`
3. `set_switch("sw_01", "maintenance")`
4. `set_equipment_state("brake_02", "closed")`
5. `allow_dispatch("station_main", True)`

### 15.6 Interlock Layer

The interlock engine should run independently of user-authored rules and should:

1. Validate every command before application
2. Reject unsafe or impossible commands
3. Return diagnostic reasons for rejected commands

## 16. Frontend and User Interface Specification

### 16.1 Primary Screens

1. Project dashboard
2. 3D track editor
3. Topology and routing editor
4. Train and vehicle editor
5. Equipment editor
6. Control logic editor
7. Simulation playback and telemetry view
8. Analysis and charting view

### 16.2 3D Editor Features

The 3D workspace should support:

1. Orbit, pan, zoom
2. Point selection and dragging
3. Bank angle editing
4. Section visualization by color
5. Equipment placement markers
6. Switch and branch visualization
7. Animated train playback

### 16.3 Interaction Design

The UI should make it easy to:

1. Import geometry
2. Refine geometry manually
3. Split sections
4. Assign zone types
5. Place equipment only in valid regions
6. Inspect engineering metrics at any track point
7. Review control logic state during simulation

### 16.4 Engineering Panels

The UI should provide:

1. Speed versus time
2. Speed versus track distance
3. Tangential acceleration
4. Normal acceleration
5. Lateral acceleration
6. Block occupancy timeline
7. Station dispatch timeline

## 17. Persistence and Project File Schema

### 17.1 Project Content

A saved project should contain:

1. Project metadata
2. Track paths and points
3. Junctions and switches
4. Sections and zones
5. Stations and blocks
6. Train definitions
7. Equipment definitions
8. Control rules
9. Python control scripts
10. Simulation settings

### 17.2 Example Top-Level JSON Shape

```json
{
  "project": {
    "name": "Example Ride",
    "units": "metric",
    "version": 1
  },
  "paths": [],
  "junctions": [],
  "switches": [],
  "sections": [],
  "stations": [],
  "blocks": [],
  "trains": [],
  "equipment": [],
  "control_rules": [],
  "control_scripts": [],
  "simulation_settings": {}
}
```

## 18. Recommended Backend Package Structure

```text
backend/
  app/
    api/
      projects.py
      tracks.py
      topology.py
      trains.py
      equipment.py
      control.py
      simulation.py
    models/
      project.py
      track.py
      topology.py
      train.py
      equipment.py
      control.py
      scenario.py
    simulation/
      geometry/
        spline.py
        frames.py
        curvature.py
      topology/
        graph.py
        routing.py
        switches.py
        blocks.py
      physics/
        integrator.py
        force_models.py
        resistance.py
        train_dynamics.py
        gforce.py
      equipment/
        lsm.py
        lift.py
        pneumatic_brake.py
        trim_brake.py
        booster.py
      control/
        rule_engine.py
        python_runtime.py
        interlocks.py
        events.py
      services/
        validator.py
        project_io.py
        telemetry.py
```

## 19. Recommended Frontend Package Structure

```text
frontend/
  src/
    app/
    api/
    state/
    components/
    features/
      track-editor/
      topology-editor/
      station-editor/
      train-editor/
      equipment-editor/
      control-editor/
      simulation-player/
      analytics/
    three/
      TrackMesh.tsx
      TrainMesh.tsx
      EquipmentOverlays.tsx
      SwitchOverlay.tsx
```

## 20. API Design Outline

### 20.1 Project APIs

1. `POST /projects`
2. `GET /projects/{id}`
3. `PUT /projects/{id}`
4. `DELETE /projects/{id}`

### 20.2 Track and Topology APIs

1. `POST /projects/{id}/paths`
2. `PUT /projects/{id}/paths/{path_id}`
3. `POST /projects/{id}/junctions`
4. `POST /projects/{id}/switches`
5. `POST /projects/{id}/sections`
6. `POST /projects/{id}/blocks`
7. `POST /projects/{id}/stations`

### 20.3 Equipment APIs

1. `POST /projects/{id}/equipment`
2. `PUT /projects/{id}/equipment/{equipment_id}`
3. `DELETE /projects/{id}/equipment/{equipment_id}`

### 20.4 Simulation APIs

1. `POST /projects/{id}/simulate/start`
2. `POST /projects/{id}/simulate/stop`
3. `POST /projects/{id}/simulate/reset`
4. `GET /projects/{id}/simulate/state`
5. `WS /projects/{id}/simulate/stream`

### 20.5 Control APIs

1. `POST /projects/{id}/control/rules`
2. `POST /projects/{id}/control/scripts`
3. `POST /projects/{id}/control/validate`
4. `POST /projects/{id}/control/compile`

## 21. Validation Rules

### 21.1 Geometry Validation

1. Path has enough points for interpolation
2. Path continuity is valid
3. Banking values are within configured limits
4. Curvature is within warning or error thresholds

### 21.2 Equipment Validation

1. Device lies fully within path bounds
2. Device lies in allowed section types
3. Straightness or slope constraints are satisfied where required
4. Devices do not overlap illegally

### 21.3 Operational Validation

1. Routes are complete
2. Switch graph has no invalid dangling connections
3. Stations and blocks are reachable
4. Multiple trains have valid initial placement

### 21.4 Control Validation

1. Visual rules reference existing entities
2. Python scripts use only allowed APIs
3. Unsafe commands are flagged
4. Circular or conflicting logic is detected where practical

## 22. Performance Targets

Recommended initial goals:

1. Interactive 3D editing with smooth navigation on typical engineering workstations
2. Real-time playback for at least a moderate-size track with multiple trains
3. Fast enough simulation loop for engineering iteration and parameter tuning

Indicative first targets:

1. 3 to 5 trains simulated in real time on a medium-size network
2. Playback at `>= 30 FPS` on the frontend
3. Physics step execution fast enough for interactive control testing

## 23. MVP Definition

The minimum viable product should include:

1. Track import from point lists with bank angle
2. Track and path editing
3. Section and zone editing
4. Multiple stations
5. Maintenance branch support
6. Switch placement and route control
7. Multi-car train definitions
8. Loaded and unloaded mass cases
9. LSM, lift, pneumatic brake, trim brake, and booster support
10. Multi-train occupancy and block logic
11. Visual control rules
12. Python control scripts
13. 3D visualization with animated trains
14. Save and load project files
15. Engineering charts for speed and acceleration

## 24. Phased Delivery Plan

### Phase 1: Formal Domain Model and Schemas

1. Freeze terminology and units
2. Define JSON and database schemas
3. Define API contracts
4. Define equipment parameter schemas
5. Define control rule schemas

### Phase 2: Track Geometry and Topology Core

1. Build editable path and spline model
2. Implement path graph and junctions
3. Implement section and zone model
4. Implement switches, stations, and blocks

### Phase 3: Physics Core

1. Add train and vehicle models
2. Implement gravity, drag, and rolling resistance
3. Implement route-following motion
4. Compute engineering metrics and g-force outputs

### Phase 4: Equipment Physics

1. Add LSM launch force curves
2. Add lift engagement and release
3. Add pneumatic brake behavior with both fail-safe modes
4. Add trim brake behavior
5. Add booster drive and brake behavior

### Phase 5: Ride Control

1. Build event model
2. Build visual rule engine
3. Build Python control runtime
4. Add interlock system
5. Add control diagnostics

### Phase 6: Frontend Editing and Playback

1. Build 3D editor
2. Build equipment placement workflow
3. Build train editor
4. Build control editor
5. Build simulation playback and telemetry panels

### Phase 7: Validation and Analysis

1. Scenario tools
2. Emergency stop studies
3. Throughput studies
4. Block timing analysis
5. Comparison of load cases

## 25. Risks and Mitigations

### Risk 1: Track smoothing creates unrealistic curvature spikes

Mitigation:

1. Use constrained interpolation
2. Display curvature plots
3. Add geometry validation warnings

### Risk 2: Train-length effects across multiple zones are implemented incorrectly

Mitigation:

1. Treat train occupancy as distributed intervals
2. Test front and rear crossing different devices
3. Write integration tests around partial-zone occupancy

### Risk 3: Switch and route logic becomes unstable in multi-train operation

Mitigation:

1. Use explicit route reservation logic
2. Add interlock validation before command application
3. Simulate route conflicts in automated tests

### Risk 4: User-authored control scripts create unsafe or non-deterministic behavior

Mitigation:

1. Restrict the script API
2. Add command validation and interlocks
3. Provide diagnostics for rejected actions

### Risk 5: Scope is too broad for one implementation pass

Mitigation:

1. Build a strong shared domain model first
2. Prioritize core correctness over polish
3. Release vertical slices rather than isolated subsystems

## 26. Acceptance Criteria for Version 1

Version 1 is considered successful when:

1. A user can create or import a branched coaster track with bank angles.
2. A user can edit geometry and operational sections in the UI.
3. A user can define trains with multiple vehicles and different load cases.
4. A user can place all required equipment types and switches.
5. The simulator can run multiple trains through stations, blocks, and branches.
6. The ride control system can operate using both visual rules and Python scripts.
7. The simulator visualizes train motion in 3D.
8. The simulator exposes speed and acceleration plots suitable for engineering review.
9. The project can be saved and reloaded without losing fidelity.

## 27. Immediate Next Steps

The next concrete project steps should be:

1. Create the canonical JSON schema for:
   1. track paths
   2. sections
   3. stations
   4. blocks
   5. switches
   6. trains
   7. equipment
   8. control rules
2. Scaffold the backend using `FastAPI`
3. Scaffold the frontend using `React`, `TypeScript`, and `react-three-fiber`
4. Implement the track geometry core first
5. Implement the topology graph and switch routing immediately after geometry
6. Build the single-train physics loop before extending to multi-train occupancy
7. Add save and load support early so all later work uses the persistent project structure

## 28. Suggested Build Order

If development starts immediately, the recommended order is:

1. Project schemas and data models
2. Track path editor and geometry processing
3. Path graph, sections, stations, switches, and blocks
4. Train model and route-following simulation
5. Equipment force models
6. Multi-train occupancy logic
7. Ride control engine
8. Polished frontend workflows and engineering dashboards

## 29. Final Note

This specification is designed to support a realistic first-generation engineering simulator rather than a simplified coaster game. The design favors correct track topology, force-based equipment behavior, and operational realism while staying within a feasible software scope for an incremental implementation.
