"""
LLM integration service for regulatory requirement extraction.
Falls back to demo mode if no API key is configured.
"""
import json
import logging
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a regulatory compliance analyst specializing in insurance regulations.
Your task is to extract structured requirements from regulatory documents.

You MUST:
- Only extract information explicitly stated in the document
- Mark any field as null/unknown if not explicitly stated — never invent information
- Flag ambiguities honestly
- Use exact quotes for source passages

You MUST NOT:
- Invent effective dates, jurisdictions, or legal obligations
- Claim certainty about unclear items
- Interpret beyond what the text explicitly states

Respond ONLY with valid JSON in the exact schema provided."""

EXTRACTION_USER_PROMPT = """Analyze the following regulatory document and extract all compliance requirements.

Document text:
---
{document_text}
---

Return a JSON object with this exact schema:
{{
  "requirements": [
    {{
      "req_id": "REQ-001",
      "summary": "Brief, plain-language summary of this requirement",
      "source_passage": "Exact quote from the document supporting this requirement",
      "page_ref": "Page number or section reference if identifiable, else null",
      "jurisdiction": "State or jurisdiction if explicitly stated, else null",
      "line_of_business": "Line of business if explicitly mentioned, else null",
      "effective_date": "Effective date if explicitly stated, else null",
      "change_category": "One of: rate_change, form_revision, coverage_mandate, disclosure_requirement, underwriting_restriction, reporting_requirement, other",
      "required_action": "What an insurer must do to comply, based only on the text",
      "ambiguities": "Unclear aspects, missing information, or items requiring legal review"
    }}
  ],
  "document_summary": "Overall summary of what this regulatory document covers",
  "extraction_notes": "Any important caveats or limitations of this extraction"
}}

Extract between 1 and 15 requirements. If no clear requirements are found, return an empty requirements array with an explanation in extraction_notes."""


async def extract_requirements(document_text: str) -> dict[str, Any]:
    """
    Extract structured requirements from document text using LLM.
    Returns dict with 'requirements' list and metadata.
    Falls back to demo mode if LLM is unavailable.
    """
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        logger.warning("No OpenAI API key configured — using demo extraction mode")
        return _demo_extraction_result(document_text)

    try:
        from openai import AsyncOpenAI

        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        client = AsyncOpenAI(**client_kwargs)

        # Truncate very long documents to avoid token limits
        max_chars = 12000
        truncated = document_text[:max_chars]
        if len(document_text) > max_chars:
            truncated += f"\n\n[Document truncated at {max_chars} characters for processing]"

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": EXTRACTION_USER_PROMPT.format(document_text=truncated)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            timeout=60,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate structure
        if "requirements" not in result:
            result["requirements"] = []
        if "document_summary" not in result:
            result["document_summary"] = "No summary available"
        if "extraction_notes" not in result:
            result["extraction_notes"] = ""

        result["llm_used"] = True
        return result

    except ImportError:
        logger.error("openai package not installed")
        return _error_result("openai package not installed. Install it with: pip install openai")
    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}")
        return _error_result(f"LLM returned invalid JSON response: {e}")
    except Exception as e:
        logger.exception("LLM extraction failed")
        error_msg = str(e)
        if "rate_limit" in error_msg.lower():
            return _error_result("Rate limit reached. Please try again in a moment.")
        elif "auth" in error_msg.lower() or "401" in error_msg:
            return _error_result("Invalid API key. Please check your OPENAI_API_KEY environment variable.")
        elif "timeout" in error_msg.lower():
            return _error_result("Request timed out. The document may be too long or the service may be unavailable.")
        return _error_result(f"LLM service error: {error_msg}")


def _error_result(message: str) -> dict[str, Any]:
    return {
        "requirements": [],
        "document_summary": "Extraction failed",
        "extraction_notes": message,
        "llm_used": False,
        "error": message,
    }


def _demo_extraction_result(document_text: str) -> dict[str, Any]:
    """
    Returns a clearly-labelled demo extraction result when LLM is unavailable.
    This demonstrates the expected output structure but is NOT a real analysis.
    """
    return {
        "requirements": [
            {
                "req_id": "DEMO-REQ-001",
                "summary": "[DEMO] Insurers must update homeowner policy forms to include wildfire coverage disclosures in high-risk zones",
                "source_passage": "[DEMO — not from your document] 'All admitted homeowner insurers writing policies in Tier 1 or Tier 2 wildfire risk zones must include a standardized disclosure statement...'",
                "page_ref": "Page 3, Section 2.1",
                "jurisdiction": "California",
                "line_of_business": "Homeowners",
                "effective_date": "2025-01-01",
                "change_category": "disclosure_requirement",
                "required_action": "Update HO-3 and HO-5 policy forms to include wildfire risk disclosure language. File updated forms with CDI by 90 days prior to effective date.",
                "ambiguities": "Definition of 'Tier 1' and 'Tier 2' zones not specified in this bulletin — reference to CDI map required. Unclear whether endorsements or base forms must be amended."
            },
            {
                "req_id": "DEMO-REQ-002",
                "summary": "[DEMO] Annual reporting of wildfire-related claims data required by March 31",
                "source_passage": "[DEMO — not from your document] 'Each insurer shall submit a wildfire claims experience report to the Department no later than March 31 of each calendar year...'",
                "page_ref": "Page 5, Section 3.4",
                "jurisdiction": "California",
                "line_of_business": None,
                "effective_date": "2025-03-31",
                "change_category": "reporting_requirement",
                "required_action": "Implement annual wildfire claims data reporting process. Designate a responsible compliance officer. Submit first report by March 31, 2025.",
                "ambiguities": "Report format not specified. Unclear if aggregate or policy-level data is required."
            },
            {
                "req_id": "DEMO-REQ-003",
                "summary": "[DEMO] Premium surcharge for homes in wildfire risk zones must not exceed 15% of base premium",
                "source_passage": "[DEMO — not from your document] 'No insurer may apply a wildfire risk surcharge exceeding fifteen percent (15%) of the otherwise applicable base premium...'",
                "page_ref": "Page 7, Section 4.2",
                "jurisdiction": "California",
                "line_of_business": "Homeowners",
                "effective_date": "2025-01-01",
                "change_category": "rate_change",
                "required_action": "Review and update rating algorithms to cap wildfire surcharges at 15%. Re-file rate manual with CDI if current surcharges exceed this cap.",
                "ambiguities": "Whether this cap applies to individual endorsements or the total surcharge amount is unclear."
            }
        ],
        "document_summary": "[DEMO MODE] This is a synthetic demonstration extraction. Your uploaded document was not analyzed by AI — no API key is configured. The requirements above are fictional examples showing the expected output format.",
        "extraction_notes": "DEMO MODE: No OpenAI API key is configured. Set OPENAI_API_KEY in backend/.env to enable real AI extraction. The above requirements are fictional and do not represent any actual regulation or your uploaded document.",
        "llm_used": False,
        "is_demo_extraction": True,
    }
