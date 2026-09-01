# FULL SPOKEN SCRIPT

**14 scenes · 42 presenter steps · target 12–13 minutes**

> Durations below are the scene table's own `seconds` fields (758 s declared,
> 12 min 38 s), not estimates. If you change a scene's length in
> `web/src/state/scenes.js`, change it here too.
>
> The film was 784 s. Forty-eight seconds of held frames came out — the push
> across the machine, the settle after the time axis forms, the loop signal, and
> the QUESTIONS card, which had been budgeted as though the Q&A after it were
> part of the film. Sixteen seconds went back in, all of it to two beats that
> were carrying more argument than they had room for: residence-time alignment
> (scene 07, now two beats) and the handover from artifact to running service
> (scene 10). Net −26 s, and the slot has about fifty seconds of slack in it for
> a jury that interrupts.

Read naturally, not from the page. Every number here is verified — see
`design/RESOURCE_AUDIT.md` for provenance. Where a sentence is marked
**[GUARD]**, say it: those are the honesty statements the jury will otherwise
have to extract from you under questioning.

`→` marks a press of the right arrow.

---

## SCENE 01 — AWAKENING · ~30 s

> Good morning. What you are looking at is a rotary dryer inside the soluble MAP
> production line at Jorf Lasfar.
>
> *(pause — let the machine turn)*
>
> It is a continuous process. It does not stop for shifts, and it does not stop
> for measurements. That single fact is what this entire project is about.
>
> My work is an industrial digitalization and supervision project: taking a
> process that already runs, making more of it visible, and giving the operator
> better information — with predictive analytics and anomaly detection as the
> intelligence layer, not as the point.

→

---

## SCENE 02 — WHY THIS MATERIAL · ~21 s *(3 steps)*

> Three presenter-driven beats — **PHOSPHORUS → PLANT NUTRITION → SOLUBLE MAP**.
> They used to auto-advance on a 1.9 s timer you could not control. Press when
> you are ready, not when the clock says so.

> Phosphorus is one of the three nutrients a plant cannot substitute. OCP's
> business is getting it into a form crops can actually take up.
>
> Soluble MAP — monoammonium phosphate — is one of those forms. This is the real
> product specification from the storage hall: twelve, sixty-one, zero-zero, and
> the property that matters commercially is that it dissolves completely in
> water.
>
> Which means residual moisture in the finished crystal is not a cosmetic
> quality. It is the quality.

→

---

## SCENE 03 — FOLLOW THE MATERIAL · ~78 s *(8 steps)*

> The camera travels WITH the material and STOPS AT EVERY STAGE. One press per
> stage. The previous cut had four stops for seven stations, so pretreatment,
> ammonia vaporization, the buffer tanks and centrifugation went past at travel
> speed and were never seen. Each stage now arrives, settles, is named on
> screen, gets one sentence, and hands the material on.

### Beat 1 — THE CHAIN
> Let me show you where the product comes from. Seven stages, one continuous
> flow. Phosphoric acid and ammonia go in at this end, and from here the
> material never stops moving.

→

### Beat 2 — 01 PHOSPHORIC-ACID PRETREATMENT
> The first of the two feeds. The acid is conditioned here before it reaches
> the reaction.

→

### Beat 3 — 02 AMMONIA VAPORIZATION
> The second feed. Liquid ammonia is vaporised in these heat exchangers and
> enters the reaction as a gas.

→

### Beat 4 — 03 NEUTRALIZATION
> This is where they react, in three agitated reactors in series, and that
> reaction is the whole chemistry of this plant: phosphoric acid plus ammonia
> gives monoammonium phosphate in solution.
>
> Note the low line coming back into this stage. That is mother liquor
> returning from downstream. I will come back to it.

→

### Beat 5 — 04 BUFFER / STABILIZATION
> The solution is held and blended in these tanks before crystallization.
>
> This stage matters more than it looks. It deliberately mixes and delays —
> so anything unusual upstream does not arrive downstream as a step, it
> arrives spread out in time.

