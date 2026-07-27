from deckflix_app.models.capability import Capability


_CAPABILITIES = {
    "receive": Capability(
        id="receive",
        name="Receive Media",
        description="Import media from a shuttle drive",
        engines=[
            "Policy Engine",
            "Storage Advisor",
            "Import Queue",
            "Import Orchestrator",
        ],
        estimated_steps=6,
    ),

    "export": Capability(
        id="export",
        name="Export Media",
        description="Prepare media for a shuttle",
        engines=[
            "Storage Advisor",
            "Export Planner",
        ],
        estimated_steps=5,
    ),

    "storage": Capability(
        id="storage",
        name="Manage Storage",
        description="Plan and upgrade storage",
        engines=[
            "Storage Planner",
            "Port Planner",
            "Storage Advisor",
        ],
        estimated_steps=4,
    ),

    "library": Capability(
        id="library",
        name="Maintain Library",
        description="Review and repair media",
        engines=[
            "Library Health",
            "Repair Queue",
        ],
        estimated_steps=4,
    ),
}


def capabilities():
    return sorted(
        _CAPABILITIES.values(),
        key=lambda c: c.name,
    )


def capability(capability_id):
    return _CAPABILITIES[capability_id]
