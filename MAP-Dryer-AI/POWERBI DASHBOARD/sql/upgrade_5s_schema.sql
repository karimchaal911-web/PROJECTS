-- ============================================================================
-- 5-second multi-rate upgrade for the MAP dryer PostgreSQL layer.
--
-- Idempotent: safe to run repeatedly. Apply with
--     python realtime_pipeline/src/apply_sql_migration.py
--
-- What it does
--   1. Extends public.dryer_model_outputs with model/version/latency columns
--      and the calibrated 0-1 "Anomaly Risk".
--   2. Adds the Timestamp expression index required by the incremental
--      5-second service, plus a partial index for laboratory as-of lookups.
--   3. Extends public.vw_dryer_dashboard_powerbi IN PLACE: the 26 existing
--      columns keep their exact names, order and values (Power BI
--      relationships stay valid); new columns are appended at the end,
--      which PostgreSQL allows through CREATE OR REPLACE VIEW.
--   4. Creates vw_dryer_lab_samples (actual laboratory samples + validated
--      model performance), a lightweight rolling-eight-hour overview trend,
--      and vw_dryer_anomaly_events (consecutive anomalous rows grouped into
--      operator-facing events).
--   5. Refreshes vw_dryer_latest as the one-row latest joined state.
--
-- Laboratory semantics: quality columns in dryer_map are only non-NULL on
-- rows where a sparse represented laboratory observation exists. The "Latest Lab *" columns
-- are a backward as-of join for DISPLAY; they are never written back into
-- process rows and never used as training targets.
-- ============================================================================

ALTER TABLE public.dryer_model_outputs
    ADD COLUMN IF NOT EXISTS "Anomaly Risk" double precision,
    ADD COLUMN IF NOT EXISTS "Model Version" varchar(40),
    ADD COLUMN IF NOT EXISTS "Feature Schema Version" varchar(40),
    ADD COLUMN IF NOT EXISTS "Inference Timestamp" timestamp,
    ADD COLUMN IF NOT EXISTS "Inference Latency Ms" double precision;

-- Timestamp expression index: used by the incremental service
-- (MAX("Date"+"Time")) and by every as-of/lateral lookup below.
CREATE INDEX IF NOT EXISTS ix_dryer_map_timestamp
    ON public.dryer_map ((("Date" + "Time")));

-- Laboratory rows are ~1/1440 of all rows; a partial expression index makes
-- the backward as-of LATERAL join an index-only descent.
CREATE INDEX IF NOT EXISTS ix_dryer_map_lab_timestamp
    ON public.dryer_map ((("Date" + "Time")))
    WHERE "Final Moisture (%H2O)" IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_dryer_model_outputs_timestamp
    ON public.dryer_model_outputs ((("Date" + "Time")));

-- Versioned rows are the authoritative 5-second stream. This partial index
-- makes restart position and latest-state lookups independent of any retained
-- legacy one-minute rows.
CREATE INDEX IF NOT EXISTS ix_dryer_model_outputs_canonical_v6_timestamp
    ON public.dryer_model_outputs ((("Date" + "Time")))
    WHERE "Model Version" = 'canonical_92d_v6.0';

-- Diagnostics page queries only anomalous rows. Keep event-building scans off
-- the full five-second history during page switches and refresh cycles.
CREATE INDEX IF NOT EXISTS ix_dryer_model_outputs_anomaly_v6_timestamp
    ON public.dryer_model_outputs ((("Date" + "Time")))
    WHERE "Anomaly Detected" IS TRUE
      AND "Model Version" = 'canonical_92d_v6.0';