→

### Beat 6 — 05 CONCENTRATION & CRYSTALLIZATION
> The solution is concentrated and crystallised. From this point the product is
> a wet solid, not a liquid.

→

### Beat 7 — 06 CENTRIFUGATION
> The crystals are separated from the mother liquor. The crystals go on to the
> dryer; the mother liquor goes back to neutralization — that is the labelled
> line — which is what makes this a loop rather than a line.

→

### Beat 8 — INTO THE DRYER
> Looking back up the whole chain. Then the crystals are dried, then cooled and
> conditioned.
>
> **[GUARD]** So the dryer is the last stage, not the only cause. Because the
> stages are coupled and the mother liquor recycles, when final moisture drifts
> you cannot attribute it to any one of them. That is a diagnosis problem, and
> I will come back to it.

→

---

## SCENE 04 — ENTER THE DRYER · ~57 s *(3 steps)*

### Beat 1 — MACHINE
> This is the stage that sets final moisture.
>
> An inclined rotating shell carried on two riding rings. Wet crystals enter at
> the high end, dried product leaves at the low end. It turns slowly and
> continuously.

→

### Beat 2 — PHYSICS
> Inside, flights lift the material and cascade it through a counter-current
> stream of hot air. Heat goes into the product, moisture leaves with the
> exhaust.
>
> **[GUARD]** This is a schematic transfer picture — it is not a CFD result and I
> am not claiming to have simulated the internals.
>
> What matters is that the outcome depends on several things at once: how much
> material, how hot the air, how much air, how long it stays inside.

→

### Beat 3 — DATA
> And all of those are measured. Nine process variables, on the prototype's
> five-second grid: dryer air temperature, steam pressure, air flow, feed rate,
> residence time, vacuum, fan speed, and the temperatures either side.
>
> Every one of those is continuous.
>
> The one thing that is *not* continuous is the number on the right — final
> moisture. That comes from the laboratory.

→

---

## SCENE 05 — THE VISIBILITY GAP · ~56 s *(3 steps)* — **the centre of the talk**

### Beat 1 — DISTANCE BECOMES TIME
> So let me change what this axis means.
>
> *(let the flow line straighten — do not talk over it)*
>
> The path the material was travelling is now twelve hours of real production —
> a window from the held-out test period. The material keeps flowing. Nothing
> about the process has changed.

→

### Beat 2 — SIX RESULTS
> These are the laboratory results in that window. All of them. Six.
>
> Point zero seven four. Point zero seven nine. Point zero eight zero. And so
> on — on a percentage-point scale, so this is hundredths of a percent of water.
>
> Two hours apart.

→

### Beat 3 — THROUGH THE INTERVAL
> Now watch the gap between the first two.
>
> *(silence — let the camera travel; roughly six seconds)*
>
> Two hours between results, and nothing measured in between.
>
> And this is not a theoretical concern. Between those two results the product
> actually moved by five thousandths of a percentage point — a real change, in
> real product that was really packed and shipped, and nothing measured it while
> it happened.

→

---

## SCENE 06 — THE ENGINEERING RESPONSE · ~38 s *(2 steps)*

### Beat 1 — THE QUESTION
> So: how do we see between measurements?
>
> The answer is not to sample more often. Laboratory analysis costs time and
> people, and you would still have gaps. The answer is to infer the quantity we
> cannot measure continuously from the quantities we already do.

→

### Beat 2 — ESTIMATE BETWEEN MEASUREMENTS
> *(let the trace draw)*
>
> That is a soft sensor. Six hundred and ninety-five estimates across the same
> twelve hours, from the same window, using only process variables aligned to
> the product they describe, plus the previous laboratory result.
>
> **[GUARD]** Notice it lands near each laboratory point without replacing it.
> The laboratory remains the reference. This is an estimate between references,
> not a substitute for them.

