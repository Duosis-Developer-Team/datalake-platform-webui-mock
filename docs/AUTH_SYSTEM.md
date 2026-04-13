# Authentication and RBAC (operator summary)

The Dash UI in this repository uses the same authentication stack as **Datalake Platform GUI**: a dedicated **auth PostgreSQL** database, hierarchical **RBAC**, optional **LDAP**, Flask session cookies, and optional **JWT** for calls to FastAPI microservices.

## Quick facts

| Topic | Details |
|-------|---------|
| Auth database | Separate PostgreSQL (`AUTH_DB_*` env vars). Schema applied at startup via migrations in `src/auth/migration.py`. |
| HTTP | Blueprint `src/auth/routes.py` — `/auth/login`, `/auth/logout`; middleware in `src/auth/middleware.py`. |
| Session | Cookie name default `dl_session` (`SESSION_COOKIE_NAME`). |
| Permissions | Tree in `src/auth/permission_catalog.py`; effective rights in `src/auth/permission_service.py`. |
| APIs | Optional JWT on FastAPI when `API_AUTH_REQUIRED=true`; set `API_JWT_SECRET` consistently on Dash and services. |

## Environment variables

See root [`env.example`](../env.example) for `AUTH_*`, `SECRET_KEY`, `FERNET_KEY`, `AUTH_DISABLED`, `API_JWT_SECRET`, `REDIS_URL` (optional permission cache), etc.

## Kubernetes

- Create Secret `bulutistan-auth-secrets` (see [`k8s/auth-secrets-reference.yaml`](../k8s/auth-secrets-reference.yaml)).
- Set non-secret auth DB keys in [`k8s/frontend/configmap.yaml`](../k8s/frontend/configmap.yaml).
- Full steps: [K8S_DEPLOYMENT_AND_UPDATE.md](K8S_DEPLOYMENT_AND_UPDATE.md).

## Full reference (upstream)

Canonical documentation with module table, Docker notes, and troubleshooting lives in the GUI repository:

**[../Datalake-Platform-GUI/docs/AUTH_SYSTEM.md](../Datalake-Platform-GUI/docs/AUTH_SYSTEM.md)**

When the two repositories diverge, prefer syncing `src/auth/` and `sql/auth_schema.sql` from that upstream project if this repo is a downstream fork or mock variant.
