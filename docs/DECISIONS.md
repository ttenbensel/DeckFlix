
# Architectural Decisions

## GitHub First

GitHub is the only source of truth.

The installed copy is never edited directly.

---

## Development Workflow

Every sprint follows:

1. Edit GitHub
2. Commit
3. Pull
4. Install
5. Test

---

## Safety

DeckFlix must never:

- overwrite media automatically
- delete media automatically

Every destructive action requires user confirmation.

---

## User Experience

The application should guide the user.

Instead of simply reporting problems, DeckFlix should recommend the best action.

---

## Long-term Vision

DeckFlix is not just an import tool.

It is a complete media management platform designed specifically for shipboard Jellyfin installations.
