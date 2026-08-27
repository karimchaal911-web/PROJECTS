# Full Speaker Notes - Cinematic MAP Dryer Soutenance

The embedded film lasts about 83 seconds. For a full defense, launch the live 3D version and use Space only to pause/resume at the required chapters; the camera transitions themselves remain automatic. The PowerPoint chapter slides are intended for discussion and Q&A after the film.

## 01 - Site awakening

Film line: The process never waits, so visibility cannot either.

Soluble MAP production evolves continuously: material moves, energy is exchanged, and final moisture changes even when no new laboratory result is available. The project therefore starts with a supervision question, not a model question: how can the operating state of the dryer remain readable between quality-reference measurements?

Boundary: this is an advisory digitalization prototype. It does not write to the process, replace laboratory moisture, or claim autonomous control.

## 02 - Follow the granule

Film line: Follow one MAP granule through a coupled production chain.

The luminous granule connects neutralization, crystallization, centrifugation, drying, and cooling. A condition introduced upstream can arrive at the dryer later and interact with air, heat, feed loading, and residence time. The visual journey avoids treating the dryer as an isolated vessel.

## 03 - Dryer hero

Film line: Moisture is strongly shaped inside the rotary dryer.

The central object is a stylized rotary drum. Wet feed enters, the drum rotates, hot air crosses the material, and exhaust carries removed moisture. Temperature, air flow, feed, residence-related context, steam pressure, vacuum, fan behavior, and derived interactions all contribute to the final result.

Boundary: the cutaway is an explanatory mechanism, not a CFD simulation.

## 04 - Inside the drum

Film line: Rotation lifts the product; gravity cascades it through the heat field; vapor leaves.

The lifters and particle curtain make the history of the material visible. This is why the data preparation is residence-aware and why instantaneous signals alone cannot explain the product at the outlet.

## 05 - Time tunnel

Film line: The process keeps moving during roughly two hours of laboratory silence.

The three large white anchors represent the approximate laboratory spacing. They remain the final-moisture quality reference. The dense green pulses represent the prototype replay and visualization rhythm of five seconds.

Critical qualifier: five seconds is not a confirmed plant historian frequency. It is the implemented prototype cadence used for deterministic replay and dashboard visualization.

## 06 - Signal lattice

Film line: Raw signals become a disciplined data product.

The strands leaving the dryer are aligned, cleaned, engineered, and replayed in a structured order. Derived relationships include temperature differences, flow-to-feed relationships, interactions, and residence-aware context. The wireframe dryer means digitally readable supervision, not a full first-principles digital twin.

## 07 - Architecture flight

Film line: Sensors feed Python; Python prepares data and runs the models; PostgreSQL persists results; Power BI visualizes them.

The architecture is deliberately separated by responsibility. Python owns preprocessing and inference. The model outputs and context are persisted in PostgreSQL. Power BI reads the published data for supervision; it does not execute Ridge or One-Class SVM.

## 08 - Intelligence split

Film line: One data stream supports two different questions.

The quality branch asks, "What is the estimated final moisture between laboratory results?" The process branch asks, "Is this operating combination different from learned normal behavior?" Keeping the branches distinct prevents an anomaly display from being mistaken for a quality prediction.

## 09 - Ridge ribbon

Film line: Ridge provides an advisory moisture estimate between sparse laboratory anchors.

The selected soft sensor is Ridge regression with alpha 10 and 16 features. It combines process variables, previous laboratory context, and engineered relationships. The continuous ribbon is the estimate; the white spheres are laboratory anchors.

Boundary: the estimate fills a visibility interval. Laboratory moisture remains the quality reference.

## 10 - Novelty envelope

Film line: One-Class SVM recognizes novelty and points to evidence that should be checked.

The detector uses 15 process-only features. A negative decision function indicates novelty. The display transform produces an operator-facing risk scale, but that risk is not a calibrated probability. Robust contribution ranking localizes evidence; it does not prove causality. The validation novelty-flag rate is 5.925 percent.

## 11 - Validation theatre

Film line: Evidence comes before ambition.

The authentic held-out plot shows chronological TEST behavior over 165 laboratory samples. TEST performance is R-squared 0.8245, MAE 0.001069, and RMSE 0.001403. Error units are percentage points of moisture, percent H2O.

The development dataset is deterministic synthetic data covering 92 days, with 1,589,760 five-second replay rows, 1,104 laboratory observations, and 1,103 supervised rows. This proves reproducibility of the prototype; it does not prove generalization to live plant operation.

## 12 - Control room

Film line: Supervision is not automation.

The curved control-room surfaces use authentic project previews: an operating overview and a diagnostic investigation page. They expose predicted moisture, latest laboratory context, validated error, anomaly risk, process status, severity, trends, contributors, and verification guidance.

Critical qualifier: Power BI visualizes PostgreSQL outputs. Python runs the models. No control command is produced here.

## 13 - Operating loop

Film line: Replay, predict, detect, publish, supervise.

The camera pulls back so the whole operating-intelligence chain can be read at once. Physical signals become structured data; the two model branches generate complementary advisory context; PostgreSQL publishes the result; Power BI returns it to the operator.

Boundary: the five-second rhythm is prototype replay. There is no live PCS7 connection, actuator write-back, or autonomous loop.

## 14 - Governed roadmap

Film line: Prove the system in shadow mode before claiming plant value.

The solid node is the reproducible prototype. The outlined nodes are future work: read-only representative plant data, data-quality review, chronological shadow validation against laboratory results and operator observation, then a governed advisory deployment only if the evidence supports it.

Assisted operation would be a later possibility subject to governance and validation. Closed-loop control is outside the current project.

## 15 - Closing visibility

Film line: The dryer keeps moving; digital visibility continues beyond laboratory delay.

The final camera returns to the same physical dryer, now surrounded by the visibility ribbon, sensor pulses, and digital layer. The point is not to replace the laboratory or the operator. It is to keep the interval between laboratory results readable, actionable, and governed.

Close: laboratory moisture remains the reference. The prototype remains advisory. Invite questions, then use the chapter slides or live 3D scene navigation for discussion.
