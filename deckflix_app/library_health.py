from pathlib import Path

from deckflix_app.config import load_config
from deckflix_app.health import (
    library_report,
    quality_score,
    size_gb,
)
from deckflix_app.library import (
    DuplicateClassification,
    LibraryAudit,
    LibraryIssue,
    LibraryRepairPlan,
    LibraryRepairStatus,
    audit_libraries,
    build_library_repair_plan,
    current_deckflix_library_roots,
)
from deckflix_app.library.repair_operation import (
    LibraryRepairExecutor,
    RepairOperationManager,
    RepairOperationState,
    RepairOperationTransitionError,
)
from deckflix_app.metadata.quality_verification import (
    verify_quality,
)
from deckflix_app.library.integrity import (
    MediaIntegrityStatus,
    classify_media_integrity,
)
from deckflix_app.metadata.probe import probe_media


ISSUE_LABELS = {
    LibraryIssue.MISPLACED: "Misplaced Media",
    LibraryIssue.LEGACY_LOCATION: "Legacy Location",
    LibraryIssue.DUPLICATE_CANDIDATE: "Duplicate Candidates",
    LibraryIssue.STRUCTURE_REVIEW: "Structure Review",
    LibraryIssue.WEAK_METADATA: "Weak Metadata",
}


def _format_size(value):
    gib = value / 1024**3

    if gib >= 1024:
        return f"{gib / 1024:.2f} TiB"

    return f"{gib:.2f} GiB"


def _identity(media):
    text = media.title

    if media.year is not None:
        text += f" ({media.year})"

    if (
        media.media_type == "tv"
        and media.season is not None
        and media.episode is not None
    ):
        text += (
            f" S{media.season:02d}"
            f"E{media.episode:02d}"
        )

    return text


def _show_issue_entries(
    audit,
    issue,
):
    entries = [
        entry
        for entry in audit.entries
        if issue in entry.issues
    ]

    title = ISSUE_LABELS[issue]

    print()
    print(title)
    print("═" * len(title))
    print()

    if not entries:
        print("None found.")

    for number, entry in enumerate(
        entries,
        start=1,
    ):
        print(
            f"{number:>4}. "
            f"{_identity(entry.media)}"
        )
        print(
            f"      Root: "
            f"{entry.root.name}"
        )
        print(
            f"      Type: "
            f"{entry.media.media_type}"
        )
        print(
            f"      Path: "
            f"{entry.relative_path}"
        )

    if entries:
        print()
        print(f"Total: {len(entries)}")

    print()
    print("No files have been changed.")


DUPLICATE_CLASSIFICATION_LABELS = {
    DuplicateClassification.LEGACY_DUPLICATE:
        "Legacy duplicate",
    DuplicateClassification.LIKELY_EXACT_DUPLICATE:
        "Likely exact duplicate",
    DuplicateClassification.BETTER_QUALITY:
        "Better quality available",
    DuplicateClassification.QUALITY_VARIANT:
        "Quality variant",
    DuplicateClassification.POSSIBLE_FALSE_POSITIVE:
        "Possible false positive",
}


DUPLICATE_CLASSIFICATION_REASONS = {
    DuplicateClassification.LEGACY_DUPLICATE:
        "The same media identity exists in both a primary "
        "and a legacy library location.",
    DuplicateClassification.LIKELY_EXACT_DUPLICATE:
        "The files have the same media identity, matching "
        "quality characteristics, and the same file size.",
    DuplicateClassification.BETTER_QUALITY:
        "One version has a uniquely higher quality score "
        "with a known quality difference.",
    DuplicateClassification.QUALITY_VARIANT:
        "The files share the same media identity, but the "
        "available metadata does not safely establish one "
        "version as superior.",
    DuplicateClassification.POSSIBLE_FALSE_POSITIVE:
        "The duplicate identity may represent split-part "
        "media rather than two independent copies.",
}


def _show_duplicate_classification_summary(
    audit,
):
    counts = {
        classification: 0
        for classification in DuplicateClassification
    }

    for classification in (
        audit.duplicate_classifications.values()
    ):
        counts[classification] += 1

    print("Classification Summary")
    print("──────────────────────")

    for classification in DuplicateClassification:
        print(
            f"{DUPLICATE_CLASSIFICATION_LABELS[classification]:<28}"
            f"{counts[classification]:>5}"
        )

    print()


