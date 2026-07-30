# DeckFlix Vision

## Mission

DeckFlix is an offline-first, intelligent media management system for Jellyfin.

Jellyfin plays the media.

DeckFlix manages the media.

DeckFlix is designed for ships, remote locations, unreliable networks, removable shuttle drives, and large media libraries where safety and recoverability matter.

---

## Core Responsibilities

DeckFlix manages:

- Media intake from shuttle drives
- Movie and television library organisation
- Duplicate and quality comparison
- Missing television episode detection
- Storage planning and monitoring
- Safe import approval
- Quarantine and repair workflows
- Restore and recovery
- Jellyfin library synchronisation
- Ship Mode and low-impact operation
- Reports, logs, and audit history

DeckFlix does not replace Jellyfin or act as a media player.

---

## Core Principles

### Safety Before Speed

Potentially destructive operations must follow this workflow:

1. Scan
2. Analyse
3. Recommend
4. Approve
5. Execute
6. Verify
7. Record
8. Allow restoration where possible

DeckFlix must not silently overwrite, move, rename, quarantine, or delete media.

### Offline First

Core scanning, comparison, importing, repairing, and restoring must work without internet access.

Internet-dependent features must fail safely and remain optional.

### Reversible Operations

Imports, repairs, moves, renames, and quarantine actions should produce enough metadata to explain and reverse what happened.

### Explain Every Decision

DeckFlix should show why an item was classified, skipped, imported, ranked, quarantined, or recommended for review.

### Terminal Friendly

The terminal interface remains a supported operational interface, even after a web interface is introduced.

### Configuration Driven

Deployment-specific paths and settings belong in configuration files rather than application source code.

### Low-Impact Operation

Ship Mode must reduce unnecessary disk activity, CPU use, network use, metadata refreshes, and background tasks.

---

## Product Areas

### Shuttle Manager

- Detect shuttle drives
- Validate mount and storage status
- Scan incoming media
- Compare shuttle media against destination libraries
- Prepare a safe import plan
- Empty and eject, or eject only, after approval

### Library Intelligence

- Index movies and television episodes
- Identify duplicates
- Rank versions by quality
- Detect missing television episodes
- Detect unknown or misclassified media
- Validate folder structures
- Produce library health reports

### Import Engine

- Build an approval queue
- Show source and destination paths
- Check available storage
- Prevent unintended overwrites
- Copy approved media
- Verify copied files
- Produce import reports

### Repair Engine

- Identify repair candidates
- Preview proposed changes
- Quarantine questionable files
- Record original paths and reasons
- Require approval before execution

### Restore Engine

- Read quarantine and operation metadata
- Restore files to their original locations
- Detect destination conflicts
- Record restoration outcomes

### Jellyfin Manager

- Connect to one or more Jellyfin servers
- Trigger library refreshes after approved imports
- Confirm whether media is indexed
- Defer network operations while offline or in Ship Mode

### Ship Mode

- Operate without internet
- Reduce background scanning
- Defer external integrations
- Limit disk and CPU impact
- Queue work for later execution
- Clearly display the active operating mode

### Reports and Audit History

- Import reports
- Repair reports
- Restore reports
- Storage changes
- Duplicate decisions
- Errors and interrupted operations
- Full action history

---

## Intended User Experience

DeckFlix should always answer these questions:

- What did DeckFlix find?
- What does DeckFlix recommend?
- Why is it recommending that?
- What will change?
- Has the user approved it?
- Did the operation succeed?
- Can the operation be reversed?

The application should feel predictable, cautious, and professional.
