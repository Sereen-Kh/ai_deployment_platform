# AI Deployment Platform — Complete UI Specification

## Overview

This document provides a comprehensive overview of all UI screens in the AI Deployment Platform, their relationships, and navigation patterns.

---

## Application Structure

### Navigation Architecture

```
├── Public Routes
│   ├── /login - Login Page
│   └── /register - Registration Page
│
└── Authenticated Routes (requires login)
    ├── / - Dashboard (Home)
    ├── /deployments - Deployments List
    ├── /deployments/:id - Deployment Detail
    ├── /playground - AI Playground
    ├── /rag - RAG Management
    ├── /analytics - Analytics Dashboard
    └── /settings - User Settings
```

---

## Screen Summary

### 1. Dashboard (`/`)
**Purpose:** Central hub showing overview of all deployments and key metrics

**Key Features:**
- Stats cards (deployments, requests, costs)
- Usage charts
- Recent deployments list
- Quick actions

**Spec:** [dashboard-tab-spec.md](./dashboard-tab-spec.md)

---

### 2. Deployments List (`/deployments`)
**Purpose:** Browse and manage all AI model deployments

**Key Features:**
- Grid of deployment cards
- Status indicators
- Quick start/stop actions
- Create new deployment dialog
- Click to view detail

**Spec:** Integrated with deployment detail spec

---

### 3. Deployment Detail (`/deployments/:id`)
**Purpose:** Detailed view and configuration for a single deployment

**Key Features:**
- Deployment summary header
- Configuration panel (accordion)
- Monitoring tabs (overview, metrics, cost)
- Logs & events viewer
- Deployment history

**Spec:** [deployment-tab-spec.md](./deployment-tab-spec.md)

---

### 4. Playground (`/playground`)
**Purpose:** Interactive testing environment for AI models

**Key Features:**
- Real-time chat interface
- Model selection and configuration
- Streaming responses
- Presets for quick testing
- Session statistics

**Spec:** [playground-tab-spec.md](./playground-tab-spec.md)

---

### 5. RAG (`/rag`)
**Purpose:** Manage document collections and test retrieval

**Key Features:**
- Collection management
- Document upload and indexing
- Vector search testing
- Query interface

**Spec:** [rag-tab-spec.md](./rag-tab-spec.md)

---

### 6. Analytics (`/analytics`)
**Purpose:** Deep-dive into usage metrics and costs

**Key Features:**
- Time period selection
- Multiple chart types
- Model breakdown
- Cost tracking

**Spec:** [analytics-tab-spec.md](./analytics-tab-spec.md)

---

### 7. Settings (`/settings`)
**Purpose:** User account and API key management

**Key Features:**
- Profile information
- API key creation and management
- Account preferences

**Spec:** [settings-tab-spec.md](./settings-tab-spec.md)

---

### 8. Login (`/login`)
**Purpose:** User authentication

**Key Features:**
- Email/password form
- Remember me option
- Link to registration
- Password reset (future)

---

### 9. Register (`/register`)
**Purpose:** New user registration

**Key Features:**
- Email/password/name form
- Password strength indicator
- Link to login
- Terms acceptance

---

## Common Components

### Layout Component
- **Sidebar navigation** with active state indicators
- **Header** with user menu and logout
- **Responsive** hamburger menu on mobile
- **Breadcrumbs** (optional)

### UI Components (shadcn/ui)
- **Cards** - Container component used throughout
- **Buttons** - Primary, secondary, destructive, ghost variants
- **Inputs** - Text, number, password with validation
- **Selects** - Dropdowns for options
- **Dialogs** - Modals for create/confirm actions
- **Tabs** - Tab navigation within pages
- **Tables** - Data display
- **Charts** - Recharts integration
- **Badges** - Status indicators
- **Spinners** - Loading states
- **Toasts** - Notifications

---

## Design Patterns

### Color Scheme
- **Primary:** Blue (`#3b82f6`)
- **Success:** Green
- **Warning:** Yellow/Orange
- **Destructive:** Red
- **Muted:** Gray

### Status Colors
- **Running:** Green
- **Stopped:** Gray
- **Deploying:** Yellow
- **Failed:** Red

### Typography
- **Headings:** Bold, sans-serif
- **Body:** Regular, sans-serif
- **Code/Keys:** Monospace font

### Spacing
- Consistent gap sizes: `gap-2`, `gap-4`, `gap-6`
- Padding: `p-4`, `p-6`
- Margins: `mt-4`, `mb-6`

---

## State Management

### Auth Store (Zustand)
- User information
- Access/refresh tokens
- Login/logout actions
- Persist to localStorage

