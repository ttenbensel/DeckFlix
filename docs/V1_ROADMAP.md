# DeckFlix v1.0 Roadmap

## Current Foundation

The repository already contains early implementations of:

- Shuttle scanning
- Media comparison
- Import queues
- Approval workflows
- Import execution
- Library health reporting
- Duplicate inspection
- Repair queues
- Quarantine metadata
- Restore functionality
- Terminal dashboard
- Installer and project documentation

The following roadmap develops these components into a stable v1.0 release.

---

## v0.9.1 — Configuration Foundation

### Goals

- Replace hard-coded storage paths in application code
- Load local paths from `config/local.json`
- Provide a tracked example configuration
- Validate required configuration values
- Show useful errors for missing or inaccessible paths

### Required Settings

- Shuttle path
- Movie library paths
- Television library paths
- Report directory
- Read-only mode
- Operating profile
- Jellyfin settings when enabled

### Completion Criteria

- No deployment-specific storage paths are hard-coded
- Invalid configuration prevents unsafe operations
- A new user can configure DeckFlix without editing Python files

---

## v0.9.2 — Package and Scanner Consolidation

### Goals

- Decide the long-term role of `deckflix/` and `deckflix_app/`
- Establish one authoritative scanner implementation
- Establish one authoritative parser implementation
- Remove or archive duplicated scanner logic
- Preserve stable CLI behaviour

### Parser Requirements

- `S01E01`
- `1x01`
- `S01X01`
- Season-folder layouts
- Multi-episode files
- Movie title and year extraction
- Release-tag cleanup
- Unknown-media classification
- Confidence and review reasons

### Completion Criteria

- All scans use the same parser and models
- Scanner behaviour is covered by automated tests
- Unknown or uncertain media is sent to review rather than guessed

---

## v0.9.3 — Safe Import Workflow

### Goals

- Complete the shuttle-to-library workflow
- Validate source and destination storage
- Prevent overwrites
- Verify copies before reporting success
- Record every completed or failed import
- Support movies and television libraries

### Workflow

1. Detect shuttle
2. Scan media
3. Compare with libraries
4. Build import plan
5. Review and approve
6. Check destination storage
7. Copy
8. Verify
9. Report
10. Offer safe shuttle eject options

### Completion Criteria

- No import occurs without explicit approval
- Every import is logged
- Partial failures are visible and recoverable
- Read-only mode guarantees no file changes

---

## v0.9.4 — Library Intelligence

### Goals

- Improve duplicate grouping
- Rank duplicate quality
- Detect missing television episodes
- Detect sample and junk files
- Detect misplaced movies and television episodes
- Detect malformed folder structures
- Report unknown media

### Completion Criteria

- Recommendations include understandable reasons
- Quality ranking does not automatically delete lower-ranked media
- Results can be reviewed from the terminal interface
- Library health reports remain read-only by default

---

## v0.9.5 — Repair and Restore Hardening

### Goals

- Use a consistent repair plan format
- Record original and proposed paths
- Require confirmation before execution
- Store quarantine metadata beside quarantined files
- Detect restore conflicts
- Test interrupted repair and restore scenarios

### Completion Criteria

- Every repair action has an audit record
- Quarantined files can be traced to their original location
- Restore refuses to overwrite an existing destination without approval
- Failed operations produce actionable reports

---

## v0.9.6 — Storage and Shuttle Management

### Goals

- Support the 2 TB shuttle drive as the media transport drive
- Support the 4 TB drive as the primary media destination
- Detect drive identity rather than relying only on mount paths
- Show capacity, used space, and free space
- Estimate whether an import plan will fit
- Add Empty and Eject
- Add Eject Only
- Refuse unsafe eject operations

### Completion Criteria

- DeckFlix verifies the correct shuttle and destination drives
- Planned imports cannot start without adequate space
- Eject actions are explicit and logged
- Empty and Eject requires additional confirmation

---

## v0.9.7 — Jellyfin Integration

### Goals

- Configure one or more Jellyfin servers
- Test connectivity without blocking offline operation
- Trigger targeted library refreshes
- Confirm whether newly imported media appears in Jellyfin
- Queue refreshes when offline

### Completion Criteria

- Jellyfin is optional
- Jellyfin failures do not invalidate successful file imports
- Credentials remain outside Git
- Refresh activity is visible in reports

---

## v0.9.8 — Ship Mode

### Goals

- Add Normal, Ship, and Ship Low Impact profiles
- Reduce scan frequency and concurrency
- Defer internet-dependent work
- Reduce logging noise while preserving audit records
- Avoid unnecessary library-wide rescans
- Display the active profile and capabilities

### Completion Criteria

- Core media management works offline
- Low Impact mode measurably reduces resource use
- Deferred work is visible and can be resumed
- The current operating profile is always shown

---

## v0.9.9 — Interface and Release Preparation

### Goals

- Stabilise the terminal navigation
- Improve error messages and confirmations
- Add status and diagnostics commands
- Complete installation documentation
- Add upgrade and rollback instructions
- Expand automated tests
- Add GitHub Actions

### Required CLI Commands

- `deckflix status`
- `deckflix scan-shuttle`
- `deckflix emergency-eject`
- `deckflix repair`

### Completion Criteria

- Fresh installation succeeds from documented steps
- Tests run automatically on GitHub
- Configuration and credentials are never committed
- Upgrade and recovery procedures are documented

---

## v1.0.0 — Stable Release

### Release Requirements

- Safe import workflow
- Duplicate and quality analysis
- Missing-episode reporting
- Repair, quarantine, and restore workflows
- Shuttle Empty and Eject and Eject Only
- Configuration-driven storage paths
- Ship Mode with Low Impact option
- Jellyfin refresh integration
- Terminal-friendly interface
- Installation and upgrade documentation
- Automated tests
- Stable configuration format
- Versioned release notes

---

## After v1.0

Potential future work:

- FastAPI service
- React or Vue web interface
- PostgreSQL persistence
- Redis task queues
- Docker Compose deployment
- Sonarr integration
- Radarr integration
- Prowlarr integration
- Multiple host-server management
- Notifications and scheduled reports
