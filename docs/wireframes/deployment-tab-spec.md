# Deployment Tab — Single-screen Wireframe Spec (Designer + API Mapped)

Scope: Translate the provided “Deployment Tab – Wireframe (AI Deployment Platfo
rm)” into an implementation-ready, single-screen UI spec.

Constraints

- Do not change the feature set in the wireframe.
- Labels match wireframe wording.
- Explicit MVP vs Advanced split.
- Every UI block is mapped to existing backend APIs where possible; gaps are called out.

---

## 0) Screen Definition

**Screen name:** Deployment Detail ("Deployment Tab")

**Primary user goal:** See deployment status + endpoint, control lifecycle (stop/redeploy/rollback/delete), adjust configuration, view live monitoring, and inspect logs/events.

**Data dependencies:**

- Deployment: `GET /api/v1/deployments/{deployment_id}`
- Monitoring (placeholder today): `GET /api/v1/analytics/usage` + `GET /api/v1/analytics/usage/timeseries`

---

## 1) Overall Layout (Single Screen)

Top → Bottom

1. **Sticky Header: Deployment Summary**
2. **Main Content Row (2 columns)**
   - Left: **Configuration & Controls (Accordion)**
   - Right: **Monitoring (Default Tab)**
3. **Logs & Events Section (Bottom)**
4. **Deployment History (Expandable Drawer)**

Grid guidance (wireframe intent)

- Header spans full width.
- Main content is a two-column layout (left narrower than right).
- Logs and History span full width.

---

## 2) Header: Deployment Summary (Sticky)

### 2.1 Visual content + exact labels

Row/Block content (verbatim label patterns):

- **Deployment:** `<deployment name>`
- **Status badge:** `Running` / `Deploying` / `Failed` / `Paused`
- **Model:** `<model name + version>`
- **Env:** `<environment>`
- **Updated:** `<relative timestamp>`
- **Endpoint:** `<endpoint url>` and a button `[ Copy ]`

Primary actions (wireframe buttons):

- `[ Stop ]` `[ Redeploy ]` `[ Rollback ]` `[ Delete ]`

### 2.2 Interaction rules

- **Copy** copies the full endpoint URL string.
- **Stop** stops a running deployment.
- **Redeploy** triggers a new deployment rollout using current configuration.
- **Rollback** reverts to a previously known-good version (requires history API; see gaps).
- **Delete** is destructive and requires confirmation.

### 2.3 State-driven enable/disable

Status mapping (backend vs wireframe)

- Wireframe `Running` → backend `running`
- Wireframe `Deploying` → backend `deploying` / `building` (display as Deploying)
- Wireframe `Failed` → backend `failed`
- Wireframe `Paused` → backend `stopped`

Button availability (minimum safe behavior)

- Status=Running: `Stop` enabled; `Redeploy` enabled; `Rollback` enabled (if history exists); `Delete` enabled (confirm).
- Status=Paused/Stopped: `Stop` disabled; `Redeploy` enabled; `Rollback` enabled (if history exists); `Delete` enabled (confirm).
- Status=Deploying/Building: `Stop` enabled (optional) or disabled if platform doesn’t allow; `Redeploy` disabled; `Rollback` disabled; `Delete` enabled (confirm).
- Status=Failed: `Stop` disabled; `Redeploy` enabled; `Rollback` enabled (if history exists); `Delete` enabled.

### 2.4 Backend mapping

- Deployment name: `DeploymentResponse.name`
- Status: `DeploymentResponse.status`
- Updated: `DeploymentResponse.updated_at` (render relative like “2h ago”)
- Endpoint URL: `DeploymentResponse.endpoint_url`
- Model name/version:
  - MVP mapping: `DeploymentResponse.config.model.model` and `DeploymentResponse.version`
  - If the string already includes a version (e.g., “FraudNet v2.3”), display as-is.
- Env:
  - MVP mapping: read-only derived from `DeploymentResponse.config.environment_variables.ENV` if present, else show `—`.

Actions

- Stop: `POST /api/v1/deployments/{id}/stop`
- Redeploy: `POST /api/v1/deployments/{id}/redeploy`
- Delete: `DELETE /api/v1/deployments/{id}` (soft delete sets status to `deleted`)
- Rollback: not available in backend today (gap).

---

## 3) Left Panel — Configuration & Controls (Accordion)

Accordion sections (wireframe numbering):

- 3.1 Model & Serving
- 3.2 Compute & Runtime
- 3.3 Scaling
- 3.4 Environment & Secrets
- 3.5 Security

### 3.1 Model & Serving

Wireframe controls and labels:

- **Model Version:** dropdown `[ v2.3 ▼ ]`
- **Serving Type:** radio `(• REST) ( ) gRPC ( ) Batch`
- **Input Type:** segmented `JSON | Image | Text`