def _show_duplicate_groups(audit):
    print()
    print("Duplicate Candidates")
    print("════════════════════")
    print()

    groups = list(
        audit.duplicate_groups.items()
    )

    if not groups:
        print("None found.")
        print()
        print("No files have been changed.")
        return

    _show_duplicate_classification_summary(
        audit
    )

    for number, (
        key,
        entries,
    ) in enumerate(
        groups,
        start=1,
    ):
        if key[0] == "movie":
            title = entries[0].media.title

            if key[2] is not None:
                title += f" ({key[2]})"

        else:
            title = (
                f"{entries[0].media.title} "
                f"S{key[2]:02d}"
                f"E{key[3]:02d}"
            )

        classification = (
            audit.duplicate_classifications.get(
                key
            )
        )

        print(
            f"{number:>4}. {title}"
        )

        if classification is not None:
            classification_label = (
                DUPLICATE_CLASSIFICATION_LABELS.get(
                    classification,
                    classification.value,
                )
            )
            classification_reason = (
                DUPLICATE_CLASSIFICATION_REASONS.get(
                    classification,
                    "Operator review required.",
                )
            )

            print(
                f"      Classification: "
                f"{classification_label}"
            )
            print(
                f"      Code:           "
                f"{classification.value}"
            )
            print(
                f"      Reason:         "
                f"{classification_reason}"
            )

        for entry in entries:
            media = entry.media

            print(
                f"      [{entry.root.name}]"
            )
            print(
                f"        Path:         "
                f"{entry.relative_path}"
            )
            print(
                f"        Size:         "
                f"{_format_size(media.size)}"
            )
            print(
                f"        Resolution:   "
                f"{media.resolution or '-'}"
            )
            print(
                f"        Source:       "
                f"{media.source or '-'}"
            )
            print(
                f"        Codec:        "
                f"{media.video_codec or '-'}"
            )

            verification = verify_quality(
                media
            )

            if (
                verification is not None
                and verification.changed
            ):
                verified_resolution = (
                    verification.resolution
                    or "-"
                )
                verified_codec = (
                    verification.video_codec
                    or "-"
                )

                print(
                    f"        Verified:     "
                    f"{verified_resolution} / "
                    f"{verified_codec}"
                )

        print()

    print(
        f"Groups: {len(groups)}"
    )
    print(
        "Candidate files: "
        f"{sum(len(group) for _, group in groups)}"
    )

    print()
    print("READ-ONLY")
    print(
        "Duplicate classification is informational only."
    )
    print(
        "No files have been changed."
    )


def _show_summary(audit):
    summary = audit.summary

    print()
    print("Library Health")
    print("══════════════")
    print()

    print("Library Inventory")
    print("─────────────────")
    print(
        f"Total videos          "
        f"{summary.total_videos}"
    )
    print(
        f"Movies                "
        f"{summary.movie_videos}"
    )
    print(
        f"TV                    "
        f"{summary.tv_videos}"
    )
    print(
        f"Total size            "
        f"{_format_size(summary.total_bytes)}"
    )

    print()
    print("Audit")
    print("─────")
    print(
        f"Correct               "
        f"{summary.correct}"
    )
    print(
        f"Misplaced             "
        f"{summary.misplaced}"
    )
    print(
        f"Legacy location       "
        f"{summary.legacy}"
    )
    print(
        f"Duplicate candidates  "
        f"{summary.duplicate_candidates}"
    )
    print(
        f"Structure review      "
        f"{summary.structure_review}"
    )
    print(
        f"Weak metadata         "
        f"{summary.weak_metadata}"
    )
    print(
        f"Duplicate groups      "
        f"{len(audit.duplicate_groups)}"
    )

    print()
    print("Read-only audit.")
    print("No files have been changed.")


