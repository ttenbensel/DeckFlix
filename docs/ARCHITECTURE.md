
# DeckFlix Architecture

## Vision

DeckFlix is a shipboard media management system built around Jellyfin.

Jellyfin plays the media.

DeckFlix manages the media.

---

## Design Goals

- Safe before fast
- Never overwrite without approval
- Never delete without confirmation
- Designed for unreliable and low-bandwidth environments
- Terminal-first interface
- Modular architecture
- Easy to maintain

---

## Components

### Shuttle Manager

Detects and analyses incoming shuttle drives.

### Import Engine

Plans and safely imports approved media.

### Library Intelligence

Scans and analyses the complete media library.

### Inspectors

Dedicated tools for investigating:

- Duplicate media
- Quality
- TV episodes
- Folder structure
- Unknown media

### Jellyfin Manager

Synchronises with Jellyfin and refreshes libraries.

### Ship Mode

Optimises behaviour while at sea.

---

## Philosophy

Importing is only one feature.

The long-term goal is intelligent media library management.