MVP backend mapping (what can be stored today)

- Model version:
  - Store/display using `DeploymentResponse.version` (integer) OR embed in `config.model.model` if you represent versioned model IDs.
- Serving Type: **no field exists today** → Advanced/gap.
- Input Type: **no field exists today** → Advanced/gap.

### 3.2 Compute & Runtime

Wireframe fields:

- Runtime: `Python 3.11`
- Framework: `PyTorch 2.1`
- Resources:
  - CPU Cores `[ 4 ]`
  - Memory (GB) `[ 8 ]`
  - GPU `[ None ▼ ]`
- Replicas:
  - Min `[ 1 ]`
  - Max `[ 5 ]`

MVP backend mapping

- CPU / Memory:
  - Map to `DeploymentUpdate.cpu_limit` and `DeploymentUpdate.memory_limit`.
  - Note: backend stores these as strings (e.g., `"1000m"`, `"2Gi"`). If UI collects numeric cores/GB, conversion rules must be defined (Advanced).
- Replicas:
  - MVP supports a single `replicas` integer (`DeploymentUpdate.replicas`).
  - Min/Max replicas require autoscaling fields (gap).
- Runtime/Framework/GPU:
  - No backend fields today (gap).

### 3.3 Scaling

Wireframe fields:

- Autoscaling: `[ ON ]`
- Scale Metric: `CPU Utilization`
- Target: `60%`
- Cooldown: `120s`

Backend

- No autoscaling fields today (gap).

### 3.4 Environment & Secrets

Wireframe content:

- Environment Vars:
  - `+ KEY = VALUE`
- Secrets:
  - `+ OPENAI_API_KEY (hidden)`
  - `+ DB_TOKEN (hidden)`

MVP backend mapping

- Environment Vars: map to `DeploymentUpdate.config.environment_variables`.
- Secrets: no dedicated storage model in backend today (gap). If implemented later, never return secret values from APIs; only metadata.

### 3.5 Security

Wireframe fields:

- Authentication: `API Key`
- Rate Limit: `100 RPS`
- Visibility: `Private`
- IP Allow List: `10.0.0.0/24`

MVP backend mapping

- API Key exists as `Deployment.api_key` in DB but is not returned in `DeploymentResponse` today.
- Rate limit / visibility / IP allow list: not modeled (gap).

### 3.X Save behavior (implicit)

Because configuration is editable, define **Save** semantics even if not drawn:

- Minimal interpretation: any change triggers a “Save” action (inline) that calls `PATCH /api/v1/deployments/{id}`.
- If you must avoid adding new UI elements, use auto-save with optimistic UI + toast.

Backend update endpoint

- `PATCH /api/v1/deployments/{id}` with `DeploymentUpdate`:
  - `name`, `description`, `replicas`, `cpu_limit`, `memory_limit`, `config`.

---

## 4) Right Panel — Monitoring (Default Tab)

Wireframe tabs:

- `[ Overview ] [ Metrics ] [ Drift ] [ Cost ]`

### 4.1 Overview (default)

Wireframe metrics list (exact labels):

- Latency (p95): `120 ms`
- Error Rate: `0.3%`
- Throughput: `240 req/min`
- CPU Usage: `55%`
- GPU Usage: `--`

Wireframe note:

- “Mini line charts update every few seconds.”

Backend mapping (best-available today)

- Use `GET /api/v1/analytics/usage?deployment_id=<id>&period=24h` for:
  - `p95_latency_ms` → Latency (p95)
  - `failed_requests/total_requests` → Error Rate
  - Throughput: not directly provided (derive from timeseries of requests; see Metrics)
  - CPU/GPU usage: no backend data (display `--`)

### 4.2 Metrics tab

Wireframe high-level intent:

- “Latency | Errors | RPS | CPU | GPU” with mini charts/sparklines.

Backend mapping

- Use `GET /api/v1/analytics/usage/timeseries?metric=requests&period=24h&deployment_id=<id>`
- Use `GET /api/v1/analytics/usage/timeseries?metric=latency&period=24h&deployment_id=<id>`
- `tokens` and `cost` are available as timeseries metrics too.
- Errors/RPS/CPU/GPU are not explicitly modeled as timeseries today; approximate:
  - Errors: use `GET /api/v1/analytics/errors?deployment_id=<id>` (returns aggregate, not timeseries)
  - RPS: derive from `requests` timeseries bucket size (UI-level calculation)
  - CPU/GPU: `--` until backend provides.

### 4.3 Drift tab (Advanced)

Wireframe includes Drift tab.

- Backend: no drift endpoint today (gap).

### 4.4 Cost tab

Backend mapping

- Use `GET /api/v1/analytics/costs?period=30d` (not filtered by deployment today; gap)
- Use `GET /api/v1/analytics/usage?deployment_id=<id>&period=30d` for deployment cost estimate.

