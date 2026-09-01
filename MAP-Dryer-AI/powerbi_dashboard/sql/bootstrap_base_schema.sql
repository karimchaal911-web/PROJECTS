-- ============================================================================
-- Base schema bootstrap for the MAP_DRYER database.
--
-- The production database was created by hand on the original machine and
-- its DDL never lived in the repository. This file reconstructs exactly the
-- objects the pipeline code calls, so a fresh environment can run the whole
-- prototype. Idempotent: safe to run repeatedly.
--
-- Apply with:  python realtime_pipeline/src/bootstrap_database.py
-- (which runs this file and then powerbi_dashboard/sql/upgrade_5s_schema.sql)
--
-- Naming notes confirmed from the pipeline sources:
--   * dryer_map quality columns are NULL between laboratory samples — that
--     is the multi-rate contract, not missing data.
--   * The airflow column is "Air Flow Rate " WITH a trailing space (the CSV
--     column has none; the historical SQL column does).
--   * All writes go through the four functions below, keyed on
--     ("Date","Time") with ON CONFLICT upserts — retried rows can never
--     duplicate.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.dryer_map (
    "Date" date NOT NULL,
    "Time" time NOT NULL,
    "Dryer Air Temperature" double precision,
    "Cooler Air Temperature" double precision,
    "Air Flow Rate " double precision,
    "Wet Product Feed Rate" double precision,
    "Product Inlet Temperature" double precision,
    "Residence Time" double precision,
    "Vacuum" double precision,
    "Steam Pressure" double precision,
    "Fan Speed" double precision,
    "Product Density" double precision,
    "Final Product Temp" double precision,
    "Final Moisture (%H2O)" double precision,
    PRIMARY KEY ("Date", "Time")
);

CREATE TABLE IF NOT EXISTS public.dryer_model_outputs (
    "Date" date NOT NULL,
    "Time" time NOT NULL,
    "Predicted Final Moisture" double precision,
    "Prediction Confidence" double precision,
    "Anomaly Score" double precision,
    "Anomaly Detected" boolean,
    "Severity" varchar(40),
    "Likely Subsystem" text,
    "Probable Diagnosis" text,
    "Possible Causes" text,
    "Diagnosis Confidence" double precision,
    "Recommended Verification" text,
    PRIMARY KEY ("Date", "Time")
);

CREATE TABLE IF NOT EXISTS public.dryer_abnormal_variables (
    event_date date NOT NULL,
    event_time time NOT NULL,
    contribution_rank integer NOT NULL,
    feature_name text NOT NULL,
    observed_value double precision,
    reference_center double precision,
    reference_scale double precision,
    lower_normal_limit double precision,
    upper_normal_limit double precision,
    signed_deviation double precision,
    deviation_percent double precision,
    contribution_score double precision,
    deviation_direction text,
    is_direct_process_feature boolean,
    variable_severity text
);

CREATE INDEX IF NOT EXISTS ix_dryer_abnormal_variables_event
    ON public.dryer_abnormal_variables (event_date, event_time);

-- ----------------------------------------------------------------------------
-- Write functions. Python never touches the difficult quoted identifiers;
-- every writer is an idempotent upsert keyed on ("Date","Time").
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.insert_dryer_observation(
    p_date date,
    p_time time,
    p_dryer_air_temperature double precision,
    p_cooler_air_temperature double precision,
    p_air_flow_rate double precision,
    p_wet_product_feed_rate double precision,
    p_product_inlet_temperature double precision,
    p_residence_time double precision,
    p_vacuum double precision,
    p_steam_pressure double precision,
    p_fan_speed double precision,
    p_product_density double precision,
    p_final_product_temp double precision,
    p_final_moisture double precision
) RETURNS void
LANGUAGE sql
AS $$
    INSERT INTO public.dryer_map (
        "Date", "Time",
        "Dryer Air Temperature", "Cooler Air Temperature", "Air Flow Rate ",
        "Wet Product Feed Rate", "Product Inlet Temperature", "Residence Time",
        "Vacuum", "Steam Pressure", "Fan Speed",
        "Product Density", "Final Product Temp", "Final Moisture (%H2O)"
    )
    VALUES (
        p_date, p_time,
        p_dryer_air_temperature, p_cooler_air_temperature, p_air_flow_rate,
        p_wet_product_feed_rate, p_product_inlet_temperature, p_residence_time,
        p_vacuum, p_steam_pressure, p_fan_speed,
        p_product_density, p_final_product_temp, p_final_moisture
    )
    ON CONFLICT ("Date", "Time") DO UPDATE SET
        "Dryer Air Temperature"     = EXCLUDED."Dryer Air Temperature",
        "Cooler Air Temperature"    = EXCLUDED."Cooler Air Temperature",
        "Air Flow Rate "            = EXCLUDED."Air Flow Rate ",
        "Wet Product Feed Rate"     = EXCLUDED."Wet Product Feed Rate",
        "Product Inlet Temperature" = EXCLUDED."Product Inlet Temperature",
        "Residence Time"            = EXCLUDED."Residence Time",
        "Vacuum"                    = EXCLUDED."Vacuum",
        "Steam Pressure"            = EXCLUDED."Steam Pressure",
        "Fan Speed"                 = EXCLUDED."Fan Speed",
        "Product Density"           = EXCLUDED."Product Density",
        "Final Product Temp"        = EXCLUDED."Final Product Temp",
        "Final Moisture (%H2O)"     = EXCLUDED."Final Moisture (%H2O)";
