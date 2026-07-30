# MAP Dryer AI

## Digitalization and Predictive Monitoring of the Soluble MAP Drying Process

**MAP Dryer AI** is an industrial digitalization and machine-learning project developed in the context of fertilizer production at **OCP Group**.

The project focuses on the production of **water-soluble Monoammonium Phosphate (MAP)** and, more specifically, on the **drying section of the MAP production installation**.

Its purpose is to build a digital layer around the industrial process by combining:

* process measurements from the production control system;
* laboratory quality measurements;
* process engineering knowledge;
* data processing and feature engineering;
* predictive machine-learning models;
* anomaly and off-spec detection;
* process visualization through an operator dashboard.

The project is structured as an industrial decision-support system rather than a replacement for the existing process-control infrastructure.

---

# 1. Industrial Context

## 1.1 OCP Group

OCP Group is a major industrial group operating across the phosphate value chain, from phosphate extraction and processing to the production of phosphoric acid and phosphate-based plant nutrition solutions.

Phosphate rock is transformed into intermediate and finished products used in agriculture and other industries.

Within the fertilizer value chain, phosphoric acid is an important intermediate used in the production of several phosphate fertilizers, including:

* Monoammonium Phosphate — MAP;
* Diammonium Phosphate — DAP;
* Triple Superphosphate — TSP;
* specialty and water-soluble plant nutrition products.

OCP also produces water-soluble MAP products intended for applications such as fertigation, foliar nutrition, hydroponics, and precision plant nutrition.

The MAP Dryer AI project fits within this broader industrial context by exploring how **process digitalization and machine learning can support fertilizer-production monitoring and product-quality prediction**.

---

# 2. Monoammonium Phosphate

## 2.1 What is MAP?

Monoammonium Phosphate is a phosphate compound produced from the reaction between:

* phosphoric acid;
* ammonia.

The simplified chemical reaction is:

```text
H3PO4 + NH3 → NH4H2PO4
```

or:

```text
Phosphoric Acid + Ammonia → Monoammonium Phosphate
```

MAP supplies two major plant nutrients:

```text
Phosphorus
+
Nitrogen
```

For water-soluble MAP production, product quality depends not only on obtaining the desired chemical composition but also on controlling physical and process characteristics such as:

* moisture;
* temperature;
* product condition;
* drying behavior;
* process stability;
* material residence;
* thermal conditions;
* air conditions;
* feed conditions.

The production process must therefore be treated as a **continuous interaction between chemistry, heat transfer, mass transfer, material flow, and process control**.

---

# 3. MAP Production Installation Studied in This Project

The installation studied by this project is represented through two principal production sections:

```text
Raw Materials
     │
     ▼
Neutralization
     │
     ▼
MAP Material / Wet Product
     │
     ▼
Drying
     │
     ▼
Cooling / Final Conditioning
     │
     ▼
Final MAP Product
```

The AI work in this repository concentrates on the **drying section**, while the neutralization section remains important because the condition of the material leaving neutralization directly affects the material entering the dryer.

---

# 4. Neutralization Section

## 4.1 Purpose

The neutralization stage creates the MAP-containing material that will continue through the downstream production process.

The principal chemical inputs are:

```text
Phosphoric Acid
+
Gaseous Ammonia
```

The installation can also contain recycled process liquids, including **mother liquor or other recovered liquid streams**, which are returned to the process.

A simplified representation is:

```text
Phosphoric Acid ──────┐
                      │
Gaseous Ammonia ──────┼──► Neutralization System
                      │
Recycled Liquids ─────┘
                              │
                              ▼
                         MAP Material
```

---

## 4.2 Reaction

Inside the neutralization system, phosphoric acid reacts with ammonia.

The reaction is **exothermic**, meaning that heat is released during the chemical reaction.

The neutralization system therefore combines:

```text
Chemical Reaction
+
Mixing
+
Material Flow
+
Thermal Behavior
+
Process Regulation
```

The addition of ammonia influences both the chemistry of the reacting medium and its thermal state.

Process control around this section is therefore important for maintaining stable operating conditions before the product reaches downstream equipment.

---

