# FULL SPOKEN SCRIPT

**14 scenes · 35 presenter steps · target 13–14 minutes**

Read naturally, not from the page. Every number here is verified — see
`design/RESOURCE_AUDIT.md` for provenance. Where a sentence is marked
**[GUARD]**, say it: those are the honesty statements the jury will otherwise
have to extract from you under questioning.

`→` marks a press of the right arrow.

---

## SCENE 01 — AWAKENING · ~50 s

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

## SCENE 02 — WHY THIS MATERIAL · ~35 s

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

## SCENE 03 — FOLLOW THE MATERIAL · ~60 s

> Let me show you where it comes from.
>
> Phosphoric acid is pretreated. Ammonia is vaporised. They react — and that
> reaction is the whole chemistry of this plant. The solution is buffered,
> concentrated, crystallised, and the crystals are separated from the mother
> liquor by centrifugation.
>
> Then they are dried. Then cooled and conditioned.
>
> Two things to notice. First, this is continuous — material is at every stage
> simultaneously. Second, it is *coupled*: the mother liquor goes back to
> neutralization, and the buffer tanks deliberately mix and delay disturbances.
>
> **[GUARD]** So when final moisture drifts, you cannot assume the dryer caused
> it. That is a diagnosis problem, and I will come back to it.

→

---

## SCENE 04 — ENTER THE DRYER · ~75 s *(3 steps)*

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

## SCENE 05 — THE VISIBILITY GAP · ~80 s *(3 steps)* — **the centre of the talk**

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
> The process never stops. Laboratory visibility does.
>
> And this is not a theoretical concern. Between those two results the product
> actually moved by five thousandths of a percentage point — a real change, in
> real product that was really packed and shipped, and nothing measured it while
> it happened.

→

---

## SCENE 06 — THE ENGINEERING RESPONSE · ~60 s *(3 steps)*

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

### Beat 3 — TWO QUESTIONS
> But filling that gap answers only one question — what is the moisture likely to
> be right now.
>
> There is a second, different question: is the process behaving unusually at
> all? Those are not the same question, they need different models, and the
> system answers both.

→

---

## SCENE 07 — PHYSICAL BECOMES DIGITAL · ~70 s *(3 steps)*

### Beat 1 — SENSORS
> Let me show you how the process becomes data.

→

### Beat 2 — THE STACK BUILDS
> Nothing here is drawn in advance. Each layer appears when its data arrives,
> because that is genuinely the order things happen in.
>
> Just under one point six million process rows. Nine variables. Alignment.
> Features. The two models. PostgreSQL. Power BI. The operator.

→

### Beat 3 — RESIDENCE-TIME ALIGNMENT
> And I want to stop on this layer, because it is the part of the method that is
> easiest to get wrong.
>
> *(the packet waits)*
>
> The product being sampled now left the dryer roughly twenty-four and a half
> minutes ago. So the model must not read the process as it is now — it must
> read the process as it was then, plus the most recent laboratory result that
> was already available at that moment.
>
> **[GUARD]** This is what makes the model causal by construction. No future
> information reaches training or selection. If I had skipped this, the results
> later would look far better and mean nothing.

→

---

## SCENE 08 — TWO INTELLIGENCE PATHWAYS · ~80 s *(4 steps)*

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

### Beat 4 — LEAVING THE REGION
> So "anomaly" here has a precise meaning: distance from the region the model
> learned.
>
> *(the point leaves)*
>
> This is a real recorded trajectory from the held-out period. The process state
> drifts, then departs, and the risk score follows it out.

→

---

## SCENE 09 — PROVE IT · ~90 s *(4 steps)* — **the technical core**

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

## SCENE 10 — VALIDATION BECOMES SUPERVISION · ~65 s *(3 steps)*

### Beat 1 — THE CHART BECOMES THE VISUAL
> Here is the part I think matters most practically.
>
> That hold-out trend is not a figure I made for a report. It is already the
> visual an operator reads.

→

### Beat 2 — OPERATIONS OVERVIEW
> This is the real Power BI report, reading live from PostgreSQL over
> DirectQuery, refreshing about every five seconds.
>
> Predicted final moisture. The latest laboratory result beside it. The validated
> error between them — so the operator can always see how far the estimate was
> off the last time we actually knew. Current anomaly risk against the warning
> and critical lines. Process status and severity. The rolling eight-hour trend.
> The critical process variables. And the diagnosis context.
>
> **[GUARD]** Note the prototype-replay indicator, top right. That is on the real
> screen, deliberately, so this can never be mistaken for a live plant historian.

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

## SCENE 11 — THROUGH THE DASHBOARD · ~65 s *(3 steps)*

### Beat 1 — BEHIND THE PLANE
> Rather than show you an architecture diagram, let me take you through it.

→

### Beat 2 — THE RUNTIME
> Power BI reads five semantic SQL views. It never loads a model file and never
> runs inference — that separation is deliberate, so the visualisation layer
> cannot silently change a result.
>
> Behind the views, three PostgreSQL tables. Behind those, one Python service
> that loads the exact artifacts exported by the notebooks — same files, verified
> by hash — and writes idempotently. Nine milliseconds average inference cycle,
> forty-seven maximum.
>
> And behind that, the replay: the held-out test period, two hundred and
> thirty-seven thousand rows, one row every five seconds.

→

### Beat 3 — THE LOOP CLOSES
> And the replay leads back to the process it describes.
>
> That is the whole system in one frame. It runs end to end, today, on one
> machine, with one command.

→

---

## SCENE 12 — WHAT THIS IS WORTH · ~50 s

> So what does it actually buy.
>
> More continuous moisture visibility between laboratory results. Earlier
> awareness when the multivariable behaviour of the process becomes unusual.
> Ranked, readable evidence instead of a raw alarm. And a supervision layer that
> supports production continuity.
>
> **[GUARD]** What I am deliberately not claiming: any return-on-investment
> figure, any control action, and any reduction in laboratory work. The
> laboratory remains the reference and the operator remains the decision-maker.

→

---

## SCENE 13 — TODAY → NEXT · ~55 s *(2 steps)*

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

## SCENE 14 — RETURN · ~45 s *(3 steps)*

### Beat 1 — MORE OF IT VISIBLE
> This is the first frame of the presentation again. The same hall, the same
> machine, the same light.
>
> The physical process never stopped. Digitalization made more of it visible.

→

### Beat 2 — FROM MONITORING TO OPERATION
> That is the direction this work points in: from process monitoring, toward
> intelligent industrial operation — with a person in the loop at every step.

→

### Beat 3 — QUESTIONS
> Thank you. I would be glad to take your questions.

*(Do not advance further. Stay on this frame.)*

---

# TIMING PATHS

## 14-minute path (default)
Play every beat with the pauses marked.

## 12-minute path
* Scene 02: one sentence, skip the product specification.
* Scene 04 beat 1: two sentences.
* Scene 09 beat 2 (candidate comparison): compress to *"I compared five models
  on validation RMSE and the regularised linear one won."*
* Scene 12: read the four value statements, drop the elaboration.

## 10-minute emergency path
Press `1` … then jump directly with the number keys:
`1` → `4` → `5` → `6` → `9` → `10` → `13` → `14`
(Scene 05 and Scene 09 must never be cut — they are the problem and the
evidence.)

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