$$;

CREATE OR REPLACE FUNCTION public.upsert_moisture_output(
    p_date date,
    p_time time,
    p_predicted_final_moisture double precision,
    p_prediction_confidence double precision
) RETURNS void
LANGUAGE sql
AS $$
    INSERT INTO public.dryer_model_outputs (
        "Date", "Time", "Predicted Final Moisture", "Prediction Confidence"
    )
    VALUES (p_date, p_time, p_predicted_final_moisture, p_prediction_confidence)
    ON CONFLICT ("Date", "Time") DO UPDATE SET
        "Predicted Final Moisture" = EXCLUDED."Predicted Final Moisture",
        "Prediction Confidence"    = EXCLUDED."Prediction Confidence";
$$;

CREATE OR REPLACE FUNCTION public.upsert_anomaly_output(
    p_date date,
    p_time time,
    p_anomaly_score double precision,
    p_anomaly_detected boolean,
    p_severity varchar
) RETURNS void
LANGUAGE sql
AS $$
    INSERT INTO public.dryer_model_outputs (
        "Date", "Time", "Anomaly Score", "Anomaly Detected", "Severity"
    )
    VALUES (p_date, p_time, p_anomaly_score, p_anomaly_detected, p_severity)
    ON CONFLICT ("Date", "Time") DO UPDATE SET
        "Anomaly Score"    = EXCLUDED."Anomaly Score",
        "Anomaly Detected" = EXCLUDED."Anomaly Detected",
        "Severity"         = EXCLUDED."Severity";
$$;

CREATE OR REPLACE FUNCTION public.upsert_diagnosis_output(
    p_date date,
    p_time time,
    p_severity varchar,
    p_likely_subsystem text,
    p_probable_diagnosis text,
    p_possible_causes text,
    p_diagnosis_confidence double precision,
    p_recommended_verification text
) RETURNS void
LANGUAGE sql
AS $$
    INSERT INTO public.dryer_model_outputs (
        "Date", "Time", "Severity", "Likely Subsystem", "Probable Diagnosis",
        "Possible Causes", "Diagnosis Confidence", "Recommended Verification"
    )
    VALUES (
        p_date, p_time, p_severity, p_likely_subsystem, p_probable_diagnosis,
        p_possible_causes, p_diagnosis_confidence, p_recommended_verification
    )
    ON CONFLICT ("Date", "Time") DO UPDATE SET
        "Severity"                 = EXCLUDED."Severity",
        "Likely Subsystem"         = EXCLUDED."Likely Subsystem",
        "Probable Diagnosis"       = EXCLUDED."Probable Diagnosis",
        "Possible Causes"          = EXCLUDED."Possible Causes",
        "Diagnosis Confidence"     = EXCLUDED."Diagnosis Confidence",
        "Recommended Verification" = EXCLUDED."Recommended Verification";
$$;

-- ----------------------------------------------------------------------------
-- Compatibility view kept for insert_one_row.py and the pre-5s tooling.
-- Column order matches the historical 26-column dashboard view.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW public.vw_dryer_dashboard_v2 AS
SELECT
    d."Date",
    d."Time",
    (d."Date" + d."Time") AS "Event Timestamp",
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
    (d."Date" + d."Time") AS "Timestamp"
FROM public.dryer_map AS d
LEFT JOIN public.dryer_model_outputs AS m
    ON d."Date" = m."Date"
   AND d."Time" = m."Time";

-- ----------------------------------------------------------------------------
-- Ranked-contributor view consumed by the Power BI semantic model
-- (sourceColumn names are the snake_case physical names plus "Timestamp").
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW public.vw_dryer_contributors_powerbi AS
SELECT
    (v.event_date + v.event_time)::timestamp AS "Timestamp",
    v.contribution_rank,
    v.feature_name,
    v.observed_value,
    v.reference_center,
    v.reference_scale,
    v.lower_normal_limit,
    v.upper_normal_limit,
    v.signed_deviation,
    v.deviation_percent,
    v.contribution_score,
    v.deviation_direction,
    v.is_direct_process_feature,
    v.variable_severity
FROM public.dryer_abnormal_variables AS v;
