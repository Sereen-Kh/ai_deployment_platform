# Settings Tab — Wireframe Spec

## 0) Screen Definition

**Screen name:** Settings

**Primary user goal:** Manage user account, profile information, and API keys for programmatic access.

**Data dependencies:**
- User info: `GET /api/v1/auth/me`
- API keys: `GET /api/v1/api-keys`
- Create key: `POST /api/v1/api-keys`
- Delete key: `DELETE /api/v1/api-keys/{id}`

---

## 1) Overall Layout

The page uses a **tabbed interface** with two main sections:

1. **Profile** - User account information
2. **API Keys** - Manage API keys for authentication

---

## 2) Page Header

### Visual content
- **Title:** "Settings"
- **Description:** "Manage your account and API keys"

---

## 3) Tab 1: Profile

### 3.1 Profile Information Card

#### Header
- **Title:** "Profile Information"
- **Description:** "Your account details and preferences"

#### Fields

##### Email
- **Label:** "Email"
- **Input:** Text input (disabled/read-only)
- **Value:** User's email from backend
- **Backend:** `user.email`

##### Username (Optional)
- **Label:** "Username"
- **Input:** Text input (read-only or editable)
- **Value:** User's username
- **Backend:** `user.username`

##### Role
- **Label:** "Role"
- **Display:** Badge (not editable)
- **Value:** User's role (admin, user, viewer)
- **Style:** Capitalized badge with variant color
- **Backend:** `user.role`

##### Account Created
- **Label:** "Account Created"
- **Display:** Read-only text
- **Value:** Formatted date (e.g., "January 15, 2024")
- **Backend:** `user.created_at`

##### Account Status
- **Label:** "Status"
- **Display:** Badge
- **Value:** Active/Inactive/Suspended
- **Backend:** `user.status` (if available)

---

### 3.2 Password Change Section (Optional)

#### Header
- **Title:** "Change Password"
- **Description:** "Update your account password"

#### Fields
- **Current Password** - Password input
- **New Password** - Password input with strength indicator
- **Confirm Password** - Password input

#### Button
- **Label:** "Update Password"
- **Validation:** 
  - All fields required
  - New password must meet requirements
  - Confirm must match new password

---

### 3.3 Preferences Section (Optional)

#### Notifications
- **Email notifications** - Toggle switch
- **Weekly reports** - Toggle switch

#### Theme
- **Dark mode** - Toggle switch (if supported)

---

## 4) Tab 2: API Keys

### 4.1 API Keys List

#### Header
- **Title:** "API Keys"
- **Description:** "Create and manage API keys for programmatic access"
- **Button:** "+ Create API Key"

#### Empty State
- **Icon:** Key icon
- **Message:** "No API keys yet"
- **Description:** "Create an API key to access the platform programmatically"
- **Button:** "Create Your First API Key"

---

### 4.2 API Key Cards/Table

Each API key displays:

#### Card Layout
- **Key Name** (bold)
- **Key Value** (masked by default)
  - Format: `sk_****...****` (first 4 and last 4 characters visible)
  - Toggle button (eye icon) to show/hide full key
- **Created Date** (relative time, e.g., "2 days ago")
- **Last Used** (relative time or "Never used")
- **Actions:**
  - Copy button (clipboard icon)
  - Delete button (trash icon)

#### Table Layout (Alternative)
| Name | Key | Created | Last Used | Actions |
|------|-----|---------|-----------|---------|
| Production Key | sk_••••...••••4a2b | 2 days ago | 1 hour ago | Copy, Delete |

---

### 4.3 Create API Key Dialog

#### Trigger
- Click "+ Create API Key" button

#### Dialog Content

##### Key Name
- **Label:** "Key Name"
- **Input:** Text input
- **Placeholder:** "Production API Key"
- **Required:** Yes
- **Validation:** 3-50 characters

##### Scopes/Permissions (Optional)
- **Label:** "Permissions"
- **Input:** Checkbox group
- **Options:**
  - Read deployments
  - Write deployments
  - Read analytics
  - Manage API keys