-- ----------------------------------------------------------------------------
-- Extended dashboard view. Columns 1-26 are byte-identical to the previous
-- definition (previously SELECTed through vw_dryer_dashboard_v2); columns
-- 27+ are new.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.vw_dryer_dashboard_powerbi AS
SELECT
    d."Date",
    d."Time",
    (d."Date" + d."Time")                                  AS "Event Timestamp",
    d."Dryer Air Temperature",
    d."Cooler Air Temperature",
    d."Air Flow Rate ",
    d."Wet Product Feed Rate",
    d."Product Inlet Temperature",
    d."Residence Time",
    d."Vacuum",
    d."Steam Pressure",
    d."Fan Speed",
    d."Product Density",
    d."Final Product Temp",
    d."Final Moisture (%H2O)",
    m."Predicted Final Moisture",
    m."Prediction Confidence",
    m."Anomaly Score",
    m."Anomaly Detected",
    m."Severity",
    m."Likely Subsystem",
    m."Probable Diagnosis",
    m."Possible Causes",
    m."Diagnosis Confidence",
    m."Recommended Verification",
    (d."Date" + d."Time")                                  AS "Timestamp",
    m."Anomaly Risk",
    m."Model Version",
    m."Feature Schema Version",
    m."Inference Timestamp",
    m."Inference Latency Ms",
    lab.lab_timestamp                                      AS "Latest Lab Sample Timestamp",
    lab.lab_density                                        AS "Latest Lab Product Density",
    lab.lab_product_temp                                   AS "Latest Lab Final Product Temp",
    lab.lab_moisture                                       AS "Latest Lab Final Moisture",
    EXTRACT(
        EPOCH FROM ((d."Date" + d."Time") - lab.lab_timestamp)
    ) / 60.0                                               AS "Lab Result Age Min",
    (lab.lab_timestamp IS NOT NULL)                        AS "Lab Sample Available",
    (d."Final Moisture (%H2O)" IS NOT NULL)                AS "Is Lab Sample",
    CASE
        WHEN d."Final Moisture (%H2O)" IS NOT NULL
         AND m."Predicted Final Moisture" IS NOT NULL
        THEN m."Predicted Final Moisture" - d."Final Moisture (%H2O)"
    END                                                    AS "Validated Moisture Error",
    CASE
        WHEN d."Final Moisture (%H2O)" IS NOT NULL
         AND m."Predicted Final Moisture" IS NOT NULL
        THEN ABS(m."Predicted Final Moisture" - d."Final Moisture (%H2O)")
    END                                                    AS "Validated Absolute Error"
FROM public.dryer_map AS d
LEFT JOIN public.dryer_model_outputs AS m
    ON d."Date" = m."Date"
   AND d."Time" = m."Time"
LEFT JOIN LATERAL (
    SELECT
        (l."Date" + l."Time")      AS lab_timestamp,
        l."Product Density"        AS lab_density,
        l."Final Product Temp"     AS lab_product_temp,
        l."Final Moisture (%H2O)"  AS lab_moisture
    FROM public.dryer_map AS l
    WHERE l."Final Moisture (%H2O)" IS NOT NULL
      AND (l."Date" + l."Time") <= (d."Date" + d."Time")
    ORDER BY (l."Date" + l."Time") DESC
    LIMIT 1
) AS lab ON TRUE
WHERE m."Model Version" = 'canonical_92d_v6.0';

-- Contributor evidence must belong to the same active runtime contract as the
-- dashboard row. Older rows remain auditable in base tables but are not mixed
-- into the operator-facing semantic model.
CREATE OR REPLACE VIEW public.vw_dryer_contributors_powerbi AS
SELECT
    v.*,
    (v.event_date + v.event_time)::timestamp AS "Timestamp"
FROM public.dryer_abnormal_variables AS v
JOIN public.dryer_model_outputs AS m
    ON v.event_date = m."Date"
   AND v.event_time = m."Time"
WHERE m."Model Version" = 'canonical_92d_v6.0';

-- ----------------------------------------------------------------------------
-- Actual laboratory samples with validated model performance at each sample.
-- Row count equals the number of laboratory analyses, never process rows.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.vw_dryer_lab_samples AS
SELECT
    (d."Date" + d."Time")                                  AS "Sample Timestamp",
    d."Product Density",
    d."Final Product Temp",
    d."Final Moisture (%H2O)"                              AS "Laboratory Moisture",
    m."Predicted Final Moisture"                           AS "Predicted Moisture At Sample",
    CASE
        WHEN m."Predicted Final Moisture" IS NOT NULL
        THEN m."Predicted Final Moisture" - d."Final Moisture (%H2O)"
    END                                                    AS "Validated Error",
    CASE
        WHEN m."Predicted Final Moisture" IS NOT NULL
        THEN ABS(m."Predicted Final Moisture" - d."Final Moisture (%H2O)")
    END                                                    AS "Validated Absolute Error",
    LAG(d."Date" + d."Time") OVER (ORDER BY (d."Date" + d."Time"))
                                                           AS "Previous Sample Timestamp"
FROM public.dryer_map AS d
JOIN public.dryer_model_outputs AS m
    ON d."Date" = m."Date"
   AND d."Time" = m."Time"
WHERE d."Final Moisture (%H2O)" IS NOT NULL
  AND m."Model Version" = 'canonical_92d_v6.0';