# 5. Recycled Liquids and Mother Liquor

Industrial fertilizer processes commonly reuse liquid streams generated elsewhere in the production circuit.

Within the installation studied during this project, recycled liquids form part of the process context surrounding MAP production.

A recycled liquid stream can be represented as:

```text
Process
   │
   ▼
Liquid Separation / Recovery
   │
   ▼
Mother Liquor / Recovered Liquid
   │
   └─────────────────┐
                     ▼
              Neutralization
```

This creates a process loop rather than a purely linear production chain.

From a digitalization perspective, this matters because the state of the current production cycle can depend partly on material returned from previous process stages.

---

# 6. Transition Toward Drying

After the upstream MAP preparation stage, the product entering the drying section still contains moisture that must be removed.

The drying installation must therefore transform:

```text
Wet MAP Product
```

into:

```text
Conditioned Final MAP Product
```

while preserving the required product quality.

The dryer is therefore not an isolated piece of equipment.

Its behavior depends on:

```text
Upstream Product Condition
        +
Product Feed
        +
Thermal Input
        +
Air Conditions
        +
Equipment Operating State
        +
Residence Conditions
        +
Downstream Conditions
```

This interaction is the central reason the drying section is suitable for a data-driven predictive-monitoring project.

---

# 7. Drying Section

## 7.1 Purpose of Drying

The purpose of the drying stage is to remove residual water from the MAP material using controlled heat and airflow.

At a simplified level:

```text
Wet MAP
   │
   ▼
┌──────────────────────┐
│       DRYER          │
│                      │
│ Heat                 │
│ Air Flow             │
│ Product Flow         │
│ Residence            │
│ Draft / Vacuum       │
└──────────────────────┘
   │
   ▼
Dried MAP
```

Drying involves both:

```text
Heat Transfer
```

and:

```text
Mass Transfer
```

Heat is transferred toward the product while water is removed from the material and transported away with the drying gas stream.

---

# 8. Dryer Process Architecture

The dryer can be viewed as an interaction between several physical domains.

## Thermal Domain

Includes measurements associated with temperatures and the energy supplied to the drying process.

Examples include:

```text
Dryer Air Temperature
Product Inlet Temperature
Final Product Temperature
Cooler Air Temperature
Steam Pressure
```

---

## Air and Gas Domain

Represents the movement of drying air and the draft conditions of the installation.

Examples include:

```text
Air Flow Rate
Vacuum
Fan Speed
```

These variables describe the gas-side operating conditions surrounding heat and moisture removal.

---

## Product Flow Domain

Represents how much material enters the dryer and how the material travels through it.

Examples include:

```text
Wet Product Feed Rate
Residence Time
Product Density
```

---

## Quality Domain

Represents the final state of the material after processing.

The central quality variable studied in this project is:

```text
Final Product Moisture
```

Other laboratory or process quality indicators may later be incorporated depending on data availability and project requirements.

---

# 9. Cooling and Final Product Condition

Drying is followed by downstream product conditioning.

The repository includes measurements associated with the cooling section because the thermal history of the product does not necessarily stop immediately at the dryer outlet.

The simplified sequence is:

```text
Wet MAP
   │
   ▼
Drying
   │
   ▼
Hot / Dried Product
   │
   ▼
Cooling
   │
   ▼
Final Product
```

This is why variables related to dryer conditions, final product temperature, and cooler conditions can be considered together when describing the overall process state.

---

# 10. Industrial Instrumentation

The process is monitored through industrial instrumentation connected to the plant control system.

The installation contains measurements related to:

```text
Temperature
Pressure
Flow
Vacuum
Equipment Speed
Material Feed
Product State
```

These signals create the process-information layer required for digitalization.

---

# 11. Siemens PCS7

A major process-data source for the project is **Siemens PCS7**.

PCS7 is the plant's distributed process-control environment used to supervise and control industrial operations.

At project level, PCS7 represents the source of continuously available process information.

Conceptually:

```text
Sensors
   │
   ▼
Transmitters
   │
   ▼
PLC / Automation Layer
   │
   ▼
Siemens PCS7
   │
   ├── Process Control
   ├── Operator Visualization
   ├── Alarms
   ├── Trends
   └── Process Measurements
```

