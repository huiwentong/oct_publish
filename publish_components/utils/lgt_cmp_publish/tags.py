from __future__ import annotations


# Verified read-only against ShotGrid on 2026-08-18.
# The order matches the legacy LG/CMP publisher UI.
LEGACY_REVIEW_TAGS = (
    (339, "P1"),
    (1017, "P2"),
    (340, "P3"),
    (282, "测试"),
)

LEGACY_REVIEW_TAG_IDS = tuple(tag_id for tag_id, _ in LEGACY_REVIEW_TAGS)


def configure_required_tag_combo(combo) -> None:
    """
    Add the legacy empty placeholder and require an explicit selection.

    The framework already rejects an item whose user data is None. Inserting
    that placeholder at index zero therefore reproduces the legacy behavior:
    the form initially looks unselected and cannot continue until the artist
    chooses P1, P2, P3 or 测试.
    """
    has_placeholder = (
        combo.count() > 0
        and combo.itemText(0) == ""
        and combo.itemData(0) is None
    )
    if not has_placeholder:
        combo.insertItem(0, "", None)
    combo.setCurrentIndex(0)