→

> One more sentence before we move: filling that gap answers only one question —
> what is the moisture likely to be right now. There is a second, different
> question, and a separate model answers it. You will see both in a moment.

→

> *(The old third beat here — "TWO QUESTIONS. ONE SUPERVISION SYSTEM." — was cut.
> Scene 08 opens on exactly that idea eighty seconds later, with the models
> actually on screen, and the beat parked the camera at the farthest pose in the
> film to say it.)*

---

## SCENE 07 — PHYSICAL BECOMES DIGITAL · ~78 s *(4 steps)*

### Beat 1 — SENSORS
> Let me show you what actually leaves the equipment.

→

### Beat 2 — THE STACK BUILDS
> Nothing here is drawn in advance. Each layer appears when its data arrives,
> because that is genuinely the order things happen in.
>
> Just under one point six million process rows. Nine variables. Alignment.
> Features. The two models. PostgreSQL. Power BI. The operator.

→

### Beat 3 — THE DELAY IS PHYSICAL
> I want to stop here, because this is the part of the method that is easiest to
> get wrong — and it starts with the machine, not with the data.
>
> *(the marker crosses)*
>
> The dryer has a length. Material takes about twenty-four and a half minutes to
> travel it. So the sample the laboratory analyses at nine o'clock is describing
> product that entered the dryer at twenty-five to nine.
>
> And residence time is not a constant I assumed. It is one of the nine measured
> variables — it moves between twenty-four point one five and twenty-four point
> eight nine minutes across the dataset, and the runtime uses the value at each
> timestamp.

→

### Beat 4 — RESIDENCE-TIME ALIGNMENT
> Which means this. *(the wrong pairing, in red)*
>
> If I pair the process variables with the quality result at the same timestamp,
> I am describing the wrong material. Every input is therefore shifted back by
> the residence time at that moment — *(the shift)* — and the density and product
> temperature come from the previous laboratory sample, the one that was already
> on the bench when that material went in.
>
> **[GUARD]** That is what makes the model causal by construction. No future
> information reaches training or selection. If I had skipped this step, the
> numbers in the next act would look considerably better and mean nothing.

→

---

## SCENE 08 — TWO INTELLIGENCE PATHWAYS · ~68 s *(3 steps)*

### Beat 1 — THE SPLIT
> One stream of data, two models. Sixteen features go to quality, fifteen
> process-only features go to behaviour. Neither model sees the other's answer.

→

### Beat 2 — QUALITY INTELLIGENCE
> The soft sensor is a Ridge regression — alpha of ten — over sixteen
> standardised inputs. That is what you are looking at: sixteen coefficients and
> one output.
>
> I compared it against linear regression, elastic net, random forest and
> gradient boosting, tuned with time-aware cross-validation on the training
> segment only. The regularised linear model won. I did not need it to be
> complicated, and I am not going to pretend it was.

→

### Beat 3 — PROCESS INTELLIGENCE
> The second model is different in kind.
>
> This cloud is real: two thousand four hundred actual training process states,
> projected into three dimensions — which captures about ninety-four percent of
> the variance. The brighter points are the model's own hundred and thirty-six
> support vectors. They are the learned boundary.
>
> **[GUARD]** It is a One-Class SVM. It is *unsupervised*. It learned what normal
> operation looks like and nothing else. It has never been shown an anomaly, and
> there is no anomaly label anywhere in its training.

→

> *(stay on this beat — the trajectory plays here)*
>
> So "anomaly" here has a precise meaning: distance from the region the model
> learned.
>
> *(the point leaves)*
>
> This is a real recorded trajectory from the held-out period. The process state
> drifts, then departs, and the risk score follows it out.

→

> *(The trajectory used to be its own beat, reached by six units of camera
> movement — a static cut carrying six seconds of animation. It is now a
> sub-reveal inside PROCESS INTELLIGENCE.)*

---

