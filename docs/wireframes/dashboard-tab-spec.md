# Dashboard Tab — Wireframe Spec

## 0) Screen Definition

**Screen name:** Dashboard (Home)

**Primary user goal:** Get a quick overview of all deployments, usage statistics, and recent activity.

**Data dependencies:**

- Dashboard stats: `GET /api/v1/analytics/dashboard`
- Deployments: `GET /api/v1/deployments`
- Usage data: `GET /api/v1/analytics/usage?period=7d`

---

## 1) Overall Layout

Top → Bottom sections:

1. **Page Header** - Title and description
2. **Stats Grid** - 4 key metrics cards
3. **Charts Row** - 2 charts side by side
4. **Recent Deployments** - Table/list of recent deployments

---

## 2) Page Header

### Visual content

- **Title:** "Dashboard"
- **Description:** "Overview of your AI deployments and usage"

---

## 3) Stats Grid (4 cards)

### 3.1 Total Deployments

- **Label:** "Total Deployments"
- **Value:** Count of all deployments
- **Icon:** Rocket
- **Change indicator:** "+12% from last week" (green)
- **Backend:** `dashboard.total_deployments`

### 3.2 Active Deployments

- **Label:** "Active Deployments"
- **Value:** Count of running deployments
- **Icon:** Activity
- **Change indicator:** "+5% from last week" (green)
- **Backend:** `dashboard.active_deployments`

### 3.3 Total Requests

- **Label:** "Total Requests"
- **Value:** Formatted number of requests
- **Icon:** TrendingUp
- **Change indicator:** "+23% from last week" (green)
- **Backend:** `dashboard.total_requests`

### 3.4 Total Cost

- **Label:** "Total Cost"
- **Value:** Formatted currency
- **Icon:** DollarSign
- **Change indicator:** "-8% from last week" (green - cost reduction)
- **Backend:** `dashboard.total_cost`

---

## 4) Charts Row

### 4.1 API Usage Chart

- **Type:** Line chart
- **Title:** "API Usage"
- **Description:** "Requests over the last 7 days"
- **Data:** Time series of request counts
- **Backend:** `GET /api/v1/analytics/usage/timeseries?metric=requests&period=7d`

### 4.2 Cost Breakdown Chart

- **Type:** Bar chart
- **Title:** "Cost by Model"
- **Description:** "Spending breakdown by model"
- **Data:** Model names and associated costs
- **Backend:** `GET /api/v1/analytics/usage` (aggregate by model)

---

## 5) Recent Deployments Table

### Columns

- **Deployment Name** - Clickable link to detail page
- **Model** - Model name/version
- **Status** - Badge (Running/Stopped/Failed/Deploying)
- **Created** - Relative timestamp
- **Actions** - Quick action buttons

### Features

- Show top 5 most recent deployments
- Click row to navigate to deployment detail
- Link to "View All" → Deployments page

### Backend

- `GET /api/v1/deployments?page=1&page_size=5`

---

## 6) Loading / Empty / Error States

### Loading

- Show skeleton cards for stats
- Show loading spinner in chart areas
- Show skeleton rows in recent deployments

### Empty (No deployments)

- Show empty state with icon and message
- "Get started by creating your first deployment"
- Button to create new deployment

### Error

- Show error message with retry button
- Keep layout intact, show errors inline in affected sections

---

## 7) API Mapping

| UI Element         | API Endpoint                  | Method |
| ------------------ | ----------------------------- | ------ |
| Stats Grid         | `/analytics/dashboard`        | GET    |
| Active Deployments | `/deployments`                | GET    |
| Usage Chart        | `/analytics/usage/timeseries` | GET    |
| Cost Chart         | `/analytics/usage`            | GET    |
| Recent Deployments | `/deployments`                | GET    |

---

## 8) Responsive Behavior

- **Desktop (lg+):** 4-column stats grid, 2-column charts
- **Tablet (md):** 2-column stats grid, 2-column charts
- **Mobile (sm):** 1-column layout for all sections

---

## 9) Implementation Status

✅ **Implemented** - Dashboard page follows this spec completely
