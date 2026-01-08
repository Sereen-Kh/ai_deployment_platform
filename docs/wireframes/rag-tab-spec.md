# RAG Tab — Wireframe Spec

## 0) Screen Definition

**Screen name:** RAG (Retrieval-Augmented Generation)

**Primary user goal:** Manage document collections, upload files, and query knowledge bases using vector search.

**Data dependencies:**
- Collections: `GET /api/v1/rag/collections`
- Documents: `GET /api/v1/rag/documents?collection_name={name}`
- Query: `POST /api/v1/rag/query`

---

## 1) Overall Layout

The page uses a **tabbed interface** with two main tabs:

1. **Collections & Documents** - Manage collections and documents
2. **Query & Test** - Test retrieval with queries

---

## 2) Tab 1: Collections & Documents

### Layout (Side by Side)

Left panel: **Collections List**
Right panel: **Documents in Selected Collection**

---

### 2.1 Left Panel - Collections

#### Header
- **Title:** "Collections"
- **Button:** "+ Create Collection"

#### Collection List
- Card-based layout
- Each card shows:
  - Collection name (bold)
  - Description
  - Document count badge
  - Delete button (trash icon)
- **Click card** → Select collection and load documents
- **Active state** → Highlighted border/background

#### Create Collection Dialog
- **Fields:**
  - Name (required, text input)
  - Description (optional, textarea)
- **Actions:**
  - Cancel button
  - Create button (disabled until name provided)
- **Backend:** `POST /api/v1/rag/collections`

#### Delete Collection
- **Confirmation dialog:** "Are you sure? All documents will be deleted."
- **Backend:** `DELETE /api/v1/rag/collections/{name}`

---

### 2.2 Right Panel - Documents

#### Header
- **Title:** "Documents in {collection_name}"
- **Button:** "+ Upload Document" (disabled if no collection selected)

#### Upload Document Dialog
- **File input:** Drag & drop or click to browse
- **Supported formats:** PDF, TXT, DOCX, MD
- **Progress indicator** during upload
- **Backend:** `POST /api/v1/rag/documents?collection_name={name}`

#### Document List
- Table or card layout
- Columns:
  - **Filename** (with file icon)
  - **Size** (formatted, e.g., "2.3 MB")
  - **Uploaded** (relative time)
  - **Status** (Processing/Ready badge)
  - **Actions** (Delete button)
- **Empty state:** "No documents in this collection. Upload your first document to get started."

#### Delete Document
- **Confirmation dialog:** "Delete this document?"
- **Backend:** `DELETE /api/v1/rag/documents/{id}`

---

## 3) Tab 2: Query & Test

### Layout (Top to Bottom)

1. **Query Input Section**
2. **Query Results Section**

---

### 3.1 Query Input Section

#### Collection Selector
- **Label:** "Select Collection"
- **Dropdown:** List of all collections
- **Required** to enable query

#### Query Input
- **Label:** "Enter your query"
- **Textarea:** Multi-line input
- **Placeholder:** "What information are you looking for?"

#### Query Settings (Expandable)
- **Top K:** Number input (default: 5, range: 1-20)
- **Score Threshold:** Number input (default: 0.5, range: 0.0-1.0)

#### Query Button
- **Label:** "Search"
- **Icon:** Search icon
- **Disabled:** When no collection selected or query empty
- **Loading state:** Spinner during query

---

### 3.2 Query Results Section

#### Results Header
- **Count:** "Found {N} results"
- **Time:** "in {X}ms"

#### Result Cards
Each result shows:
- **Document name** (bold, clickable)
- **Relevance score** (e.g., "85% match")
- **Content snippet** (highlighted query terms)
- **Metadata:**
  - Source file
  - Page/section number (if available)

#### Empty State
- "No results found. Try adjusting your query or score threshold."

#### Error State
- "Query failed: {error message}"
- Retry button

---

## 4) Interaction Rules

### Collection Selection
- Selecting a collection loads its documents
- Deselecting clears document list
- Collection must be selected to upload documents

### Document Upload
- Multi-file upload supported
- Show progress for each file
- Display errors for failed uploads
- Auto-refresh document list on success

### Query Execution
- Real-time search on button click
- Results update in place
- Preserve query and settings for re-run

---

## 5) Loading / Empty / Error States

### Collections Loading
- Show skeleton cards

### Documents Loading
- Show skeleton table rows

### Query Loading
- Show spinner in results area
- Disable query button

### Empty States
- **No collections:** "Create your first collection to get started"
- **No documents:** "Upload documents to this collection"
- **No results:** "No matching documents found"

### Error States
- **Collection creation failed:** Toast notification
- **Upload failed:** Error message in upload dialog
- **Query failed:** Error banner in results area

---

## 6) API Mapping

| Action | API Endpoint | Method | Payload |
|--------|-------------|--------|---------|
| List collections | `/rag/collections` | GET | - |
| Create collection | `/rag/collections` | POST | `{name, description}` |
| Delete collection | `/rag/collections/{name}` | DELETE | - |
| List documents | `/rag/documents` | GET | `?collection_name={name}` |
| Upload document | `/rag/documents` | POST | FormData + `?collection_name={name}` |
| Delete document | `/rag/documents/{id}` | DELETE | - |
| Query | `/rag/query` | POST | `{query, collection_name, top_k, score_threshold}` |

---

## 7) Responsive Behavior

- **Desktop (lg+):** Side-by-side collections/documents
- **Tablet (md):** Stacked layout
- **Mobile (sm):** Full-width stacked, tabs for collections/docs

---

## 8) Validation Rules

### Collection Name
- Required
- 3-50 characters
- Alphanumeric, hyphens, underscores only
- Must be unique

### Document Upload
- Max file size: 10 MB per file
- Allowed extensions: .pdf, .txt, .docx, .md

### Query
- Min length: 3 characters
- Max length: 500 characters

---

## 9) Implementation Status

✅ **Implemented** - RAG page follows this spec completely