## SCENE 09 — PROVE IT · ~98 s *(4 steps)* — **the technical core**

### Beat 1 — MOISTURE HOLD-OUT
> Evidence.
>
> One hundred and sixty-five laboratory targets from a chronological hold-out —
> the last two weeks of the record. The model never saw this period during
> training or during model selection.
>
> R-squared of point eight two. Mean absolute error of about one thousandth of a
> percentage point. RMSE about one point four thousandths.
>
> That is a modest, specific result and I will defend exactly that and nothing
> more.

→

### Beat 2 — WHY RIDGE
> This is the comparison I mentioned. Validation RMSE, five candidates, tuned on
> the training segment only. Ridge at one point three five seven thousandths,
> elastic net and linear regression essentially level with it, and both
> tree ensembles worse.
>
> On this data, with these features, the simple model won.

→

### Beat 3 — ANOMALY EVIDENCE
> And this is the anomaly result I am most confident about.
>
> This window contains a disturbance that the data generator injected — a steam
> dip, about forty-five minutes long. The shaded band is where it actually was.
>
> Mean display risk inside the event: point eight zero. Outside it: point two
> three. Of the seventy-nine points that crossed the warning line, seventy-three
> fall inside the labelled event.
>
> **[GUARD]** And I want to be precise about what that does and does not show.
> The detector is unsupervised — it never saw that label. The label exists only
> in the generator, and I am using it here purely to check where the learned
> boundary actually fired.

→

### Beat 4 — WHAT IT IS WORTH
> Which brings me to the limits, and I would rather state them than have them
> extracted from me.
>
> **[GUARD]** The dataset is synthetic. The disturbances and their labels come
> from a generator, not from a plant. The evaluation is a chronological hold-out,
> which is the right protocol, but it is a hold-out on synthetic data. Anomaly
> risk is a calibrated display score, not a probability of failure. Diagnosis
> localises evidence; it does not prove root cause.
>
> This is a working prototype with a verified analytical workflow. It is not a
> validated plant system, and I am not presenting it as one.

→

---

## SCENE 10 — THE MODEL LEAVES THE NOTEBOOK · ~76 s *(3 steps)*

### Beat 1 — THE MODEL LEAVES THE NOTEBOOK
> Here is the part I think matters most practically. *(the artifact resolves)*
>
> This is what notebook 03 wrote. `quality_moisture_pipeline.joblib`, and beside
> it the one-class model and its scaler.
>
> *(it folds into the service)*
>
> And this is `realtime_service.py`. It does not re-implement anything and it does
> not re-fit anything — it opens those exact files, once, at start. The SHA-256 of
> the artifact is recorded in the model registry, so that claim is checkable
> rather than something you have to take from me.
>
> *(inference travels to the screen)*
>
> Nine milliseconds a cycle, a new answer every five seconds — into an operator's
> screen instead of into a validation figure.
>
> **[GUARD]** This is a prototype running a replay. It is a handover, not a
> deployment, and nothing here writes back to the process.

> *(The line here used to be "the same chart", over a crossfade between the
> hold-out scatter and the report's rolling trend. They are different charts of
> different windows, so the claim was dropped rather than dressed up. What
> transfers is the ARTIFACT — and that is now something the audience watches
> happen rather than a sentence they are asked to accept.)*

→

### Beat 2 — OPERATIONS OVERVIEW
> This is the real Power BI report, reading from PostgreSQL over DirectQuery.
> The replay writes a new row every five seconds; the page itself refreshes on a
> sixty-second cycle — the pill top right says so.
>
> Predicted final moisture. The latest laboratory result beside it. The validated
> error between them — so the operator can always see how far the estimate was
> off the last time we actually knew. Current anomaly risk against the warning
> and critical lines. Process status and severity. The rolling eight-hour trend.
> The critical process variables. And the diagnosis context.
>
> **[GUARD]** This capture is a live replay state, not a mock-up: the freshness
> pill reads LIVE DATA, the anomaly score is 0.95 with severity HIGH, and the
> diagnosis and operator-guidance panels are populated because the replay was
> inside an injected disturbance when it was taken. Predicted 0.0798 %,
> laboratory 0.0752 %, validated error 0.0013 % — the same scale as the hold-out
> chart you just saw, because it is the same quantity.
>
> **[GUARD]** And say the boundary out loud: prototype, replay, advisory.

