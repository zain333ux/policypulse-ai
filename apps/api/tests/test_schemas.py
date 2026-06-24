import pytest
from pydantic import ValidationError

from policypulse_api.demo import build_demo_result
from policypulse_api.schemas import Sentiment


def test_demo_result_has_valid_evidence_references() -> None:
    result = build_demo_result()
    source_ids = {source.id for source in result.sources}
    concern_ids = {concern.id for concern in result.concerns}
    gap_ids = {gap.id for gap in result.gaps}

    assert set(result.policy.evidence_ids) <= source_ids
    assert all(set(concern.evidence_ids) <= source_ids for concern in result.concerns)
    assert all(set(gap.evidence_ids) <= source_ids for gap in result.gaps)
    assert all(set(gap.concern_ids) <= concern_ids for gap in result.gaps)
    assert all(set(item.evidence_ids) <= source_ids for item in result.recommendations)
    assert all(set(item.gap_ids) <= gap_ids for item in result.recommendations)


def test_sentiment_percentages_must_total_100() -> None:
    with pytest.raises(ValidationError):
        Sentiment(support=30, opposition=30, neutral=30, overall_mood="Mixed")