---

## 5) Logs & Events Section (Bottom)

Wireframe table

- Columns: `Timestamp | Level | Message`
- Example rows:
  - `INFO  Model loaded`
  - `WARN  High latency detected`
  - `ERROR Timeout on request id=8123`

Wireframe controls

- “Controls - Search - Filter by level - Download logs”
- Filter chips: `[ Filter: Errors | Warnings | All ]`

Backend

- No logs/events endpoint exists today (gap).

Minimum MVP delivery option (without changing wireframe feature set)

- UI can render the Logs section but show an “empty state” with guidance until backend exists.

---

## 6) Deployment History (Expandable Drawer)

Wireframe behavior

- Drawer title: `Deployment History`
- Entries like:
  - `v2.3 deployed by amouna - 2h ago`
  - `v2.2 rollback - yesterday`
  - `v2.1 failed - 3 days ago`
- Clicking an entry shows:
  - Config diff
  - Reason
  - Rollback button

Backend

- No deployment history/versions endpoint exists today (gap).
- Backend has a single `Deployment.version` integer that increments on update; no history store.

---

## 7) MVP vs Advanced (Wireframe-aligned)

MVP UI (must work end-to-end)

- Header summary
- Model version selector
- CPU/GPU config
- Endpoint URL
- Basic metrics
- Logs

Advanced UI (planned)

- Traffic splitting
- Canary deployments
- Drift visualization
- Cost optimization panel

Backend reality check (important)

- MVP UI elements that are fully supported by existing APIs today:
  - Header summary (except “Env” if you don’t store it)
  - Endpoint URL display
  - Stop / Redeploy / Delete
  - Basic metrics (placeholder analytics APIs exist)
  - Environment variables (not secrets)
  - Replicas + cpu/memory limits (as strings)
- MVP UI elements present in wireframe but lacking backend support today (gaps):
  - Rollback + Deployment History
  - Logs & Events data source
  - GPU usage/config
  - Autoscaling min/max + scaling policy
  - Serving type + input type
  - Rate limit, IP allow list, visibility settings

---

## 8) Loading / Empty / Error States (Exact)

Global screen

- Loading: show skeletons for header + panels; disable actions.
- Error (401): redirect to login (or show auth error).
- Error (404 deployment not found): show not-found message and a single “Back to Deployments” action.

Header

- Loading: show placeholder name/status; actions disabled.
- Empty: if `endpoint_url` is null, show `Endpoint: —` and disable Copy.
- Error: if lifecycle action fails, keep current status and show destructive toast.

Configuration panel

- Loading: disable all controls.
- Empty: show defaults but do not send PATCH until user edits.
- Error (PATCH failed): revert last edited control to server value and show toast.

Monitoring panel

- Loading: show empty metrics placeholders.
- Empty: if analytics returns zeros/no data, show `—` values and a “No data in selected period” caption.
- Error: show a compact inline error (“Metrics unavailable”) with retry.

Logs & Events

- Loading: skeleton rows.
- Empty: show “No logs available” and keep filters/search visible.
- Error: show “Unable to load logs” and keep download disabled.

History drawer

- Loading: skeleton list.
- Empty: show “No deployment history available”.
- Error: show retry.

---

## 9) API Mapping Table (UI → Backend)

Header / Summary

- Read: `GET /api/v1/deployments/{id}`
- Stop: `POST /api/v1/deployments/{id}/stop`
- Redeploy: `POST /api/v1/deployments/{id}/redeploy`
- Delete: `DELETE /api/v1/deployments/{id}`
- Rollback: (gap)

Configuration & Controls

- Update: `PATCH /api/v1/deployments/{id}`
  - `name`, `description`, `replicas`, `cpu_limit`, `memory_limit`, `config.environment_variables`, `config.model.*`, `config.enable_streaming`, `config.enable_caching`, `config.cache_ttl`

Monitoring

- Overview metrics: `GET /api/v1/analytics/usage?deployment_id=<id>&period=24h`
- Timeseries (sparklines): `GET /api/v1/analytics/usage/timeseries?metric=<requests|tokens|cost|latency>&period=24h&deployment_id=<id>`
- Errors aggregate: `GET /api/v1/analytics/errors?deployment_id=<id>&period=24h`
- Costs: `GET /api/v1/analytics/costs?period=30d` (not deployment-scoped today)

Logs & Events

- (gap)

Deployment History

- (gap)

---

## 10) Notes for Engineering (Non-Design)

- Analytics routes currently return sample/placeholder data; UI should be resilient to that.
- `cpu_limit` / `memory_limit` are strings in backend; align UI data types before implementing numeric inputs.
- If “Env” is required as a first-class concept, the least invasive MVP path is to use `config.environment_variables.ENV`.
