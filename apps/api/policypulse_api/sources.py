import re

from .schemas import SourceItem, SourceType


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def split_policy_paragraphs(policy_text: str) -> list[SourceItem]:
    raw_parts = re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z])", policy_text)
    paragraphs = [normalize_text(part) for part in raw_parts if normalize_text(part)]
    return [
        SourceItem(id=f"POL-{index:03d}", type=SourceType.POLICY, text=text)
        for index, text in enumerate(paragraphs, start=1)
    ]


def create_comment_sources(comments: list[str]) -> list[SourceItem]:
    return [
        SourceItem(
            id=f"COM-{index:03d}",
            type=SourceType.COMMENT,
            text=normalize_text(comment),
        )
        for index, comment in enumerate(comments, start=1)
        if normalize_text(comment)
    ]
