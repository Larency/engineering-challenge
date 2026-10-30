import json
import sys
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pipeline import SourceNormaliserPipeline

def main():
    fixture_path = Path(__file__).parent.parent / "fixtures" / "g2-cases.json"
    if not fixture_path.exists():
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "g2-cases.json"
    
    if not fixture_path.exists():
        print(f"Fixture file not found at {fixture_path}")
        return

    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture_data = json.load(f)

    raw_cases = fixture_data.get("cases", [])
    sources_to_run = []
    
    for case in raw_cases:
        if isinstance(case, dict):
            case_id = case.get("id")
            metadata = case.get("metadata", {})
            
            # Faithfully extract payload matching fixture keys without fabricating URLs
            payload = {
                "id": case_id,
                "statement": case.get("statement"),
                "source_type": metadata.get("source_type"),
                "content_type": metadata.get("content_type"),
                "publication_date": metadata.get("published_at"),
                "event_date": metadata.get("event_date"),
                "effective_from": metadata.get("effective_from"),
                "current_status": metadata.get("current_status"),
                "supported": metadata.get("supported", True),
                "superseded": metadata.get("superseded", False),
                "contradiction": metadata.get("contradiction", False),
                "competitor_product_claim": metadata.get("competitor_product_claim", False),
                # Preserve original URL fields as-is (None if not present in fixture)
                "canonical_url": metadata.get("canonical_url") or metadata.get("url"),
                "raw_url": metadata.get("raw_url") or metadata.get("url")
            }
            
            sources_to_run.append(payload)

    pipeline = SourceNormaliserPipeline()
    result = pipeline.run(sources_to_run)

    print("=== PIPELINE EXECUTION RESULT ===")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()