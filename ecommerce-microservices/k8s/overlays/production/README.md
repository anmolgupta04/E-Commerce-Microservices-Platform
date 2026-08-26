# Production overlay

`kubectl apply -k .` deploys everything in `../../base` plus the pinned
image tags above.

Before applying to a real cluster, provide `ecommerce-secrets` one of two
ways -- **do not** commit a filled-in copy of `02-secret.template.yaml`:

1. **CI-rendered Secret** (simplest): the deploy workflow
   (`.github/workflows/cd.yml`) reads `JWT_SIGNING_KEY`,
   `INTERNAL_SERVICE_TOKEN`, DB credentials, and per-service RDS hostnames
   from GitHub Actions secrets / Terraform outputs, renders
   `02-secret.template.yaml` with `envsubst`, and applies it just before
   the kustomize build.
2. **External Secrets Operator** (recommended for a real deployment):
   replace `02-secret.template.yaml` with an `ExternalSecret` that pulls
   the same keys directly from AWS Secrets Manager, so no secret material
   ever passes through CI logs or Git history at all.
