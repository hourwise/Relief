-- Relief Apply 1A bounded database roles.
--
-- This file is deliberately secret-free. It is a declarative role definition,
-- not a credential store. The operator LOGIN role receives its password in a
-- separately approved, secure provisioning step; no PASSWORD clause belongs
-- in this repository.
--
-- The roles are intentionally narrower than postgres/service_role. The Apply
-- migration grants the owner role only its exact registry/read/allowlisted
-- write permissions and grants the operator role only private-schema usage
-- and execution of the Apply function.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'relief_apply_owner'
  ) THEN
    CREATE ROLE relief_apply_owner
      NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  ELSE
    ALTER ROLE relief_apply_owner
      NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'relief_apply_operator'
  ) THEN
    CREATE ROLE relief_apply_operator
      LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  ELSE
    ALTER ROLE relief_apply_operator
      LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;

  -- The migration executor is the hosted postgres role, not a superuser.
  -- Membership lets it transfer ownership of the SECURITY DEFINER function
  -- to the NOLOGIN owner role. This does not grant the owner role to any app
  -- role and does not grant the operator role any additional membership.
  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'postgres'
  ) THEN
    EXECUTE 'GRANT relief_apply_owner TO postgres';
  END IF;
END;
$$;