The machine-learning system is designed as an additional layer around this infrastructure.

It does not replace PCS7.

---

# 12. PCS7 Variables Used by the Project

The dryer dataset contains process information such as:

```text
dryer_air_temperature
cooler_air_temperature
air_flow_rate
wet_product_feed_rate
product_inlet_temperature
residence_time
vacuum
steam_pressure
fan_speed
product_density
final_product_temp
```

These variables describe different parts of the process and together provide a representation of the operating condition of the dryer.

---

# 13. Laboratory Data

Not every important quality measurement comes directly from PCS7.

Some product characteristics are determined through laboratory analysis.

The main quality target currently considered by the project is:

```text
final_moisture_h₂o
```

The industrial information architecture therefore contains two different data sources:

```text
PROCESS DATA                       QUALITY DATA

Siemens PCS7                       Laboratory
     │                                 │
     │                                 │
Temperatures                        Moisture
Flows                               Product Analysis
Pressure                            Quality Measurements
Vacuum
Fan State
Feed Conditions
     │                                 │
     └───────────────┬─────────────────┘
                     ▼
              Unified Dataset
```

---

# 14. The Data-Alignment Problem

PCS7 process measurements and laboratory measurements are not naturally produced in the same way.

Process measurements can be generated continuously.

Laboratory results correspond to samples taken from the physical process and analyzed separately.

Therefore:

```text
Process Timestamp
≠
Automatically
Laboratory Timestamp
```

A reliable industrial ML system must associate each product-quality result with the process conditions that actually produced that material.

The future production data pipeline must therefore consider:

```text
Sampling Time
+
Material Residence Time
+
Process Delay
+
Relevant Historical Window
+
Laboratory Analysis Time
```

This temporal alignment is a core architectural component of the project.

---

# 15. Why a Soft Sensor?

A laboratory analyzer provides a direct measurement of product quality.

A **soft sensor** estimates a variable indirectly using other measurements.

In this project:

```text
PCS7 Process Variables
          │
          ▼
Machine-Learning Model
          │
          ▼
Estimated Final Moisture
```

The model therefore acts as a virtual measurement layer between process instrumentation and product-quality information.

Conceptually:

```text
Physical Sensor
      ↓
Process Variable

Laboratory
      ↓
Quality Measurement

ML Soft Sensor
      ↓
Estimated Quality State
```

---

# 16. Project Scope

The complete project is designed around three complementary AI components.

```text
MAP Dryer AI
│
├── Model 1 — Moisture Soft Sensor
│
├── Model 2 — Off-Spec Detection
│
└── Model 3 — Anomaly Detection
```

Each model addresses a different industrial question.

---

# 17. Model 1 — Moisture Soft Sensor

The first model is a regression system.

Its architecture is:

```text
Process Measurements
        │
        ▼
Feature Engineering
        │
        ▼
Regression Model
        │
        ▼
Estimated Product Moisture
```

The model uses dryer operating conditions to estimate the moisture state of the resulting product.

This forms the main predictive-quality component of the project.

---

# 18. Model 2 — Off-Spec Classification

The second model is intended to represent the product state as a classification problem.

Conceptually:

```text
Current Process State
        │
        ▼
Classification Model
        │
        ├── Normal / In Specification
        │
        └── Potential Off-Spec Condition
```

The classification model complements the regression model.

While the regression model estimates a continuous quality variable, the classifier creates a direct process-quality status that can later be integrated into alarms or dashboard indicators.

---

# 19. Model 3 — Anomaly Detection

The anomaly model addresses abnormal process behavior.

Unlike the soft sensor, anomaly detection does not necessarily need a final laboratory target for every observation.

Its architecture can be represented as:

```text
Current Process Variables
        │
        ▼
Learned Normal Operating Behavior
        │
        ▼
Deviation Detection
        │
        ├── Normal Process State
        │
        └── Abnormal Process State
```

Its purpose is to identify combinations of measurements that differ from the process behavior represented in the training data.

This provides a process-monitoring perspective rather than only a product-quality perspective.

---

# 20. Combined AI Architecture

