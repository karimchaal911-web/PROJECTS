-- OPTIONAL EXAMPLE ONLY. This file is not executed by bootstrap_database.py.
-- Review with the database owner before running. It creates NOLOGIN group
-- roles and does not contain or alter credentials.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'map_dryer_runtime') THEN
        CREATE ROLE map_dryer_runtime NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'map_dryer_powerbi_readonly') THEN
        CREATE ROLE map_dryer_powerbi_readonly NOLOGIN;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE "MAP_DRYER" TO map_dryer_runtime;
GRANT USAGE ON SCHEMA public TO map_dryer_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON
    public.dryer_map,
    public.dryer_model_outputs,
    public.dryer_abnormal_variables
TO map_dryer_runtime;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO map_dryer_runtime;

GRANT CONNECT ON DATABASE "MAP_DRYER" TO map_dryer_powerbi_readonly;
GRANT USAGE ON SCHEMA public TO map_dryer_powerbi_readonly;
GRANT SELECT ON
    public.vw_dryer_dashboard_powerbi,
    public.vw_dryer_overview_trends_powerbi,
    public.vw_dryer_lab_samples,
    public.vw_dryer_anomaly_events,
    public.vw_dryer_contributors_powerbi,
    public.vw_dryer_latest
TO map_dryer_powerbi_readonly;

-- A database administrator may create separate LOGIN roles and grant one of
-- these group roles. Supply passwords through the organization's secret
-- mechanism; never add them to this repository.