def _show_media_integrity(
    audit,
):
    """Run a simple read-only integrity check."""
    total = len(audit.entries)

    counts = {
        status: 0
        for status in MediaIntegrityStatus
    }
    problems = []

    print()
    print("Media Integrity")
    print("═══════════════")
    print()
    print(f"Files to check: {total}")
    print()
    print("READ-ONLY")
    print("No files will be changed.")
    print()

    for number, entry in enumerate(
        audit.entries,
        start=1,
    ):
        media = entry.media

        if media.path is None:
            continue

        if (
            number == 1
            or number % 50 == 0
            or number == total
        ):
            print(
                f"Checking {number}/{total}"
            )

        technical = probe_media(
            media.path
        )
        result = classify_media_integrity(
            media,
            technical,
        )

        counts[result.status] += 1

        if result.status in {
            MediaIntegrityStatus.CORRUPT,
            MediaIntegrityStatus.SUSPICIOUS,
        }:
            problems.append(
                (media, result)
            )

    print()
    print("Results")
    print("───────")
    print(
        "Healthy          "
        f"{counts[MediaIntegrityStatus.HEALTHY]}"
    )
    print(
        "Needs Review     "
        f"{counts[MediaIntegrityStatus.SUSPICIOUS]}"
    )
    print(
        "Bad Media        "
        f"{counts[MediaIntegrityStatus.CORRUPT]}"
    )
    print(
        "Ignored Extras   "
        f"{counts[MediaIntegrityStatus.AUXILIARY]}"
    )

    print()
    print("Problems")
    print("────────")

    if not problems:
        print("None found.")
    else:
        for media, result in problems:
            print()
            print(_identity(media))

            if (
                result.status
                == MediaIntegrityStatus.CORRUPT
            ):
                print("  Bad Media")
            else:
                print("  Needs Review")

            print(
                f"  {media.path}"
            )

            for reason in result.reasons:
                print(
                    f"  {reason}"
                )

    print()
    print("READ-ONLY")
    print("No files have been changed.")


def _show_repair_plan_summary(
    plan: LibraryRepairPlan,
):
    print()
    print("Library Repair Plan")
    print("═══════════════════")
    print()

    print(
        f"Planned       {len(plan.items)}"
    )
    print(
        f"Ready         "
        f"{plan.count(LibraryRepairStatus.READY)}"
    )
    print(
        f"Review        "
        f"{plan.count(LibraryRepairStatus.REVIEW)}"
    )
    print(
        f"Blocked       "
        f"{plan.count(LibraryRepairStatus.BLOCKED)}"
    )

    print()
    print("READ-ONLY")
    print("No files will be changed.")


def _show_repair_items(
    plan: LibraryRepairPlan,
    status: LibraryRepairStatus,
):
    items = [
        item
        for item in plan.items
        if item.status is status
    ]

    title = f"{status.value} Repairs"

    print()
    print(title)
    print("═" * len(title))
    print()

    if not items:
        print("None.")

    for number, item in enumerate(
        items,
        start=1,
    ):
        print(
            f"{number:>4}. "
            f"{_identity(item.media)}"
        )
        print(
            f"      Action:   "
            f"{item.action.value}"
        )
        print(
            f"      Current:  "
            f"{item.source}"
        )
        print(
            f"      Proposed: "
            f"{item.destination or '-'}"
        )
        print(
            f"      Reason:   "
            f"{item.reason}"
        )
        print()

    if items:
        print(f"Total: {len(items)}")

    print()
    print("READ-ONLY")
    print("No files have been changed.")


def _build_repair_plan(
    audit: LibraryAudit,
) -> LibraryRepairPlan:
    roots = current_deckflix_library_roots()

    movies_root = next(
        root.path
        for root in roots
        if root.name == "Primary Movies"
    )

    tv_root = next(
        root.path
        for root in roots
        if root.name == "Primary TV"
    )

    return build_library_repair_plan(
        audit,
        movies_root=movies_root,
        tv_root=tv_root,
    )


def _repair_operation_path() -> Path:
    config = load_config()

    return (
        Path(config.report_directory)
        / "library-repair-operation.json"
    )


def _create_repair_operation(
    plan: LibraryRepairPlan,
) -> RepairOperationManager:
    return RepairOperationManager(
        plan,
        journal_path=_repair_operation_path(),
    )