The three models are designed to work together.

```text
                    PROCESS DATA
                        │
                        ▼
                Data Processing Layer
                        │
                        ▼
                Feature Engineering
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
      Soft Sensor    Off-Spec      Anomaly
      Regression    Classifier     Detection
          │             │             │
          ▼             ▼             ▼
      Moisture       Quality       Process
      Estimate        Status        Health
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                 Decision Layer
                        │
                        ▼
                    Dashboard
```

---

# 21. Feature Engineering

Raw process variables do not always describe the physical relationships inside the dryer directly.

The project therefore includes an engineering layer that creates additional process indicators from existing measurements.

Current engineered variables include:

```text
temperature_drop
air_product_delta
air_per_feed
steam_temp_interaction
heating_index
```

These features represent combinations of process conditions such as:

```text
Temperature Relationships
Air-to-Product Relationship
Thermal Input Relationships
Residence-and-Temperature Relationships
```

The general architecture is:

```text
RAW PROCESS VARIABLES
          │
          ▼
ENGINEERING RELATIONSHIPS
          │
          ▼
MODEL FEATURES
```

The purpose is to give the predictive models access to relationships between measurements rather than only isolated sensor values.

---

# 22. End-to-End Industrial Architecture

The intended final architecture of the project is:

```text
                    INDUSTRIAL PROCESS
                           │
                           ▼
                    Physical Sensors
                           │
                           ▼
                     Siemens PCS7
                           │
                           ▼
                Process Data Acquisition
                           │
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
      Process Measurements         Laboratory Results
            │                             │
            └──────────────┬──────────────┘
                           ▼
                    Data Alignment
                           │
                           ▼
                    Data Validation
                           │
                           ▼
                    Data Cleaning
                           │
                           ▼
                  Feature Engineering
                           │
                           ▼
                  Predictive AI Layer
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
          Soft Sensor   Off-Spec     Anomaly
              │        Classification Detection
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Process Health
                           │
                           ▼
                      Dashboard
                           │
                           ▼
                Operator / Engineer
                           │
                           ▼
                  Operational Decision
```

---

# 23. Control-System Positioning

A distinction must be made between:

```text
PROCESS CONTROL
```

and:

```text
PREDICTIVE DECISION SUPPORT
```

PCS7 remains responsible for industrial process control.

MAP Dryer AI is designed around:

```text
Monitoring
Prediction
Anomaly Detection
Quality Estimation
Visualization
Decision Support
```

Therefore the initial architecture is:

```text
PCS7
 │
 ├── Reads Sensors
 ├── Controls Equipment
 ├── Executes Control Loops
 ├── Handles Industrial Alarms
 │
 └────────► MAP Dryer AI
                 │
                 ├── Analyze
                 ├── Predict
                 ├── Detect
                 └── Display
```

The AI layer should initially remain separate from direct actuator control.

---

# 24. Future Closed-Loop Architecture

A future industrial architecture could allow model outputs to participate in control decisions.

Conceptually:

```text
Process
   │
   ▼
PCS7
   │
   ▼
AI Monitoring
   │
   ▼
Recommendation / Alert
   │
   ▼
Operator Validation
   │
   ▼
PCS7 Action
```

Only after sufficient industrial validation could more advanced architectures be considered.

For example:

```text
AI Prediction
      │
      ▼
Supervisory Logic
      │
      ▼
Safety / Constraint Layer
      │
      ▼
PCS7 Setpoint Adjustment
```

Any connection between machine learning and physical plant control would require dedicated industrial validation, cybersecurity review, process-safety assessment, control-engineering validation, authorization logic, operating procedures, and appropriate human supervision.

---

# 25. Data Architecture

The project follows a layered data architecture.

```text
data/
│
├── raw/
│
├── processed/
│
└── external/
```

---

## Raw Data

```text
data/raw/
```

Contains original source datasets.

Typical sources include:

```text
PCS7 Process Data
Laboratory Measurements
Prototype Industrial Data
```

Raw data should remain unchanged so that the processing pipeline can always be reproduced.

---

## Processed Data

```text
data/processed/
```

Contains datasets produced after:

```text
Schema Validation
Data-Type Conversion
Timestamp Construction
Duplicate Handling
Missing-Value Handling
Feature Engineering
Model Preparation
```

---

## External Data

```text
data/external/
```

Reserved for additional reference information that may later support the project.

---

# 26. Repository Architecture

```text
MAP-Dryer-AI/
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── figures/
│
├── final report/
│
├── installation_analysis/
│   ├── industrial_analysis/
│   └── process_analysis/
│
├── models/
│   ├── soft_sensor/
│   ├── off_spec/
│   └── anomaly/
│
├── notebooks/
│   ├── 01_Data_Exploration.ipynb
│   ├── 02_Feature_Engineering.ipynb
│   ├── 03_Model1_SoftSensor.ipynb
│   ├── 04_Model2_OffSpec.ipynb
│   ├── 05_Model3_Anomaly.ipynb
│   └── 06_Model_Comparison.ipynb
│
├── src/
│   ├── data/
│   ├── stats/
│   ├── features/
│   ├── models/
│   ├── visualization/
│   └── utils/
│
├── .gitignore
│
└── README.md
```

---

# 27. Installation Analysis

The folder:

```text
installation_analysis/
```

contains the process-understanding layer of the project.

It separates the engineering work surrounding the physical production installation from the machine-learning implementation.

```text
installation_analysis/
│
├── industrial_analysis/
│
└── process_analysis/
```

This section can contain:

* process-flow analysis;
* equipment understanding;
* production diagrams;
* PCS7 screenshots;
* process-variable identification;
* instrumentation analysis;
* material-flow analysis;
* operating logic;
* relationships between process stages;
* notes collected from production personnel;
* technical documentation.

This engineering context is essential because the project is not intended to treat the MAP dryer as a generic tabular machine-learning dataset.

The data must remain linked to the actual industrial process.

---

# 28. Notebook Architecture

The development workflow is divided into dedicated notebooks.

```text
01_Data_Exploration
        │
        ▼
02_Feature_Engineering
        │
        ▼
03_Model1_SoftSensor
        │
        ▼
04_Model2_OffSpec
        │
        ▼
05_Model3_Anomaly
        │
        ▼
06_Model_Comparison
```

---

# 29. Data Exploration

```text
01_Data_Exploration.ipynb
```

This notebook handles the initial dataset inspection.

Its role includes:

```text
Data Loading
Schema Inspection
Variable Identification
Data-Type Verification
Timestamp Handling
Missing-Value Detection
Duplicate Detection
Descriptive Analysis
Data Visualization
```

The objective is to establish a clean and understood representation of the dryer dataset before model development.

---

# 30. Feature Engineering

```text
02_Feature_Engineering.ipynb
```

This notebook connects process understanding with model preparation.

It handles:

```text
Variable Preparation
Timestamp Construction
Data Cleaning
Process Relationships
Engineered Features
Correlation Analysis
Feature Review
Model-Ready Dataset Creation
```

The feature-engineering layer is where industrial understanding of the dryer begins to become mathematical input for machine-learning models.

---

# 31. Soft-Sensor Development

```text
03_Model1_SoftSensor.ipynb
```

This notebook contains the regression workflow used to build the moisture soft sensor.

Its architecture is:

```text
Processed Dataset
       │
       ▼
Feature Selection
       │
       ▼
Time-Aware Data Split
       │
       ▼
Preprocessing
       │
       ▼
Model Training
       │
       ▼
Validation
       │
       ▼
Model Selection
       │
       ▼
Explainability
       │
       ▼
Final Soft Sensor
```

---

# 32. Off-Spec Model

```text
04_Model2_OffSpec.ipynb
```

This notebook is dedicated to the classification component.

Its intended workflow is:

```text
Process State
     +
Quality State
     │
     ▼
Specification Label
     │
     ▼
Classifier
     │
     ▼
Quality Status
```

---

# 33. Anomaly Model

```text
05_Model3_Anomaly.ipynb
```

This notebook is dedicated to process anomaly detection.

Its intended architecture is:

```text
Process Variables
       │
       ▼
Normal Operating Representation
       │
       ▼
Anomaly Detection
       │
       ▼
Process Health Indicator
```

