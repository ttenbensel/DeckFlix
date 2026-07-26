from dataclasses import dataclass, field

from deckflix_app.models.library_policy import LibraryPolicy


RESOLUTION_RANK = {
    "unknown": 0,
    "480p": 1,
    "720p": 2,
    "1080p": 3,
    "2160p": 4,
}

CODEC_RANK = {
    "unknown": 0,
    "H264": 1,
    "HEVC": 2,
    "AV1": 3,
}


@dataclass(slots=True)
class PolicyRecommendation:
    """
    Explainable import recommendation.

    Advisory only. Nothing is moved, replaced, or deleted.
    """

    action: str
    confidence: int
    reasons: list[str] = field(default_factory=list)

    existing_score: int = 0
    incoming_score: int = 0

    storage_change_bytes: int = 0

    @property
    def storage_change_gb(self):
        return self.storage_change_bytes / 1024**3


def profile_score(item, policy: LibraryPolicy):
    """
    Score how well one media item matches the selected library policy.
    """

    score = 0

    target_resolution = RESOLUTION_RANK.get(
        policy.preferred_resolution,
        0,
    )
    item_resolution = RESOLUTION_RANK.get(
        item.resolution,
        0,
    )

    if item_resolution == target_resolution:
        score += 40
    elif item_resolution < target_resolution:
        score += max(0, 30 - (target_resolution - item_resolution) * 10)
    else:
        # Above-target resolution is useful, but not automatically ideal.
        score += max(10, 35 - (item_resolution - target_resolution) * 10)

    if item.codec == policy.preferred_codec:
        score += 25
    elif item.codec not in (None, "unknown"):
        score += 10

    maximum_size_gb = (
        policy.maximum_episode_size_gb
        if item.media_type == "tv"
        else policy.maximum_movie_size_gb
    )

    size_gb = item.size / 1024**3 if item.size else 0

    if size_gb <= maximum_size_gb:
        score += 25
    elif size_gb <= maximum_size_gb * 1.5:
        score += 10
    else:
        score -= 15

    if getattr(item, "source", "unknown") != "unknown":
        score += 5

    if getattr(item, "quality_score", 0) > 0:
        score += min(item.quality_score // 10, 5)

    return score


def recommend_import(existing, incoming, policy: LibraryPolicy):
    """
    Compare an existing library copy with an incoming shuttle copy.

    Returns an explainable recommendation:
    KEEP_EXISTING, UPGRADE, REPLACE_EFFICIENTLY, or REVIEW.
    """

    existing_score = profile_score(existing, policy)
    incoming_score = profile_score(incoming, policy)

    storage_change = incoming.size - existing.size
    reasons = []

    if (
        incoming.resolution == existing.resolution
        and incoming.codec == policy.preferred_codec
        and incoming.size < existing.size
        and incoming_score >= existing_score
    ):
        reasons.append(
            "Incoming copy provides similar viewing quality "
            "with better storage efficiency"
        )

        return PolicyRecommendation(
            action="REPLACE_EFFICIENTLY",
            confidence=90,
            reasons=reasons,
            existing_score=existing_score,
            incoming_score=incoming_score,
            storage_change_bytes=storage_change,
        )

    if incoming_score >= existing_score + 15:
        reasons.append(
            f"Incoming copy better matches the {policy.profile} profile"
        )

        if incoming.resolution != existing.resolution:
            reasons.append(
                f"Resolution changes from "
                f"{existing.resolution} to {incoming.resolution}"
            )

        if incoming.codec != existing.codec:
            reasons.append(
                f"Codec changes from "
                f"{existing.codec} to {incoming.codec}"
            )

        return PolicyRecommendation(
            action="UPGRADE",
            confidence=85,
            reasons=reasons,
            existing_score=existing_score,
            incoming_score=incoming_score,
            storage_change_bytes=storage_change,
        )

    if existing_score >= incoming_score:
        reasons.append(
            f"Existing copy already matches the "
            f"{policy.profile} profile as well as or better than "
            f"the incoming copy"
        )

        if storage_change > 0:
            reasons.append(
                f"Importing the incoming copy would use "
                f"an additional {storage_change / 1024**3:.2f} GB"
            )

        return PolicyRecommendation(
            action="KEEP_EXISTING",
            confidence=85,
            reasons=reasons,
            existing_score=existing_score,
            incoming_score=incoming_score,
            storage_change_bytes=storage_change,
        )

    reasons.append(
        "The versions are close enough that manual review is recommended"
    )

    return PolicyRecommendation(
        action="REVIEW",
        confidence=60,
        reasons=reasons,
        existing_score=existing_score,
        incoming_score=incoming_score,
        storage_change_bytes=storage_change,
    )