### Deployment Store (Zustand)
- Selected deployment
- Filters and sorting
- Cache deployment list

### React Query
- Server state caching
- Automatic refetching
- Optimistic updates
- Error handling

---

## API Integration

All API calls go through the centralized `services/api.ts` with:
- Axios client with interceptors
- JWT token injection
- Token refresh on 401
- Automatic logout on auth failure

### API Modules
- `authAPI` - Authentication
- `deploymentsAPI` - Deployment management
- `analyticsAPI` - Usage and cost data
- `ragAPI` - RAG collections and documents
- `playgroundAPI` - Model testing
- `apiKeysAPI` - API key management

---

## Responsive Breakpoints

- **Mobile:** `< 768px` (sm)
- **Tablet:** `768px - 1024px` (md)
- **Desktop:** `> 1024px` (lg)

### Responsive Behaviors
- **Mobile:** Single column, hamburger menu, stacked layouts
- **Tablet:** 2-column grids, sidebar visible
- **Desktop:** Multi-column grids, full sidebar, side-by-side layouts

---

## Error Handling

### Network Errors
- Toast notification with error message
- Retry button where applicable
- Fallback to cached data (React Query)

### Validation Errors
- Inline error messages below inputs
- Form-level error summary
- Disabled submit until valid

### API Errors
- 401: Redirect to login
- 403: "Access denied" message
- 404: Not found page
- 500: "Server error" with retry

---

## Loading States

### Page Load
- Full-page spinner for initial data
- Skeleton components for partial loads

### Action Load
- Button spinner during mutations
- Disabled state to prevent double-submit
- Optimistic updates where safe

### Infinite Scroll / Pagination
- Load more spinner at bottom
- Skeleton rows for new data

---

## Accessibility

### ARIA
- Proper labels on all inputs
- Role attributes for custom components
- Live regions for dynamic content

### Keyboard Navigation
- Tab order follows visual flow
- Enter to submit forms
- Escape to close dialogs
- Arrow keys in lists/tables

### Screen Readers
- Descriptive alt text
- Semantic HTML
- Skip navigation links

---

## Performance Optimizations

### Code Splitting
- Lazy load route components
- Dynamic imports for heavy libraries

### Memoization
- React.memo for expensive renders
- useMemo for computed values
- useCallback for stable references

### Caching
- React Query stale time: 5 minutes
- localStorage for auth tokens
- Debounce search inputs

---

## Testing Strategy

### Unit Tests
- Component rendering
- User interactions
- State management
- API service functions

### Integration Tests
- Full user flows
- Form submissions
- Navigation

### E2E Tests
- Critical paths (login → create deployment → view)
- Cross-browser testing

---

## Deployment

### Environment Variables
- `VITE_API_URL` - Backend API base URL
- `VITE_WS_URL` - WebSocket URL (for playground)

### Build
```bash
npm run build
```

### Docker
```bash
docker build -t ai-platform-frontend .
docker run -p 80:80 ai-platform-frontend
```

---

## Implementation Checklist

- ✅ Dashboard page
- ✅ Deployments list page
- ✅ Deployment detail page
- ✅ Playground page
- ✅ RAG page
- ✅ Analytics page
- ✅ Settings page
- ✅ Login/Register pages
- ✅ Layout and navigation
- ✅ API service layer
- ✅ State management
- ✅ Error handling
- ✅ Loading states
- ✅ Responsive design

---

## Future Enhancements

### Phase 2 Features
- [ ] Real-time collaboration
- [ ] Team workspaces
- [ ] Advanced monitoring (drift detection)
- [ ] Cost optimization recommendations
- [ ] Deployment templates
- [ ] A/B testing deployments
- [ ] Custom metrics and alerts
- [ ] Audit logs
- [ ] Webhooks
- [ ] CLI integration

### UI Improvements
- [ ] Dark mode
- [ ] Customizable dashboards
- [ ] Saved filters and views
- [ ] Keyboard shortcuts panel
- [ ] Advanced search
- [ ] Bulk operations
- [ ] Export/import configurations

---

## Documentation Links

- [Dashboard Spec](./dashboard-tab-spec.md)
- [Deployment Detail Spec](./deployment-tab-spec.md)
- [Analytics Spec](./analytics-tab-spec.md)
- [RAG Spec](./rag-tab-spec.md)
- [Playground Spec](./playground-tab-spec.md)
- [Settings Spec](./settings-tab-spec.md)

---

## Contact & Support

For questions or issues with the UI implementation:
- Review relevant spec document
- Check API endpoint documentation
- Verify backend is running and accessible
- Check browser console for errors

---

**Last Updated:** January 7, 2026
**Version:** 1.0.0