---

# 34. Model Comparison

```text
06_Model_Comparison.ipynb
```

This notebook is intended to bring the different AI components into a common evaluation framework.

The goal is to compare their roles within the full monitoring architecture rather than treating them as isolated experiments.

---

# 35. Source Code Architecture

Reusable logic is progressively moved from notebooks into:

```text
src/
```

The intended structure is:

```text
src/
│
├── data/
│
├── stats/
│
├── features/
│
├── models/
│
├── visualization/
│
└── utils/
```

---

## Data Layer

```text
src/data/
```

Responsible for:

```text
Dataset Loading
Schema Validation
Column Standardization
Numeric Conversion
Timestamp Creation
Cleaning Operations
Project Paths
```

---

## Statistics Layer

```text
src/stats/
```

Contains reusable statistical-analysis functions.

---

## Features Layer

```text
src/features/
```

Designed to contain:

```text
Process Feature Engineering
Feature Transformation
Lag Features
Rolling Features
Temporal Features
Process-Window Features
```

---

## Models Layer

```text
src/models/
```

Designed to contain:

```text
Model Training
Prediction
Model Loading
Model Saving
Validation Utilities
Inference Pipelines
```

---

## Visualization Layer

```text
src/visualization/
```

Designed to contain reusable plotting and dashboard-support functions.

---

## Utilities Layer

```text
src/utils/
```

Reserved for shared project utilities.

---

# 36. Model Storage

Trained models are separated according to industrial function.

```text
models/
│
├── soft_sensor/
├── off_spec/
└── anomaly/
```

This keeps the three predictive components independent while allowing them to be combined by the dashboard.

---

# 37. Dashboard Architecture

The dashboard layer is located in:

```text
dashboard/
```

and is designed around Streamlit.

Its intended role is to bring the process and AI results into a single interface.

A future interface could conceptually contain:

```text
┌────────────────────────────────────────────┐
│              MAP DRYER AI                  │
├────────────────────────────────────────────┤
│                                            │
│  Process State                             │
│                                            │
│  Dryer Temperature                         │
│  Air Flow                                  │
│  Feed State                                │
│  Steam / Thermal State                     │
│  Vacuum                                    │
│  Fan State                                 │
│                                            │
├────────────────────────────────────────────┤
│                                            │
│  AI Monitoring                             │
│                                            │
│  Estimated Moisture                        │
│  Off-Spec Status                           │
│  Process Anomaly Status                    │
│                                            │
├────────────────────────────────────────────┤
│                                            │
│  Trends                                    │
│  Alerts                                    │
│  Explanations                              │
│  Historical Data                           │
│                                            │
└────────────────────────────────────────────┘
```

---

# 38. Real-Time Target Architecture

The long-term project architecture is designed around automatic data acquisition.

```text
Physical Process
       │
       ▼
Sensors
       │
       ▼
PCS7 / Process Historian
       │
       ▼
Automatic Data Collector
       │
       ▼
Data Processing Pipeline
       │
       ▼
Feature Engineering
       │
       ▼
Models
       │
       ▼
Dashboard
```

Laboratory data enters through a parallel pipeline:

```text
Laboratory
    │
    ▼
Laboratory Data Source
    │
    ▼
Quality Data Import
    │
    ▼
Timestamp / Sample Alignment
    │
    ▼
Historical Training Dataset
```

---

# 39. Training Architecture vs Runtime Architecture

An important architectural distinction exists between model development and model operation.

## Training

```text
Historical PCS7 Data
         +
Historical Laboratory Data
         │
         ▼
Data Alignment
         │
         ▼
Feature Engineering
         │
         ▼
Model Training
         │
         ▼
Validated Model
```

---

## Runtime

```text
Current PCS7 Data
        │
        ▼
Same Feature Pipeline
        │
        ▼
Saved Model
        │
        ▼
Prediction
        │
        ▼
Dashboard / Monitoring Layer
```

Laboratory values are primarily required for:

```text
Training
Validation
Model Monitoring
Future Retraining
```

The soft sensor is intended to estimate quality from available process measurements during operation.