def _approve_repair_operation(
    manager: RepairOperationManager,
    plan: LibraryRepairPlan,
):
    ready_count = len(plan.ready)
    review_count = len(plan.review)
    blocked_count = len(plan.blocked)

    print()
    print("Approve Repair Operation")
    print("════════════════════════")
    print()

    print(
        f"READY repairs       {ready_count}"
    )
    print(
        f"REVIEW items        {review_count}"
    )
    print(
        f"BLOCKED items       {blocked_count}"
    )
    print()

    print(
        "Only READY repairs will be "
        "fingerprinted and approved."
    )
    print(
        "REVIEW and BLOCKED items will "
        "remain excluded."
    )
    print()
    print(
        "This does NOT enable write access."
    )
    print(
        "This does NOT move, rename, copy, "
        "or delete media."
    )
    print()

    confirmation = input(
        "Approve these READY repairs? [y/N]: "
    ).strip().casefold()

    if confirmation != "y":
        print()
        print("Approval cancelled.")
        return

    try:
        approved = manager.approve()
    except Exception as exc:
        print()
        print("Approval failed.")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print()
    print(
        f"Approved repairs: {approved}"
    )
    print(
        f"Operation ID:     "
        f"{manager.operation_id}"
    )
    print(
        f"State:             "
        f"{manager.state.value}"
    )
    print(
        "Write authorization: DISABLED"
    )
    print()
    print(
        "Source fingerprints have been persisted."
    )
    print(
        "No media files have been changed."
    )

    input(
        "\nPress Enter to continue..."
    )


def _repair_preflight_progress(
    index,
    total,
    repair,
):
    source = repair.source
    size_gb = repair.snapshot.size / (1024 ** 3)

    print(
        f"\rVerifying source {index}/{total}: "
        f"{source.name}"
        + " " * 20,
        end="",
        flush=True,
    )

    print(
        f"\n  Size: {size_gb:.2f} GiB",
        flush=True,
    )


