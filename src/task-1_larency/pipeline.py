from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, ValidationError, Field

class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    EXCLUDED = "EXCLUDED"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"

class RawSourceInput(BaseModel):
    """Schema for incoming unvalidated raw evidence inputs."""
    id: str
    raw_url: Optional[HttpUrl] = None
    canonical_url: Optional[HttpUrl] = None
    publisher: Optional[str] = "Unknown Publisher"
    source_type: Optional[str] = "untrusted"
    publication_date: Optional[str] = None
    event_date: Optional[str] = None
    content: Optional[str] = ""
    discovery_channel: Optional[str] = "unknown"


class NormalisedRecord(BaseModel):
    """Schema for processed, deduplicated, and policy-checked output."""
    source_id: str
    canonical_url: Optional[str] = None
    publisher: Optional[str] = "Unknown Publisher"
    source_type: str
    publication_date: Optional[str] = None
    event_date: Optional[str] = None
    discovery_lineage: List[Dict[str, Any]] = []
    eligibility: EligibilityStatus
    reason_codes: List[str] = []

class PolicyConfig(BaseModel):
    """Configurable rules governing source inclusion and exclusion."""
    allowed_source_types: List[str] = ["primary_authority", "primary_documentation", "authoritative_gov"]
    competitor_source_types: List[str] = ["competitor"]
    promotional_keywords: List[str] = ["our cloud", "faster than", "cheaper", "pricing", "best cloud", "saving"]

class SourceNormaliserPipeline:
    """Core offline normalization pipeline for Task 1."""
    def __init__(self, policy: Optional[PolicyConfig] = None):
        self.policy = policy or PolicyConfig()

    def run(self, raw_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_records: List[RawSourceInput] = []
        validation_errors: List[Dict[str, Any]] = []
        
        eligible_records: List[NormalisedRecord] = []
        excluded_records: List[NormalisedRecord] = []

        # Step 1: Input Validation & Error Isolation
        for raw_item in raw_data_list:
            try:
                validated = RawSourceInput(**raw_item)
                valid_records.append(validated)
            except ValidationError as e:
                validation_errors.append({
                    "raw_id": raw_item.get("id", "UNKNOWN"),
                    "error": str(e)
                })

        # Step 2: Canonical Deduplication & Provenance Lineage Tracking
        deduped_map: Dict[str, Dict[str, Any]] = {}

        for rec in valid_records:
            lineage_entry = {
                "original_id": rec.id,
                "raw_url": str(rec.raw_url) if rec.raw_url else None,
                "channel": rec.discovery_channel
            }

            # Use a unique lookup key for missing URLs to avoid collision, 
            # while keeping the actual record data pristine.
            if not rec.canonical_url:
                lookup_key = f"__missing_url_{rec.id}"
            else:
                lookup_key = str(rec.canonical_url)

            if lookup_key in deduped_map:
                deduped_map[lookup_key]["lineage"].append(lineage_entry)
            else:
                deduped_map[lookup_key] = {
                    "record": rec,
                    "lineage": [lineage_entry]
                }

        # Step 3: Policy Filter & Eligibility Routing
        for lookup_key, item in deduped_map.items():
            rec: RawSourceInput = item["record"]
            lineage = item["lineage"]
            reasons = []
            eligibility = EligibilityStatus.ELIGIBLE

            # Extract the actual pristine canonical_url (None if missing, or string if present)
            actual_canon_url = str(rec.canonical_url) if rec.canonical_url else None

            # Check competitor source restrictions
            if rec.source_type in self.policy.competitor_source_types:
                content_lower = rec.content.lower() if hasattr(rec, "content") and rec.content else ""
                is_promotional = any(kw in content_lower for kw in self.policy.promotional_keywords)
                
                if is_promotional:
                    eligibility = EligibilityStatus.EXCLUDED
                    reasons.append("EXCLUDE_COMPETITOR_PROMOTIONAL_CLAIM")
                else:
                    eligibility = EligibilityStatus.NEEDS_VERIFICATION
                    reasons.append("COMPETITOR_GENERIC_CLAIM_REQUIRES_INDEPENDENT_VERIFICATION")

            # Check allowed primary source categories
            elif rec.source_type not in self.policy.allowed_source_types:
                eligibility = EligibilityStatus.EXCLUDED
                reasons.append("EXCLUDE_UNTRUSTED_SOURCE_TYPE")

            # Preserve explicit temporal uncertainty without fabrication
            if rec.publication_date is None:
                reasons.append("INFO_PUBLICATION_DATE_UNKNOWN")

            norm_record = NormalisedRecord(
                source_id=rec.id,
                canonical_url=actual_canon_url,
                publisher=rec.publisher,
                source_type=rec.source_type,
                publication_date=rec.publication_date,
                event_date=rec.event_date,
                discovery_lineage=lineage,
                eligibility=eligibility,
                reason_codes=reasons
            )

            if eligibility == EligibilityStatus.ELIGIBLE:
                eligible_records.append(norm_record)
            else:
                excluded_records.append(norm_record)

        # Final return statement at the end of execution
        return {
            "eligible": [rec.model_dump() for rec in eligible_records],
            "excluded": [rec.model_dump() for rec in excluded_records],
            "validation_errors": validation_errors
        }