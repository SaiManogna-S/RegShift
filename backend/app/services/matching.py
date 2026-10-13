"""
Impact matching service: matches extracted requirements against the insurance catalogue.
Uses keyword-based matching with confidence scoring.
"""
import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models import InsuranceCatalogueItem, Requirement

logger = logging.getLogger(__name__)


def compute_matches(
    requirement: Requirement,
    catalogue_items: list[InsuranceCatalogueItem],
) -> list[dict[str, Any]]:
    """
    Match a requirement against all catalogue items.
    Returns a list of match dicts with confidence scores.
    """
    matches = []

    req_text = " ".join(filter(None, [
        requirement.summary or "",
        requirement.required_action or "",
        requirement.source_passage or "",
        requirement.line_of_business or "",
        requirement.jurisdiction or "",
        requirement.change_category or "",
    ])).lower()

    for item in catalogue_items:
        score, reasons = _score_match(requirement, item, req_text)

        if score > 0:
            confidence = _score_to_confidence(score)
            matches.append({
                "catalogue_item_id": item.id,
                "confidence": confidence,
                "score": score,
                "match_reason": " | ".join(reasons),
                "suggested_action": _generate_suggested_action(requirement, item, confidence),
            })

    # Sort by score descending
    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches


def _score_match(
    req: Requirement,
    item: InsuranceCatalogueItem,
    req_text: str,
) -> tuple[float, list[str]]:
    """Return (score, reasons) for a requirement-item pair."""
    score = 0.0
    reasons = []

    item_text = " ".join(filter(None, [
        item.name or "",
        item.description or "",
        item.keywords or "",
        item.jurisdiction or "",
        item.line_of_business or "",
    ])).lower()

    # 1. Jurisdiction match (strong signal)
    if req.jurisdiction and item.jurisdiction:
        req_juris = req.jurisdiction.lower()
        item_juris = item.jurisdiction.lower()
        if req_juris == item_juris or req_juris in item_juris or item_juris in req_juris:
            score += 3.0
            reasons.append(f"Jurisdiction match: {item.jurisdiction}")
        elif item.jurisdiction.lower() in ["all states", "all", "nationwide", "multi-state"]:
            score += 1.5
            reasons.append("Item applies to all jurisdictions")

    # 2. Line of business match (strong signal)
    if req.line_of_business and item.line_of_business:
        req_lob = req.line_of_business.lower()
        item_lob = item.line_of_business.lower()
        if _text_overlap(req_lob, item_lob):
            score += 3.0
            reasons.append(f"Line of business match: {item.line_of_business}")

    # 3. Change category alignment
    if req.change_category:
        category_keywords = {
            "rate_change": ["rate", "premium", "surcharge", "pricing", "rating"],
            "form_revision": ["form", "policy form", "endorsement", "language", "wording"],
            "coverage_mandate": ["coverage", "mandate", "require", "minimum", "limit"],
            "disclosure_requirement": ["disclosure", "notice", "notification", "inform"],
            "underwriting_restriction": ["underwriting", "eligibility", "restrict", "prohibit", "underwrite"],
            "reporting_requirement": ["report", "filing", "submit", "data", "annual"],
        }
        cat_keywords = category_keywords.get(req.change_category, [])
        for kw in cat_keywords:
            if kw in item_text:
                score += 1.5
                reasons.append(f"Category keyword '{kw}' found in item")
                break

    # 4. Keyword overlap from catalogue keywords field
    if item.keywords:
        catalogue_kws = [k.strip().lower() for k in item.keywords.split(",")]
        matched_kws = [kw for kw in catalogue_kws if kw and kw in req_text]
        if matched_kws:
            score += min(len(matched_kws) * 1.0, 3.0)
            reasons.append(f"Keyword matches: {', '.join(matched_kws[:3])}")

    # 5. General text overlap
    req_words = set(w for w in req_text.split() if len(w) > 4)
    item_words = set(w for w in item_text.split() if len(w) > 4)
    overlap = req_words & item_words
    if len(overlap) >= 3:
        score += min(len(overlap) * 0.3, 2.0)
        sample_words = list(overlap)[:3]
        reasons.append(f"Text overlap: {', '.join(sample_words)}")

    return score, reasons


def _text_overlap(a: str, b: str) -> bool:
    """Check if two texts meaningfully overlap."""
    words_a = set(a.split())
    words_b = set(b.split())
    common = words_a & words_b
    return len(common) >= 1 and any(len(w) > 3 for w in common)


def _score_to_confidence(score: float) -> str:
    if score >= 5.0:
        return "high"
    elif score >= 2.5:
        return "medium"
    else:
        return "low"


def _generate_suggested_action(req: Requirement, item: InsuranceCatalogueItem, confidence: str) -> str:
    """Generate a suggested next action based on the match."""
    item_type_labels = {
        "product": "product",
        "rule": "underwriting rule",
        "form": "policy form",
    }
    item_label = item_type_labels.get(item.item_type, item.item_type)

    if confidence == "high":
        return (
            f"HIGH CONFIDENCE: Review {item_label} '{item.name}' for required changes. "
            f"This {item_label} likely requires updates based on the regulatory requirement. "
            f"Assign to the responsible team for impact assessment and implementation planning."
        )
    elif confidence == "medium":
        return (
            f"MEDIUM CONFIDENCE: Evaluate whether {item_label} '{item.name}' is affected. "
            f"The connection between this requirement and the {item_label} is plausible but not certain. "
            f"A subject-matter expert should confirm whether changes are needed."
        )
    else:
        return (
            f"LOW CONFIDENCE: This {item_label} '{item.name}' may be tangentially related. "
            f"Review is suggested but the impact is uncertain. "
            f"A compliance review team should assess relevance before taking action."
        )


def run_impact_analysis(
    db: Session,
    analysis_run_id: int,
    requirements: list[Requirement],
) -> list[dict[str, Any]]:
    """
    Run full impact analysis for all requirements in an analysis run.
    Returns list of match result dicts ready to be saved.
    """
    catalogue_items = db.query(InsuranceCatalogueItem).all()

    if not catalogue_items:
        logger.warning("No catalogue items found — cannot run impact matching")
        return []

    all_matches = []
    seen_pairs = set()

    for req in requirements:
        matches = compute_matches(req, catalogue_items)
        for match in matches:
            pair = (req.id, match["catalogue_item_id"])
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                match["requirement_id"] = req.id
                match["analysis_run_id"] = analysis_run_id
                all_matches.append(match)

    return all_matches