-- ----------------------------------------------------------------------------
-- Lightweight overview trend. This avoids executing the dashboard view's
-- laboratory as-of lookup for thousands of chart points. The fixed eight-hour
-- window is anchored to the latest versioned event timestamp, not NOW(), so a
-- historical replay remains visible and deterministic.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.vw_dryer_overview_trends_powerbi AS
WITH latest AS (
    SELECT MAX("Date" + "Time") AS latest_timestamp
    FROM public.dryer_model_outputs
    WHERE "Model Version" = 'canonical_92d_v6.0'
)
SELECT
    (d."Date" + d."Time")                                  AS "Timestamp",
    m."Predicted Final Moisture",
    d."Final Moisture (%H2O)"                              AS "Laboratory Moisture",
    m."Anomaly Risk",
    m."Anomaly Detected",
    d."Dryer Air Temperature",
    d."Wet Product Feed Rate",
    d."Steam Pressure",
    d."Air Flow Rate "                                     AS "Air Flow Rate",
    d."Vacuum"
FROM public.dryer_model_outputs AS m
JOIN public.dryer_map AS d
    ON d."Date" = m."Date"
   AND d."Time" = m."Time"
CROSS JOIN latest
WHERE m."Model Version" = 'canonical_92d_v6.0'
  AND (d."Date" + d."Time")
      > latest.latest_timestamp - INTERVAL '8 hours';

-- ----------------------------------------------------------------------------
-- Operator-facing anomaly events: consecutive anomalous 5-second rows are
-- one event while the gap between flags stays within 30 seconds. Severity,
-- subsystem and diagnosis come from the event's peak-risk row. The raw
-- "Peak Anomaly Score" is the One-Class SVM decision function (lower =
-- worse); "Peak Anomaly Risk" is the calibrated 0-1 display risk.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.vw_dryer_anomaly_events AS
WITH anomalous AS (
    SELECT
        ("Date" + "Time")          AS ts,
        "Anomaly Score"            AS score,
        "Anomaly Risk"             AS risk,
        "Severity"                 AS severity,
        "Likely Subsystem"         AS subsystem,
        "Probable Diagnosis"       AS diagnosis,
        "Possible Causes"          AS causes,
        "Recommended Verification" AS verification,
        "Predicted Final Moisture" AS predicted_moisture
    FROM public.dryer_model_outputs
    WHERE "Anomaly Detected" IS TRUE
      AND "Model Version" = 'canonical_92d_v6.0'
),
flagged AS (
    SELECT
        anomalous.*,
        CASE
            WHEN ts - LAG(ts) OVER (ORDER BY ts) <= INTERVAL '30 seconds'
            THEN 0
            ELSE 1
        END AS is_new_event
    FROM anomalous
),
grouped AS (
    SELECT
        flagged.*,
        SUM(is_new_event) OVER (ORDER BY ts) AS event_id
    FROM flagged
),
peaks AS (
    SELECT DISTINCT ON (event_id)
        event_id,
        ts                  AS peak_timestamp,
        score               AS peak_score,
        risk                AS peak_risk,
        severity            AS peak_severity,
        subsystem           AS peak_subsystem,
        diagnosis           AS peak_diagnosis,
        causes              AS peak_causes,
        verification        AS peak_verification,
        predicted_moisture  AS peak_predicted_moisture
    FROM grouped
    ORDER BY event_id, risk DESC NULLS LAST, score ASC, ts ASC
)
SELECT
    g.event_id                                             AS "Event ID",
    MIN(g.ts)                                              AS "Event Start",
    MAX(g.ts)                                              AS "Event End",
    ROUND(
        (EXTRACT(EPOCH FROM (MAX(g.ts) - MIN(g.ts))) + 5.0) / 60.0,
        2
    )::double precision                                    AS "Duration Min",
    COUNT(*)::int                                          AS "Rows In Event",
    p.peak_timestamp                                       AS "Peak Timestamp",
    p.peak_score                                           AS "Peak Anomaly Score",
    p.peak_risk                                            AS "Peak Anomaly Risk",
    p.peak_severity                                        AS "Severity",
    p.peak_subsystem                                       AS "Subsystem",
    p.peak_diagnosis                                       AS "Diagnosis",
    p.peak_causes                                          AS "Possible Causes",
    p.peak_verification                                    AS "Recommended Verification",
    p.peak_predicted_moisture                              AS "Predicted Moisture At Peak"
FROM grouped AS g
JOIN peaks AS p USING (event_id)
GROUP BY
    g.event_id,
    p.peak_timestamp,
    p.peak_score,
    p.peak_risk,
    p.peak_severity,
    p.peak_subsystem,
    p.peak_diagnosis,
    p.peak_causes,
    p.peak_verification,
    p.peak_predicted_moisture;

-- ----------------------------------------------------------------------------
-- One-row latest joined state (KPI cards, freshness checks, smoke tests).
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS public.vw_dryer_latest;
CREATE VIEW public.vw_dryer_latest AS
SELECT *
FROM public.vw_dryer_dashboard_powerbi
ORDER BY "Timestamp" DESC
LIMIT 1;
