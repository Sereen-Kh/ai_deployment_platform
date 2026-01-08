# Analytics Tab — Wireframe Spec

## 0) Screen Definition

**Screen name:** Analytics

**Primary user goal:** Deep-dive analysis of API usage, costs, performance metrics, and model breakdowns.

**Data dependencies:**
- Usage data: `GET /api/v1/analytics/usage?period={period}`
- Cost data: `GET /api/v1/analytics/costs?period={period}`
- Time series: `GET /api/v1/analytics/usage/timeseries?metric={metric}&period={period}`

---

## 1) Overall Layout

Top → Bottom sections:

1. **Page Header** - Title, description, and period selector
2. **Stats Grid** - 4 key metrics cards
3. **Charts Grid** - Multiple visualization sections
4. **Model Breakdown** - Usage by model

---

## 2) Page Header

### Visual content
- **Title:** "Analytics"
- **Description:** "Monitor your API usage and costs"
- **Period Selector:** Dropdown
  - Options: Last 24 hours, Last 7 days, Last 30 days, Last 90 days
  - Default: Last 7 days

---

## 3) Stats Grid (4 cards)

### 3.1 Total Requests
- **Label:** "Total Requests"
- **Value:** Formatted number
- **Icon:** TrendingUp
- **Change:** "+23% from previous period"
- **Backend:** `usage.total_requests`

### 3.2 Total Cost
- **Label:** "Total Cost"
- **Value:** Formatted currency ($X.XX)
- **Icon:** DollarSign
- **Change:** "-8% from previous period"
- **Backend:** `costs.total_cost`

### 3.3 Avg Response Time
- **Label:** "Avg Response Time"
- **Value:** "{X}ms"
- **Icon:** Clock
- **Change:** "-12% from previous period"
- **Backend:** `usage.avg_response_time`

### 3.4 Total Tokens
- **Label:** "Total Tokens"
- **Value:** Formatted number
- **Icon:** Zap
- **Change:** "+15% from previous period"
- **Backend:** `usage.total_tokens`

---

## 4) Charts Grid

### 4.1 Request Volume Chart
- **Type:** Area chart
- **Title:** "Request Volume"
- **Description:** "API requests over time"
- **X-axis:** Time
- **Y-axis:** Request count
- **Backend:** `GET /api/v1/analytics/usage/timeseries?metric=requests&period={period}`

### 4.2 Latency Trend Chart
- **Type:** Line chart
- **Title:** "Response Time"
- **Description:** "Average latency over time"
- **X-axis:** Time
- **Y-axis:** Milliseconds
- **Backend:** `GET /api/v1/analytics/usage/timeseries?metric=latency&period={period}`

### 4.3 Cost Trend Chart
- **Type:** Area chart with gradient
- **Title:** "Cost Over Time"
- **Description:** "Spending trend"
- **X-axis:** Time
- **Y-axis:** Dollar amount
- **Backend:** `GET /api/v1/analytics/usage/timeseries?metric=cost&period={period}`

### 4.4 Token Usage Chart
- **Type:** Bar chart
- **Title:** "Token Consumption"
- **Description:** "Tokens used over time"
- **X-axis:** Time
- **Y-axis:** Token count
- **Backend:** `GET /api/v1/analytics/usage/timeseries?metric=tokens&period={period}`

---

## 5) Model Breakdown Section

### Visual content
- **Title:** "Usage by Model"
- **Type:** Pie chart or horizontal bar chart
- **Data:** List of models with:
  - Model name
  - Request count
  - Percentage of total
  - Cost
- **Backend:** `usage.model_breakdown[]`

### Table view
| Model | Requests | Percentage | Cost |
|-------|----------|------------|------|
| GPT-4 | 15,234 | 45% | $234.56 |
| Claude 3 | 10,123 | 30% | $156.78 |
| ... | ... | ... | ... |

---

## 6) Interaction Rules

### Period Selection
- Changing period updates all stats, charts, and breakdowns
- Loading state while data refreshes
- Optimistic UI updates

### Chart Interactions
- Hover tooltips show exact values
- Responsive to window resize
- Mobile: stack charts vertically

---

## 7) Loading / Empty / Error States

### Loading
- Skeleton cards for stats
- Loading spinners in chart areas
- Preserve layout structure

### Empty (No data for period)
- Show "No data available for this period"
- Keep charts visible with empty state message
- Suggest trying different period

### Error
- Show error message in affected section
- Retry button
- Rest of page remains functional

---

## 8) API Mapping

| UI Element | API Endpoint | Method |
|------------|-------------|--------|
| Stats Grid | `/analytics/usage?period={period}` | GET |
| Stats Grid | `/analytics/costs?period={period}` | GET |
| Request Chart | `/analytics/usage/timeseries?metric=requests&period={period}` | GET |
| Latency Chart | `/analytics/usage/timeseries?metric=latency&period={period}` | GET |
| Cost Chart | `/analytics/usage/timeseries?metric=cost&period={period}` | GET |
| Token Chart | `/analytics/usage/timeseries?metric=tokens&period={period}` | GET |
| Model Breakdown | `/analytics/usage?period={period}` | GET |

---

## 9) Responsive Behavior

- **Desktop (lg+):** 4-column stats, 2×2 chart grid
- **Tablet (md):** 2-column stats, 2-column charts
- **Mobile (sm):** 1-column layout, stacked charts

---

## 10) Color Scheme

- **Request volume:** Blue gradient
- **Latency:** Orange/Yellow
- **Cost:** Green gradient
- **Tokens:** Purple
- **Model pie chart:** Multi-color palette

---

## 11) Implementation Status

✅ **Implemented** - Analytics page follows this spec completely
