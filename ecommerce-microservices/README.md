# E-Commerce Microservices Platform

A 5-service, event-driven e-commerce backend (Django + DRF) with a full
DevOps deployment story: Docker, Kubernetes, Terraform (EKS + per-service
RDS), ArgoCD (GitOps), and per-service GitHub Actions pipelines.

See **DEMO_TRANSCRIPT.md** for real captured output of the whole order
lifecycle running end-to-end.

## Architecture

| Service | Owns | Talks to |
|---|---|---|
| **auth-service** | Users, JWT tokens | — |
| **catalog-service** | Products, categories, stock | — |
| **orders-service** | Orders, order items | Auth (verify token, sync), Catalog (price + reserve stock, sync) |
| **payments-service** | Payment records (mocked gateway) | Orders (callback, sync), event bus (publish) |
| **notifications-service** | Notification log (mocked email) | event bus (consume only) |

Each service owns its own database — no shared tables, no service reaching
into another's schema.

**Synchronous** (REST, called inline while placing an order): Orders → Auth,
Orders → Catalog. If either fails, the order is never created and any stock
already reserved is rolled back.

**Asynchronous** (event bus, fire-and-forget): Orders publishes
`order.created`; Payments and Notifications each consume it independently.
Payments then publishes `order.paid` / `order.payment_failed`, which
Notifications also consumes. Orders never waits on Payments or
Notifications.

```
Orders --(sync REST)--> Auth        (verify JWT)
Orders --(sync REST)--> Catalog     (price + reserve stock)
Orders --(async event: order.created)--> Payments, Notifications
Payments --(sync REST callback)--> Orders   (mark paid / payment_failed)
Payments --(async event: order.paid | order.payment_failed)--> Notifications
```

The event bus has two interchangeable transports, controlled by
`EVENT_BUS_MODE`:
- `http` (default) — plain HTTP POST fan-out. Zero infrastructure, used for
  the local demo in this sandbox.
- `amqp` — real RabbitMQ, topic exchange `ecommerce.events`. Used by
  `docker-compose.yml` and the Kubernetes manifests. Payments and
  Notifications each run a `consume_events` management command as a
  separate worker Deployment.

Business logic (`handlers.py` in each service) is identical either way —
only the transport changes.

## Repo layout

```
auth-service/            catalog-service/         orders-service/
payments-service/        notifications-service/   (5 independent Django projects)
docker-compose.yml        # Postgres + RabbitMQ + all 5 services + 2 consumer workers
infra/                     # Postgres multi-db init script for docker-compose
k8s/
  base/                     # namespace, configmap, secret template, per-service Deployment/Service/NetworkPolicy, RabbitMQ, Ingress
  services/<name>/          # thin kustomize overlay per service, for independent ArgoCD Applications
  overlays/production/      # full-stack kustomize overlay with pinned image tags
terraform/                # VPC, EKS cluster + node group, one RDS instance per service, Secrets Manager
argocd/
  root-app.yaml             # App-of-Apps root
  applications/              # one Application per service + one for shared platform resources
.github/workflows/
  reusable-service-pipeline.yml   # test -> build -> Trivy scan -> push (GHCR) -> cosign sign -> bump GitOps manifest
  <service>.yml                    # 5 thin callers, each path-filtered to its own service directory
```

## Run it locally (zero infra, matches DEMO_TRANSCRIPT.md)

Each service is a standalone Django project using SQLite and
`EVENT_BUS_MODE=http` by default — no Docker, Postgres, or RabbitMQ
required.

```bash
python3 -m venv venv && source venv/bin/activate
for svc in auth-service catalog-service orders-service payments-service notifications-service; do
  pip install -r $svc/requirements.txt
done

for svc in auth-service catalog-service orders-service payments-service notifications-service; do
  (cd $svc && python manage.py migrate)
done

(cd auth-service          && python manage.py runserver 0.0.0.0:8001) &
(cd catalog-service       && python manage.py runserver 0.0.0.0:8002) &
(cd orders-service        && python manage.py runserver 0.0.0.0:8003) &
(cd payments-service      && python manage.py runserver 0.0.0.0:8004) &
(cd notifications-service && python manage.py runserver 0.0.0.0:8005) &
```

Then walk through the flow in `DEMO_TRANSCRIPT.md`, or open
`demo/index.html` for a visual walkthrough of the same requests without
running anything.

## Run it with Docker Compose (real Postgres + RabbitMQ)

```bash
cp .env.example .env   # fill in real secrets
docker compose up --build
```

This brings up Postgres (one DB per service), RabbitMQ, all 5 API
services, and the two consumer workers (`payments-consumer`,
`notifications-consumer`) with `EVENT_BUS_MODE=amqp`.

## Deploy to AWS (EKS)

```bash
cd terraform
terraform init
terraform apply
$(terraform output -raw configure_kubectl)
```

Then either apply the full stack directly:

```bash
kubectl apply -k k8s/overlays/production
```

...or, for GitOps, point ArgoCD at `argocd/root-app.yaml` once — it
discovers the 6 Applications in `argocd/applications/` (5 services + shared
platform resources) automatically from there on.

## CI/CD

Each service has its own path-filtered GitHub Actions workflow
(`.github/workflows/<service>.yml`) that only runs when that service's
directory changes, calling a shared `reusable-service-pipeline.yml`:

1. `python manage.py test`
2. Build the image
3. Trivy scan — fails the build on HIGH/CRITICAL CVEs
4. Push to GHCR, sign with cosign (keyless OIDC)
5. Bump that service's image tag in `k8s/overlays/production/kustomization.yaml` and commit — ArgoCD picks up the change and syncs

## Security notes

- User-facing auth: JWT (HS256, shared signing key), verified statelessly
  by every service — no service does a DB lookup against another
  service's User table.
- Service-to-service calls (stock adjustment, event webhooks, Payments →
  Orders callback) require a separate `X-Internal-Token` header, not a
  user JWT — a stand-in here for mTLS/service-mesh identity in the real
  cluster.
- `k8s/base/02-secret.template.yaml` is a template only; real values are
  rendered in CI from GitHub/Secrets Manager, never committed.
- Default-deny `NetworkPolicy` applied namespace-wide; each service's
  policy opens only the ports it actually needs.