→

### Beat 3 — DIAGNOSTICS AND ROOT CAUSE
> The second page is for investigation. The risk timeline, the selected event,
> and the ranked abnormal contributors with their normalised deviation — which
> variable moved, how far, and in which direction — mapped to a likely subsystem
> and to the checks a person should actually perform.
>
> **[GUARD]** The wording on that page is deliberate: diagnostic evidence, not
> confirmed root cause. It tells the operator where to look. It does not tell
> them what is broken.

→

---

## SCENE 11 — BEHIND THE DASHBOARD · ~60 s *(3 steps)*

### Beat 1 — BEHIND THE DASHBOARD
> Rather than show you an architecture diagram, let me take you through it.
>
> Power BI reads five semantic SQL views. It never loads a model and never runs
> inference.

→

### Beat 2 — THE RUNTIME PATH
> *(we are travelling left to right, in the direction the data travels)*
>
> The replay first: the held-out test period, two hundred and thirty-seven
> thousand rows, one row every five seconds.
>
> Then one Python service that loads the exact artifacts exported by the
> notebooks — same files, verified by hash — and writes idempotently. Nine
> milliseconds average inference cycle, forty-seven maximum.
>
> Then three PostgreSQL tables. Then the five semantic views. Then Power BI,
> which reads those views and nothing else — that separation is deliberate, so
> the visualisation layer cannot silently change a result.

→

### Beat 3 — IT ENDS WITH A PERSON
> And the chain ends here.
>
> The last step is not an actuator. It is an operator reading evidence and
> deciding what, if anything, to do.
>
> **[GUARD]** Nothing in this system writes back to the process.

> *(This beat used to animate packets travelling from the runtime back INTO the
> dryer. Read as a still frame that is closed-loop control — which scene 13 then
> says does not exist. The stream now terminates at the operator terminal, and
> the visual and the disclaimer finally agree.)*

→

---

## SCENE 12 — WHAT THIS IS WORTH · ~18 s

> So what does it actually buy.
>
> More continuous moisture visibility between laboratory results. Earlier
> awareness when the multivariable behaviour of the process becomes unusual.
> Ranked, readable evidence instead of a raw alarm.
>
> *(Three claims, not four. The fourth — "supports production continuity" —
> overlapped the closing line of scene 14 and was the least defensible of the
> set. One signal travels the ring once while you say these; that is the loop's
> direction, and it is the only motion in the scene.)*
>
> **[GUARD]** What I am deliberately not claiming: any return-on-investment
> figure, any control action, and any reduction in laboratory work. The
> laboratory remains the reference and the operator remains the decision-maker.

→

---

## SCENE 13 — TODAY → NEXT · ~48 s *(2 steps)*

### Beat 1 — SOLID MEANS BUILT
> Solid means built and running.
>
> The canonical dataset and the causal alignment. Both models. The diagnosis
> engine. PostgreSQL persistence and the five semantic views. The two-page Power
> BI report. The five-second replay runtime. And thirty-three automated tests
> that hold the contracts in place.

→

### Beat 2 — OUTLINED MEANS NOT YET
> Outlined means not built.
>
> The first honest step is representative plant historian data, then data-quality
> validation on it, then shadow mode — the system running alongside the operator
> without being trusted — then a feedback loop, and only then a governed advisory
> deployment.
>
> **[GUARD]** The last two stages are dimmer for a reason. Assisted setpoint
> guidance would be conditional on that evidence, and closed-loop regulation
> would require a great deal more than this. Closed-loop control does not exist
> in this project and nothing here should suggest that it does.

