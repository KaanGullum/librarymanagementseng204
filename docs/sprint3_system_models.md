# Sprint 3 System Models

This document captures the Sprint 3 modeling/presentation view for reporting and dashboard features, especially overdue books reporting.

## 1. Connected with Main System

Sprint 3 reporting is not a standalone feature. It depends on existing modules:

- `main_window.py`: integrates `Reports` and `Dashboard` tabs into the main system
- `views/reports.py`: overdue reporting screen and summary generation
- `views/dashboard.py`: dashboard cards and overdue preview
- `reporting.py`: reporting service layer (queries + overdue classification + derived penalty estimate)
- `views/members.py` and `views/borrowing.py`: create/update borrowing lifecycle data
- `models.py`: `Book`, `BorrowingRecord`, `Member`, `User`, `RoleEnum`
- `database.py` / `library_v2.db`: persistence layer

```mermaid
flowchart LR
    Login["login_window.py<br/>Authenticated User Session"] --> Main["main_window.py<br/>Reports/Dashboard Navigation"]

    Main --> ReportsUI["views/reports.py"]
    Main --> DashboardUI["views/dashboard.py"]

    ReportsUI --> ReportingSvc["reporting.py"]
    DashboardUI --> ReportingSvc

    BorrowingUI["views/members.py + views/borrowing.py"] --> BorrowRecord["BorrowingRecord"]
    BorrowingUI --> BookModel["Book"]
    BorrowingUI --> MemberModel["Member"]

    ReportingSvc --> BorrowRecord
    ReportingSvc --> BookModel
    ReportingSvc --> MemberModel
    ReportingSvc --> UserRole["User + RoleEnum"]
    ReportingSvc --> Penalty["Penalty/Fine (derived, not persisted)"]

    BorrowRecord --> DB[("SQLite library_v2.db")]
    BookModel --> DB
    MemberModel --> DB
    UserRole --> DB
```

### Notes

- Overdue state is synchronized from real borrowing data (`due_date`, `return_date`, `status`).
- Fine/Penalty is modeled as a derived value from `days_overdue` (presentation/reporting level); there is currently no dedicated fine table.

## 2. Context / External System Model

System boundary and external interactions for Sprint 3 reporting:

```mermaid
flowchart TB
    Admin["Admin"] --> ReportingUI
    Librarian["Librarian"] --> ReportingUI
    Assistant["Assistant"] --> ReportingUI
    MemberActor["Member (library customer)"] --> BorrowingOps

    Database[("SQLite Database")]
    FileSystem[("Local File System")]

    subgraph LMS["Library Management System (Project Boundary)"]
        Auth["Authentication + Role Session<br/>(login_window.py, auth.py)"]
        ReportingUI["Reporting/Dashboard UI<br/>(views/reports.py, views/dashboard.py)"]
        BorrowingOps["Borrowing Operations<br/>(views/members.py, views/borrowing.py)"]
        ReportingService["Reporting Service<br/>(reporting.py)"]
        Domain["Domain Model<br/>(Book, Member, BorrowingRecord, User)"]
    end

    Auth --> ReportingUI
    BorrowingOps --> Domain
    ReportingUI --> ReportingService
    ReportingService --> Domain
    Domain --> Database
    ReportingUI --> FileSystem
```

### Boundary Clarification

- **Inside boundary:** UI modules, reporting service, domain models, and SQLite access.
- **Outside boundary:** human actors (`Admin`, `Librarian`, `Assistant`, `Member`) and local file system as external storage surface.

## 3. Selected Model: Activity Diagram (Overdue Books Reporting)

```mermaid
flowchart TD
    A([Start]) --> B["User logs in and opens Reports tab"]
    B --> C{"Authenticated session exists?"}
    C -- No --> Z1["Stop (return to login)"] --> Z([End])
    C -- Yes --> D["Reports screen calls refresh_data()"]
    D --> E["reporting.fetch_overdue_records()"]
    E --> F["sync_overdue_records(): ACTIVE -> OVERDUE if due_date < now and not returned"]
    F --> G["Query BorrowingRecord + Member + Book from DB"]
    G --> H{"For each record: overdue conditions satisfied?"}
    H -- No --> H2["Skip record"] --> H
    H -- Yes --> I["Calculate days_overdue"]
    I --> J{"Penalty policy enabled?"}
    J -- Yes --> K["Estimate penalty from days_overdue (derived only)"]
    J -- No --> L["No penalty estimate"]
    K --> M["Append row to overdue result list"]
    L --> M
    M --> H
    H --> N["Update overdue table + summary cards"]
    N --> O{"User requests date-range summary?"}
    O -- No --> Z
    O -- Yes --> P["Validate start/end date"]
    P --> Q{"Validation passed?"}
    Q -- No --> R["Show validation warning"] --> Z
    Q -- Yes --> S["fetch_borrowing_summary() and display metrics"] --> Z
```

### Implementation Mapping

- Activity nodes `D/E/F/G/N` map directly to `views/reports.py` and `reporting.py`.
- Data sources in `G` map to `BorrowingRecord`, `Book`, and `Member` entities in `models.py`.
- Authentication/role context in `B/C` maps to existing login + session flow (`login_window.py`, `main.py`, `main_window.py`).
