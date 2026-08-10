# landonkea-cli-tools - Design & Workflow

## High-Level Overview

```mermaid
graph TB
    subgraph "landonkea-cli-tools"
        A[file_organizer.py] --> B[Organize files by type]
        C[disk_usage.py] --> D[Show disk usage]
        E[text_tools.py] --> F[Text processing]
        G[system_info.py] --> H[System information]
    end

    subgraph "Shared Patterns"
        I[argparse] --> A
        I --> C
        I --> E
        I --> G
        J[pathlib] --> A
        J --> C
    end
```

## File Organizer Workflow

```mermaid
flowchart TD
    A[User runs script] --> B[Parse arguments]
    B --> C[Scan directory]
    C --> D[Group files by extension]
    D --> E[Create category folders]
    E --> F[Move files]
    F --> G[Print summary]
```

## Disk Usage Workflow

```mermaid
flowchart TD
    A[User runs script] --> B[Parse arguments]
    B --> C[Walk directory tree]
    C --> D[Calculate sizes]
    D --> E[Sort by size]
    E --> F[Print formatted output]
```

## File Relationships

| File | Purpose | Used By |
|------|---------|---------|
| `file_organizer.py` | Organize files by type | CLI |
| `disk_usage.py` | Show disk usage | CLI |
| `text_tools.py` | Text processing | CLI |
| `system_info.py` | System information | CLI |
| `tests/` | Test scripts | `pytest` |

## draw.io

[Open in draw.io](https://app.diagrams.net/#RCLI%20tools%20architecture)