def _show_final_preflight(
    manager: RepairOperationManager,
):
    print()
    print("Final Read-Only Preflight")
    print("══════════════════════════")
    print()

    print(
        "Verifying approved source fingerprints..."
    )
    print()

    try:
        result = manager.final_preflight(
            progress_callback=_repair_preflight_progress,
        )
        print()
    except Exception as exc:
        print(
            f"Preflight failed: "
            f"{type(exc).__name__}: {exc}"
        )
        print()
        print(
            "READ-ONLY PREFLIGHT"
        )
        print(
            "No files have been changed."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print(
        f"Operation ID             "
        f"{result.operation_id}"
    )
    print(
        f"Approved files           "
        f"{result.approved_files}"
    )
    print(
        f"Approved bytes           "
        f"{_format_size(result.approved_bytes)}"
    )
    print(
        f"Source missing           "
        f"{result.source_missing}"
    )
    print(
        f"Source changed           "
        f"{result.source_changed}"
    )
    print(
        f"Destination conflicts    "
        f"{result.destination_conflicts}"
    )
    print(
        f"Destination unavailable  "
        f"{result.destination_not_writable}"
    )
    print(
        f"Invalid items            "
        f"{result.invalid_items}"
    )
    print()

    if result.ready:
        print("PREFLIGHT: READY")
        print(
            "All approved sources match "
            "their stored fingerprints."
        )
        print(
            "No destination conflicts detected."
        )
        print(
            "Write authorization is still "
            "DISABLED."
        )
    else:
        print("PREFLIGHT: NOT READY")

        if result.reasons:
            print()
            for reason in result.reasons:
                print(f"- {reason}")

    print()
    print("READ-ONLY PREFLIGHT")
    print("No files have been changed.")

    input(
        "\nPress Enter to continue..."
    )


def _authorize_repair_operation(
    manager: RepairOperationManager,
):
    print()
    print("Authorize Repair Mode")
    print("═════════════════════")
    print()

    if manager.state is not RepairOperationState.APPROVED:
        print(
            "Authorization requires an "
            "APPROVED operation."
        )
        print(
            f"Current state: "
            f"{manager.state.value}"
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print(
        "This is the final write-access gate."
    )
    print()
    print(
        "Authorization will:"
    )
    print(
        "  • re-run the final preflight"
    )
    print(
        "  • verify all approved source "
        "fingerprints"
    )
    print(
        "  • verify destination safety"
    )
    print(
        "  • grant write authorization only "
        "to this approved repair operation"
    )
    print(
        "  • keep global Library Protection enabled"
    )
    print()
    print(
        "Authorization does NOT execute "
        "the repair."
    )
    print(
        "No media is moved, renamed, copied, "
        "or deleted by this step."
    )
    print()

    confirmation = input(
        "Enable Repair Mode? [y/N]: "
    ).strip().casefold()

    if confirmation != "y":
        print()
        print("Authorization cancelled.")
        input(
            "\nPress Enter to continue..."
        )
        return

    config = load_config()

    print()
    print(
        "FINAL READ-ONLY PREFLIGHT"
    )
    print(
        "──────────────────────────"
    )
    print()
    print(
        "Verifying approved source fingerprints..."
    )
    print(
        "No media files will be modified during "
        "this verification."
    )
    print()

    try:
        result = manager.final_preflight(
            progress_callback=_repair_preflight_progress,
        )

        print()

        if not result.ready:
            raise RepairOperationTransitionError(
                "Final repair preflight failed: "
                + "; ".join(
                    result.reasons
                )
            )

        # The manager performs the same state transition and
        # persists the authorization. Its internal preflight is
        # deliberately retained as a second safety gate.
        result = manager.authorize(
            config
        )
    except Exception as exc:
        print()
        print("AUTHORIZATION BLOCKED")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print()
        print(
            "Operation state remains:"
            f" {manager.state.value}"
        )
        print(
            "Write authorization:"
            f" {'ENABLED' if manager.write_authorized else 'DISABLED'}"
        )
        print()
        print(
            "No media files have been changed."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print()
    print("REPAIR MODE AUTHORIZED")
    print("───────────────────────")
    print()
    print(
        f"Operation ID:      "
        f"{manager.operation_id}"
    )
    print(
        f"State:             "
        f"{manager.state.value}"
    )
    print(
        f"Approved files:    "
        f"{result.approved_files}"
    )
    print(
        f"Approved bytes:    "
        f"{_format_size(result.approved_bytes)}"
    )
    print(
        "Write authorization: ENABLED"
    )
    print()
    print(
        "IMPORTANT:"
    )
    print(
        "Authorization has NOT executed "
        "the repair."
    )
    print(
        "No media files have been changed."
    )

    input(
        "\nPress Enter to continue..."
    )


def _revoke_repair_authorization(
    manager: RepairOperationManager,
):
    manager.revoke_authorization()

    print()
    print("Repair authorization revoked.")
    print(
        f"State: "
        f"{manager.state.value}"
    )
    print(
        "Write authorization: DISABLED"
    )
    print()
    print("No files have been changed.")

    input(
        "\nPress Enter to continue..."
    )


def _show_approved_repairs(
    manager: RepairOperationManager,
):
    print()
    print("Approved Repairs")
    print("════════════════")
    print()

    if not manager.approved_repairs:
        print("No approved repairs.")
        print()
        print("No files have been changed.")
        input(
            "\nPress Enter to continue..."
        )
        return

    print(
        f"Approved repairs: "
        f"{len(manager.approved_repairs)}"
    )
    print()

    for number, repair in enumerate(
        manager.approved_repairs,
        start=1,
    ):
        print(
            f"{number:02d}. {repair.source}"
        )
        print(
            f"    -> {repair.destination}"
        )
        print(
            f"    {repair.action.value}"
        )
        print(
            f"    SHA-256: "
            f"{repair.snapshot.checksum}"
        )
        print()

    print(
        "No files have been changed."
    )

    input(
        "\nPress Enter to continue..."
    )


def _execute_repair_operation(
    manager: RepairOperationManager,
):
    print()
    print("Execute Repair Operation")
    print("════════════════════════")
    print()

    if manager.state is not RepairOperationState.AUTHORIZED:
        print(
            "EXECUTION BLOCKED"
        )
        print(
            "Repair Mode is not authorized."
        )
        print(
            f"State: {manager.state.value}"
        )
        print(
            "No media files have been changed."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    if not manager.write_authorized:
        print(
            "EXECUTION BLOCKED"
        )
        print(
            "Write authorization is disabled."
        )
        print(
            "No media files have been changed."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print(
        "Verifying approved source fingerprints..."
    )
    print()

    try:
        preflight = manager.final_preflight(
            progress_callback=_repair_preflight_progress,
        )
        print()
    except Exception as exc:
        print()
        print("EXECUTION BLOCKED")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print()
        print(
            "No media files have been changed."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print(
        "Final Read-Only Preflight"
    )
    print("──────────────────────────")
    print()

    print(
        f"Operation ID       "
        f"{manager.operation_id}"
    )
    print(
        f"Approved files     "
        f"{preflight.approved_files}"
    )
    print(
        f"Approved bytes     "
        f"{_format_size(preflight.approved_bytes)}"
    )
    print(
        f"Source missing     "
        f"{preflight.source_missing}"
    )
    print(
        f"Source changed     "
        f"{preflight.source_changed}"
    )
    print(
        f"Destination conflicts "
        f"{preflight.destination_conflicts}"
    )
    print(
        f"Destination unavailable "
        f"{preflight.destination_not_writable}"
    )
    print(
        f"Invalid items      "
        f"{preflight.invalid_items}"
    )
    print()

    if not preflight.ready:
        print(
            "EXECUTION BLOCKED"
        )
        print(
            "Final preflight is not ready."
        )

        if preflight.reasons:
            print()
            print("Reasons")
            print("───────")

            for reason in preflight.reasons:
                print(
                    f"• {reason}"
                )

        print()
        print(
            "No media files have been changed."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print(
        "⚠️  THIS WILL MODIFY THE FILESYSTEM"
    )
    print()
    print(
        "Each approved repair will:"
    )
    print(
        "  • copy the source to a temporary destination"
    )
    print(
        "  • verify the copied file with SHA-256"
    )
    print(
        "  • re-check the approved source fingerprint"
    )
    print(
        "  • publish the destination"
    )
    print(
        "  • remove the original source only after verification"
    )
    print()
    print(
        "Existing destinations will NOT be overwritten."
    )
    print(
        "Review and blocked items are NOT included."
    )
    print()
    print(
        "Global Library Protection remains enabled."
    )
    print(
        "Only this explicitly authorized repair operation "
        "has write authorization."
    )
    print()

    confirmation = input(
        "Execute these repairs? [y/N]: "
    ).strip().casefold()

    if confirmation != "y":
        print()
        print(
            "Execution cancelled."
        )
        print(
            "No media files have been changed."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print()
    print(
        "EXECUTING REPAIR OPERATION"
    )
    print("───────────────────────────")
    print()

    config = load_config()

    try:
        result = LibraryRepairExecutor().execute(
            manager,
            config=config,
        )
    except Exception as exc:
        print()
        print(
            "REPAIR EXECUTION STOPPED"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print()
        print(
            f"Operation state: "
            f"{manager.state.value}"
        )
        print(
            "Write authorization: "
            f"{'ENABLED' if manager.write_authorized else 'DISABLED'}"
        )
        print()
        print(
            "Review the operation journal before "
            "attempting any further repair."
        )
        input(
            "\nPress Enter to continue..."
        )
        return

    print()
    print(
        "REPAIR OPERATION COMPLETE"
    )
    print("──────────────────────────")
    print()
    print(
        f"Operation ID:     "
        f"{result.operation_id}"
    )
    print(
        f"Completed:        "
        f"{result.completed}"
    )
    print(
        f"Failed:           "
        f"{result.failed}"
    )
    print(
        f"Paused:           "
        f"{'YES' if result.paused else 'NO'}"
    )
    print(
        f"Final state:      "
        f"{manager.state.value}"
    )
    print(
        "Write authorization: "
        f"{'ENABLED' if manager.write_authorized else 'DISABLED'}"
    )
    print()

    if result.successful:
        print(
            "All approved repairs completed successfully."
        )
        print(
            "SHA-256 verification completed."
        )
        print(
            "Authorization has been revoked."
        )
    else:
        print(
            "The operation did not complete successfully."
        )
        print(
            "Review the operation journal."
        )

    input(
        "\nPress Enter to continue..."
    )


def _show_repair_operation(
    plan: LibraryRepairPlan,
):
    manager = _create_repair_operation(
        plan
    )

    while True:
        print()
        print("Repair Operation")
        print("════════════════")
        print()

        print(
            f"Operation ID       "
            f"{manager.operation_id}"
        )
        print(
            f"State              "
            f"{manager.state.value}"
        )
        print(
            "Write Authorization "
            f"{'ENABLED' if manager.write_authorized else 'DISABLED'}"
        )
        print(
            f"Approved repairs   "
            f"{len(manager.approved_repairs)}"
        )
        print(
            f"Journal entries    "
            f"{len(manager.journal.entries)}"
        )
        print()

        if manager.state is RepairOperationState.CREATED:
            print(
                "Operation has been created "
                "but not approved."
            )
            print()
            print("Actions")
            print("───────")
            print("1. Approve READY Repairs")
            print("2. Back")
            print()

            choice = input(
                "Select option: "
            ).strip()

            if choice == "1":
                _approve_repair_operation(
                    manager,
                    plan,
                )
                continue

            if choice == "2":
                return

            print("Invalid option.")
            continue

        if manager.state is RepairOperationState.APPROVED:
            print(
                "Operation is approved."
            )
            print(
                "Write authorization remains "
                "DISABLED."
            )
            print()
            print("Actions")
            print("───────")
            print(
                "1. Final Read-Only Preflight"
            )
            print(
                "2. Review Approved Repairs"
            )
            print(
                "3. Authorize Repair Mode"
            )
            print(
                "4. Revoke Approval"
            )
            print("5. Back")
            print()

            choice = input(
                "Select option: "
            ).strip()

            if choice == "1":
                _show_final_preflight(
                    manager
                )
                continue

            if choice == "2":
                _show_approved_repairs(
                    manager
                )
                continue

            if choice == "3":
                _authorize_repair_operation(
                    manager
                )
                continue

            if choice == "4":
                _revoke_repair_authorization(
                    manager
                )
                continue

            if choice == "5":
                return

            print("Invalid option.")
            continue

        if manager.state is RepairOperationState.AUTHORIZED:
            print(
                "Repair Mode is AUTHORIZED."
            )
            print()
            print(
                "The executor is available."
            )
            print(
                "Execution requires a fresh "
                "final preflight and explicit "
                "confirmation."
            )
            print()
            print("Actions")
            print("───────")
            print(
                "1. Final Read-Only Preflight"
            )
            print(
                "2. Review Approved Repairs"
            )
            print(
                "3. Execute Repair"
            )
            print(
                "4. Revoke Authorization"
            )
            print("5. Back")
            print()

            choice = input(
                "Select option: "
            ).strip()

            if choice == "1":
                _show_final_preflight(
                    manager
                )
                continue

            if choice == "2":
                _show_approved_repairs(
                    manager
                )
                continue

            if choice == "3":
                _execute_repair_operation(
                    manager
                )
                continue

            if choice == "4":
                _revoke_repair_authorization(
                    manager
                )
                continue

            if choice == "5":
                return

            print("Invalid option.")
            continue

        print(
            f"Operation state: "
            f"{manager.state.value}"
        )
        print(
            "This state is not currently "
            "executable from the UI."
        )
        print()
        print("1. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":
            return


def _show_repair_plan(
    audit,
):
    plan = _build_repair_plan(
        audit
    )

    while True:
        _show_repair_plan_summary(
            plan
        )

        print()
        print("Review")
        print("──────")
        print("1. Review READY Repairs")
        print(
            "2. Review Items "
            "Requiring Attention"
        )
        print("3. Review Blocked Repairs")
        print("4. Repair Operation")
        print("5. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":
            _show_repair_items(
                plan,
                LibraryRepairStatus.READY,
            )
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "2":
            _show_repair_items(
                plan,
                LibraryRepairStatus.REVIEW,
            )
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "3":
            _show_repair_items(
                plan,
                LibraryRepairStatus.BLOCKED,
            )
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "4":
            _show_repair_operation(
                plan
            )

        elif choice == "5":
            return

        else:
            print("Invalid option.")


def show_library_health(
    movies_path=None,
    tv_path=None,
):
    audit = audit_libraries(
        current_deckflix_library_roots()
    )

    while True:
        _show_summary(audit)

        summary = audit.summary

        print()
        print("Review")
        print("──────")
        print(
            f"1. Misplaced Media          "
            f"{summary.misplaced}"
        )
        print(
            f"2. Legacy Location         "
            f"{summary.legacy}"
        )
        print(
            f"3. Duplicate Candidates    "
            f"{summary.duplicate_candidates}"
        )
        print(
            f"4. Structure Review         "
            f"{summary.structure_review}"
        )
        print(
            f"5. Weak Metadata           "
            f"{summary.weak_metadata}"
        )
        print("6. Media Integrity")
        print("7. Repair Plan")
        print("8. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":
            _show_issue_entries(
                audit,
                LibraryIssue.MISPLACED,
            )
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "2":
            _show_issue_entries(
                audit,
                LibraryIssue.LEGACY_LOCATION,
            )
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "3":
            _show_duplicate_groups(audit)
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "4":
            _show_issue_entries(
                audit,
                LibraryIssue.STRUCTURE_REVIEW,
            )
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "5":
            _show_issue_entries(
                audit,
                LibraryIssue.WEAK_METADATA,
            )
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "6":
            _show_media_integrity(audit)
            input(
                "\nPress Enter to continue..."
            )

        elif choice == "7":
            _show_repair_plan(audit)

        elif choice == "8":
            return

        else:
            print("Invalid option.")