- **Default:** Read-only access

##### Expiration (Optional)
- **Label:** "Expiration"
- **Input:** Dropdown
- **Options:**
  - Never
  - 30 days
  - 90 days
  - 1 year
- **Default:** Never

#### Actions
- **Cancel** - Close dialog without creating
- **Create** - Generate new API key

---

### 4.4 API Key Created Success

#### Display
After creation, show the **new API key in full** with a warning:

- **Alert banner (warning style):**
  - "⚠️ Important: Copy your API key now. You won't be able to see it again!"
- **API Key Display:**
  - Full key in monospace font
  - Copy button next to key
  - QR code (optional)

#### Actions
- **Copy Key** - Copy to clipboard
- **I've Saved My Key** - Close dialog (required acknowledgment)

---

### 4.5 Delete API Key

#### Confirmation Dialog
- **Title:** "Delete API Key?"
- **Message:** "This will permanently revoke the API key. Applications using this key will lose access."
- **Key name:** Display which key is being deleted
- **Actions:**
  - Cancel
  - Delete (destructive button)

#### Backend
- `DELETE /api/v1/api-keys/{id}`

---

## 5) Interactions

### Show/Hide API Key
- Click eye icon to toggle visibility
- Store visibility state per key (client-side only)
- Security: Don't store full keys in frontend state

### Copy API Key
- Click copy button
- Toast notification: "API key copied to clipboard"
- Success indicator (checkmark animation)

### Create API Key
- Form validation before submission
- Loading state during creation
- Success: Show new key immediately
- Error: Display error message in dialog

### Delete API Key
- Require confirmation
- Optimistic update (remove from list immediately)
- On error, restore key and show error toast

---

## 6) Loading / Empty / Error States

### Loading
- **Profile:** Skeleton text for fields
- **API Keys:** Skeleton cards

### Empty
- **No API keys:** Show empty state with create button

### Error
- **Profile load error:** "Failed to load profile. Retry?"
- **API key load error:** "Failed to load API keys. Retry?"
- **Create error:** Error message in dialog
- **Delete error:** Toast notification

---

## 7) API Mapping

| Action | API Endpoint | Method | Payload |
|--------|-------------|--------|---------|
| Get user profile | `/auth/me` | GET | - |
| Get API keys | `/api-keys` | GET | - |
| Create API key | `/api-keys` | POST | `{name, scopes, expires_days}` |
| Delete API key | `/api-keys/{id}` | DELETE | - |
| Update profile | `/auth/me` | PATCH | `{username, email, ...}` (if editable) |
| Change password | `/auth/change-password` | POST | `{current_password, new_password}` |

---

## 8) Security Considerations

### API Key Storage
- **Never store full API keys** in frontend state after initial creation
- Only display full key once (on creation)
- Mask keys in list view

### Visibility Toggle
- Only affects UI display
- Don't persist visibility state across sessions

### Key Creation
- Strong key generation (backend)
- Prefix keys with `sk_` for identification
- Minimum 32 characters length

---

## 9) Validation Rules

### API Key Name
- Required
- 3-50 characters
- Alphanumeric, spaces, hyphens, underscores

### Password Change (if supported)
- Current password required
- New password:
  - Min 8 characters
  - Contains uppercase, lowercase, number
  - Not same as current password

---

## 10) Responsive Behavior

- **Desktop (lg+):** Two-column form layout where applicable
- **Tablet (md):** Single column, full-width cards
- **Mobile (sm):** Stacked layout, simplified table → cards

---

## 11) Accessibility

- Proper labels for all form inputs
- ARIA labels for icon buttons
- Keyboard navigation support
- Screen reader announcements for key operations

---

## 12) Implementation Status

✅ **Implemented** - Settings page follows this spec completely

---

## 13) Future Enhancements (Not in MVP)

- Two-factor authentication (2FA)
- Session management (view active sessions)
- Team settings (for team workspaces)
- Audit logs (key usage history)
- Webhook configurations
- Billing settings
