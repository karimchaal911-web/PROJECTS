-- ============================================================================
-- Reference DDL for the two Power BI-ready views.
--
-- RUN THIS ONLY IF verify_powerbi_views.py REPORTS THAT A VIEW IS MISSING.
-- The realtime_pipeline database normally already contains both views; do not
-- replace an existing, working view.
--
-- Column names on the LEFT of each AS are the physical base-table columns
-- confirmed from realtime_pipeline source code. Note that the dryer_map
-- airflow column is "Air Flow Rate " WITH a trailing space (the CSV column
-- has no trailing space, the SQL column does).
--
-- The alias names on the RIGHT are the exact names the Power BI semantic
-- model expects (sourceColumn values in the .SemanticModel TMDL files).
-- If your existing views expose different names, prefer editing the TMDL
-- sourceColumn lines instead of dropping views.
--
-- PostgreSQL refuses CREATE OR REPLACE VIEW when the column list changes.
-- That is intentional protection: investigate before dropping.
-- ============================================================================

CREATE OR REPLACE VIEW public.vw_dryer_dashboard_powerbi AS
SELECT
    (d."Date" + d."Time")::timestamp                       AS "Timestamp",
    m."Predicted Final Moisture"                           AS "Predicted Moisture",
    d."Final Moisture (%H2O)"                              AS "Laboratory Moisture",
    CASE
        WHEN m."Predicted Final Moisture" IS NULL
          OR d."Final Moisture (%H2O)" IS NULL THEN NULL
        ELSE m."Predicted Final Moisture" - d."Final Moisture (%H2O)"
    END                                                    AS "Moisture Error",
    CASE
        WHEN m."Predicted Final Moisture" IS NULL
          OR d."Final Moisture (%H2O)" IS NULL THEN NULL
        ELSE ABS(m."Predicted Final Moisture" - d."Final Moisture (%H2O)")
    END                                                    AS "Absolute Moisture Error",
    m."Anomaly Score"                                      AS "Anomaly Score",
    CASE
        WHEN m."Anomaly Detected" IS NULL THEN 'UNCLASSIFIED'
        WHEN m."Anomaly Detected" THEN 'ANOMALY'
        ELSE 'NORMAL'
    END                                                    AS "Anomaly Status",
    COALESCE(m."Severity", 'UNCLASSIFIED')                 AS "Severity",
    m."Likely Subsystem"                                   AS "Subsystem",
    m."Probable Diagnosis"                                 AS "Diagnosis",
    m."Possible Causes"                                    AS "Possible Causes",
    m."Recommended Verification"                           AS "Recommended Verification",
    d."Dryer Air Temperature"                              AS "Dryer Air Temperature",
    d."Cooler Air Temperature"                             AS "Cooler Air Temperature",
    d."Air Flow Rate "                                     AS "Air Flow Rate",
    d."Wet Product Feed Rate"                              AS "Wet Product Feed Rate",
    d."Product Inlet Temperature"                          AS "Product Inlet Temperature",
    d."Residence Time"                                     AS "Residence Time",
    d."Vacuum"                                             AS "Vacuum",
    d."Steam Pressure"                                     AS "Steam Pressure",
    d."Fan Speed"                                          AS "Fan Speed",
    d."Product Density"                                    AS "Product Density",
    d."Final Product Temp"                                 AS "Final Product Temperature"
FROM public.dryer_map AS d
LEFT JOIN public.dryer_model_outputs AS m
    ON d."Date" = m."Date"
   AND d."Time" = m."Time";

-- NOTE: the five diagnosis columns of dryer_model_outputs are written through
-- public.upsert_diagnosis_output(...) and their physical names never appear in
-- the Python sources. The names used above follow the table's confirmed
-- TitleCase convention ("Predicted Final Moisture", "Anomaly Score",
-- "Anomaly Detected", "Severity"). If \d public.dryer_model_outputs shows
-- different diagnosis column names, adjust only those references.

CREATE OR REPLACE VIEW public.vw_dryer_contributors_powerbi AS
SELECT
    (v.event_date + v.event_time)::timestamp               AS "Timestamp",
    v.contribution_rank                                    AS "Contributor Rank",
    v.feature_name                                         AS "Contributor Name",
    v.observed_value                                       AS "Observed Value",
    v.signed_deviation                                     AS "Signed Deviation",
    v.deviation_percent                                    AS "Deviation Percent",
    v.contribution_score                                   AS "Contribution Score",
    v.deviation_direction                                  AS "Deviation Direction",
    v.variable_severity                                    AS "Variable Severity"
FROM public.dryer_abnormal_variables AS v;