→

---

## SCENE 14 — RETURN · ~32 s *(2 steps)*

### Beat 1 — MORE OF IT VISIBLE
> This is the first frame of the presentation again. The same hall, the same
> machine, the same light.
>
> *(pause — let them recognise it)*
>
> The physical process never stopped. Every one of those points is now a signal
> the system reads, and that is the whole project.

→

### Beat 2 — QUESTIONS
> From process monitoring, toward intelligent industrial operation — with a
> person in the loop at every step.
>
> Thank you. I would be glad to take your questions.

*(Do not advance further. Stay on this frame — it holds for the whole defence.)*

> *(There used to be a third beat here. Beats 2 and 3 applied the same small
> dolly twice, which walked the camera off the opening pose four seconds after
> landing on it — diluting the one rhyme the film is built to deliver. Both were
> cut; the camera now holds, and QUESTIONS is set in the hero type scale.)*

---

# TIMING PATHS

## 14-minute path (default)
Play every beat with the pauses marked.

## 12-minute path
* Scene 02: run the three beats fast — one clause each.
* Scene 04 beat 1: two sentences.
* Scene 09 beat 2 (candidate comparison): compress to *"I compared five models
  on validation RMSE and the regularised linear one won."*
* Scene 12: read the three value statements, drop the elaboration.

## 10-minute emergency path
Jump with the **`G` prefix**, then the scene key:
`G 1` → `G 4` → `G 5` → `G 6` → `G 9` → `G 0` → `G X` → `G C`
(Scene 05 and Scene 09 must never be cut — they are the problem and the
evidence. `G 0` is scene 10, the deliverable; do not cut that either.)

---

# LIKELY QUESTIONS, AND HONEST ANSWERS

**"Your R² is only 0.82 — is that good enough?"**
> For a soft sensor filling a two-hour gap, it is useful rather than definitive,
> and I would not deploy it as a release criterion. What matters more is the
> error scale: mean absolute error around one thousandth of a percentage point,
> against a target band of roughly point seven to one point one. And it is a
> chronological hold-out, so it is not flattered by leakage.

**"The data is synthetic. Does any of this transfer?"**
> The results do not transfer — the method does. What I can defend is the
> workflow: causal residence-time alignment, time-aware model selection,
> chronological evaluation, artifact hashing, contract tests, and a runtime that
> loads the exact model the notebook exported. Point that at plant historian
> data and the numbers will change. The pipeline will not have to.

**"Why not a neural network?"**
> I tried five candidates including two tree ensembles. Ridge won on validation
> RMSE. With sixteen engineered features, roughly a thousand supervised rows and
> a physically smooth relationship, there was nothing for a larger model to find
> — and a linear model gives interpretable coefficients, which matters when an
> operator has to trust the output.

**"Why One-Class SVM rather than a classifier?"**
> Because I do not have trustworthy fault labels, and in a real plant you rarely
> do. A classifier would only detect the failures someone had already labelled.
> Novelty detection asks the question you can actually answer from data: is this
> operating state unlike the normal operation I have seen? That also means it can
> flag a disturbance nobody anticipated.

**"Is the five-second rate realistic?"**
> Five seconds is the prototype replay and visualisation cadence. I have not
> verified the plant historian's acquisition rate and I do not claim it. The
> repository's own data audit records that distinction explicitly.

**"Could this control the dryer?"**
> Not as it stands, and I would not recommend it. It is advisory. There is no
> write path to the process, no interlock, no setpoint. Going further would need
> representative data, shadow-mode evidence, operator acceptance and a safety
> case — in that order.

**"What would you do differently?"**
> Two things. I would push for real historian data much earlier, because it
> changes what features are even available. And I would build the diagnosis
> evaluation more rigorously — right now I can show the detector fires in the
> right window, but I cannot yet quantify how often its ranked contributors
> point a person at the right subsystem.
