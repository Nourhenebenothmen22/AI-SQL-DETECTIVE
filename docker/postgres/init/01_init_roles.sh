#!/usr/bin/env bash
set -euo pipefail

# Provision strictly isolated PostgreSQL 16 schemas and least-privilege roles:
#   1. sql_detective_migrator : Owns ecommerce & app_meta schemas (Alembic + seed only)
#   2. sql_detective_ro       : Read-only SELECT on ecommerce ONLY; zero access to app_meta
#   3. sql_detective_app      : Scoped SELECT/INSERT/UPDATE on app_meta ONLY; zero access to ecommerce

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${PG_MIGRATOR_USER:=sql_detective_migrator}"
: "${PG_MIGRATOR_PASSWORD:?PG_MIGRATOR_PASSWORD is required}"
: "${PG_RO_USER:=sql_detective_ro}"
: "${PG_RO_PASSWORD:?PG_RO_PASSWORD is required}"
: "${PG_APP_USER:=sql_detective_app}"
: "${PG_APP_PASSWORD:?PG_APP_PASSWORD is required}"
: "${SQL_STATEMENT_TIMEOUT_MS:=5000}"

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  -v db_name="$POSTGRES_DB" \
  -v migrator_user="$PG_MIGRATOR_USER" \
  -v migrator_pw="$PG_MIGRATOR_PASSWORD" \
  -v ro_user="$PG_RO_USER" \
  -v ro_pw="$PG_RO_PASSWORD" \
  -v app_user="$PG_APP_USER" \
  -v app_pw="$PG_APP_PASSWORD" \
  -v stmt_timeout="${SQL_STATEMENT_TIMEOUT_MS}ms" <<'EOSQL'
-- 1. Lock down default PUBLIC privileges
REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 2. Create roles idempotently
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT', :'migrator_user', :'migrator_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'migrator_user')\gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT', :'ro_user', :'ro_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'ro_user')\gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT', :'app_user', :'app_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user')\gexec

-- 3. Create isolated schemas owned by migrator
CREATE SCHEMA IF NOT EXISTS ecommerce AUTHORIZATION :"migrator_user";
CREATE SCHEMA IF NOT EXISTS app_meta AUTHORIZATION :"migrator_user";

REVOKE ALL ON SCHEMA ecommerce FROM PUBLIC;
REVOKE ALL ON SCHEMA app_meta FROM PUBLIC;

-- 4. Grant database CONNECT to the three dedicated roles
GRANT CONNECT ON DATABASE :"db_name" TO :"migrator_user";
GRANT CONNECT ON DATABASE :"db_name" TO :"ro_user";
GRANT CONNECT ON DATABASE :"db_name" TO :"app_user";

-- 5. Configure sql_detective_ro: strictly read-only on ecommerce ONLY
ALTER ROLE :"ro_user" SET default_transaction_read_only = on;
ALTER ROLE :"ro_user" SET statement_timeout = :'stmt_timeout';
ALTER ROLE :"ro_user" SET lock_timeout = '1000ms';
ALTER ROLE :"ro_user" SET search_path = ecommerce;

GRANT USAGE ON SCHEMA ecommerce TO :"ro_user";
GRANT SELECT ON ALL TABLES IN SCHEMA ecommerce TO :"ro_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migrator_user" IN SCHEMA ecommerce
    GRANT SELECT ON TABLES TO :"ro_user";

-- Explicitly verify zero privileges for ro_user on app_meta and public
REVOKE ALL ON SCHEMA app_meta FROM :"ro_user";
REVOKE ALL ON SCHEMA public FROM :"ro_user";

-- 6. Configure sql_detective_app: strictly scoped telemetry writer on app_meta ONLY
ALTER ROLE :"app_user" SET search_path = app_meta;

GRANT USAGE ON SCHEMA app_meta TO :"app_user";
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA app_meta TO :"app_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app_meta TO :"app_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migrator_user" IN SCHEMA app_meta
    GRANT SELECT, INSERT, UPDATE ON TABLES TO :"app_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migrator_user" IN SCHEMA app_meta
    GRANT USAGE, SELECT ON SEQUENCES TO :"app_user";

-- Explicitly verify zero privileges for app_user on ecommerce and public
REVOKE ALL ON SCHEMA ecommerce FROM :"app_user";
REVOKE ALL ON SCHEMA public FROM :"app_user";
EOSQL