---

# 40. Future Process-Historian Integration

The prototype data-collection workflow can eventually be replaced by automated extraction from PCS7 or an associated process historian.

The desired architecture is:

```text
PCS7
 │
 ▼
Historian
 │
 ▼
Query / Export Layer
 │
 ▼
Python Data Pipeline
 │
 ▼
Model Inference
```

This would remove dependence on manually recording control-room snapshots.

---

# 41. Laboratory Integration

Laboratory information may also eventually be retrieved automatically from the system used to manage quality results.

The target architecture would become:

```text
              PCS7 / Historian
                     │
                     ▼
              Process Dataset
                     │
                     │
                     ▼
                Alignment
                     ▲
                     │
                     │
             Laboratory System
                     │
                     ▼
               Quality Dataset
```

This aligned historical database becomes the foundation for model training and maintenance.

---

# 42. Process Windowing

A laboratory sample represents material that passed through the process over a preceding period.

For that reason, future dataset construction can evolve from simple point-to-point alignment toward process windows.

Conceptually:

```text
Process History
│
├── Previous Temperature Behavior
├── Previous Air-Flow Behavior
├── Previous Feed Behavior
├── Previous Steam Conditions
├── Previous Vacuum Conditions
└── Previous Equipment Conditions
             │
             ▼
       Process Window
             │
             ▼
      Laboratory Sample
```

These windows can later generate features such as:

```text
Average
Minimum
Maximum
Variation
Trend
Lag
Rolling Mean
Rolling Standard Deviation
Rate of Change
```

This forms part of the planned industrial-data architecture.

---

# 43. Explainability Layer

Industrial machine learning should provide more than a prediction.

The project therefore contains an explainability layer.

Conceptually:

```text
Prediction
    │
    ▼
Explainability
    │
    ├── Feature Importance
    ├── Model Coefficients
    ├── SHAP
    └── Local Prediction Explanation
```

The dashboard can later expose this information to help engineers understand which measurements are influencing model output.

---

# 44. Monitoring Architecture

Once a model is deployed, the system must monitor both the plant and the model.

```text
LIVE SYSTEM
│
├── Process Monitoring
│   ├── Sensor Availability
│   ├── Variable Ranges
│   └── Process State
│
├── Prediction Monitoring
│   ├── Moisture Estimate
│   ├── Off-Spec State
│   └── Anomaly State
│
└── Model Monitoring
    ├── Input Drift
    ├── Prediction Drift
    ├── Model Performance
    └── Retraining Requirement
```

---

# 45. Human-in-the-Loop Architecture

The project is designed around an operator-assisted workflow.

```text
AI Detects / Predicts
        │
        ▼
Dashboard
        │
        ▼
Operator / Process Engineer
        │
        ▼
Process Assessment
        │
        ▼
Approved Operational Action
```

The predictive system provides information to the human operator while the control system remains responsible for executing industrial commands.

---

# 46. Project Philosophy

The project follows the principle:

```text
Process Understanding
        ↓
Data Understanding
        ↓
Reliable Dataset
        ↓
Feature Engineering
        ↓
Machine Learning
        ↓
Validation
        ↓
Industrial Integration
```

The AI model is therefore only one component of the complete system.

The complete project includes:

```text
Chemical Process
Industrial Equipment
Instrumentation
PCS7
Laboratory
Data Engineering
Machine Learning
Software Architecture
Dashboarding
Industrial Validation
Process Control
```

---

# 47. Technology Stack

The project is developed primarily in Python.

The current and planned technical stack includes:

```text
Python
Pandas
NumPy
SciPy
Scikit-learn
Statsmodels
SHAP
Matplotlib
Seaborn
OpenPyXL
Jupyter
Streamlit
Joblib
```

The architecture is intentionally modular so that additional tools can later be introduced for:

```text
Industrial Data Acquisition
Databases
APIs
Process Historians
Deployment
Monitoring
Containerization
Cloud or On-Premise Infrastructure
```

---

# 48. Project Workflow

The complete development workflow can be summarized as:

```text
UNDERSTAND INSTALLATION
        │
        ▼
IDENTIFY CRITICAL VARIABLES
        │
        ▼
COLLECT PROCESS + LAB DATA
        │
        ▼
CLEAN AND VALIDATE DATA
        │
        ▼
ALIGN PROCESS WITH QUALITY
        │
        ▼
ENGINEER PROCESS FEATURES
        │
        ▼
TRAIN AI MODELS
        │
        ▼
VALIDATE MODELS
        │
        ▼
BUILD DASHBOARD
        │
        ▼
CONNECT REAL-TIME DATA
        │
        ▼
MONITOR PROCESS
        │
        ▼
INDUSTRIAL VALIDATION
```

---

# 49. Development Roadmap

```text
Repository Architecture
        │
        ▼
Installation Understanding
        │
        ▼
Dryer Variable Identification
        │
        ▼
Prototype Dataset
        │
        ▼
Data Exploration
        │
        ▼
Feature Engineering
        │
        ▼
Soft-Sensor Development
        │
        ▼
Industrial Historical Dataset
        │
        ▼
PCS7 / Laboratory Alignment
        │
        ▼
Soft-Sensor Refinement
        │
        ▼
Off-Spec Classification
        │
        ▼
Anomaly Detection
        │
        ▼
Model Integration
        │
        ▼
Streamlit Dashboard
        │
        ▼
Automated Process Data Acquisition
        │
        ▼
Model Monitoring
        │
        ▼
Industrial Decision-Support System
```

---

# 50. Final Project Vision

The final vision of MAP Dryer AI is a digital monitoring system positioned between the physical MAP production process and the engineers responsible for supervising it.

```text
                         OCP
                          │
                          ▼
                MAP Production Process
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       Neutralization               Drying
              │                       │
              └───────────┬───────────┘
                          ▼
                   Final MAP Product
                          │
                          ▼
                   Quality Control

========================================================

                 DIGITALIZATION LAYER

Physical Process
      │
      ▼
Instrumentation
      │
      ▼
Siemens PCS7
      │
      ▼
Process Data
      │
      ├───────────────┐
      │               │
      ▼               ▼
Real-Time Data      Historical Data
      │               │
      │               ├──── Laboratory Data
      │               │
      ▼               ▼
      Data Processing & Alignment
                    │
                    ▼
             Feature Engineering
                    │
                    ▼
              AI Model Layer
          ┌─────────┼─────────┐
          │         │         │
          ▼         ▼         ▼
       Moisture  Off-Spec   Anomaly
       Sensor    Detection  Detection
          │         │         │
          └─────────┼─────────┘
                    ▼
              Process Health
                    │
                    ▼
                 Dashboard
                    │
                    ▼
          Operator / Engineer
                    │
                    ▼
             Process Decision
```

The goal is to transform plant information from isolated measurements and laboratory results into a unified predictive view of the MAP drying process.

The project therefore sits at the intersection of:

```text
Fertilizer Production
+
Chemical Engineering
+
Process Engineering
+
Industrial Automation
+
Data Engineering
+
Machine Learning
+
Industrial Digitalization
```

and uses the MAP drying installation as the industrial application around which these technologies are integrated.

---

# 51. Repository Purpose

This repository documents the development of that system from process understanding to machine-learning implementation.

It is intended to contain:

```text
Installation Analysis
Process Documentation
Industrial Data
Data Processing
Feature Engineering
Model Development
Model Explainability
Anomaly Detection
Quality Prediction
Dashboard Development
Deployment Architecture
```

The repository should therefore be understood as the **digital representation of the MAP dryer AI project**, not merely as a collection of machine-learning notebooks.

---

# 52. Industrial Use Disclaimer

This repository is a research, internship, and development project.

The models and software contained in the repository must not be considered replacements for:

```text
PCS7 Control Logic
Industrial Interlocks
Safety Systems
Laboratory Quality Control
Process Procedures
Operator Judgment
Engineering Validation
```

Any future use of machine-learning output in an industrial control loop must pass through the appropriate engineering, safety, cybersecurity, operational, and organizational validation processes.

Real industrial data, internal documentation, control-system information, or other proprietary OCP information should only be stored or published when authorized.

