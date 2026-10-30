Ah, I see the hidden culprit!

Look closely at the indentation in your **Project Structure** block. The spaces before `src/task-1_larency/` and the tree lines contain **non-breaking space characters (or mixed tabs/spaces)** instead of clean standard spaces. Because of this, Markdown treats the opening ````text` as indented code rather than a code block fence, which causes the entire block to break.

Here is a 100% clean, freshly sanitized version of your entire `README.md` with standard indentation and uniform UTF-8 characters.

Copy this entire block and replace everything in your `README.md` file:

```markdown
# Evidence-to-Insight Pipeline — Task 1: Source Normalisation & Policy Routing

A robust, offline-first Python pipeline designed to ingest, validate, deduplicate, and evaluate evidence sources against enterprise policy rules with strict data fidelity.

---

## Architecture Overview

The pipeline processes raw unvalidated evidence feeds through a structured 3-stage architecture:

1. **Input Validation & Error Isolation (`RawSourceInput`)**
   - Utilizes Pydantic v2 models and `HttpUrl` validation to enforce strict schema compliance and catch malformed URLs.
   - Gracefully isolates invalid records into a dedicated `validation_errors` log without failing the entire batch execution.

2. **Canonical Deduplication & Provenance Tracking**
   - Deduplicates incoming records based on `canonical_url`.
   - Implements a robust internal lookup strategy for records lacking URLs to prevent false key collisions while keeping output data pristine (`null`).
   - Aggregates discovery lineage (`original_id`, `raw_url`, `channel`) across duplicate ingestion paths.

3. **Policy-Based Filtering & Eligibility Routing**
   - Evaluates records against a configurable `PolicyConfig` ruleset.
   - Assigns explicit eligibility statuses (`ELIGIBLE`, `EXCLUDED`, `NEEDS_VERIFICATION`) backed by standardized reason codes.

---

## Project Structure

```text
src/task-1_larency/
├── examples/
│   └── demo.py               # Executable demonstration script
├── fixtures/
│   └── g2-cases.json         # Synthetic test fixtures and policy rules
├── tests/
│   └── test_pipeline.py      # Automated unittest / pytest suite
├── pipeline.py               # Core pipeline engine, models, and policy configuration
└── README.md                 # Project documentation

```

---

## Getting Started

### Prerequisites

* **Python**: `3.10+`
* **Dependencies**: Pydantic v2 & Pytest

Install required dependencies via terminal:

```bash
pip install pydantic pytest

```

### Running the Demo Pipeline

Execute the provided demonstration script to run the test fixtures through the pipeline and inspect the serialized JSON output:

```bash
python examples/demo.py

```

### Running the Automated Test Suite

Verify all pipeline specifications (validation, deduplication, temporal handling, and policy routing) by running `pytest`:

```bash
python -m pytest

```

---

## Core Schema & Design Decisions

### Data Fidelity & Missing URL Handling

* **Zero Mutation on Raw Inputs:** In compliance with strict data fidelity guidelines, missing or `None` URLs are never artificially replaced or contaminated with synthetic placeholders in the output payloads.
* **Optional Field Safety:** Models are built with robust type guards (`Optional`, default empty lists for `reason_codes` and `discovery_lineage`) to prevent runtime validation exceptions.

### Eligibility Statuses

| Status | Definition | Example Trigger |
| --- | --- | --- |
| **`ELIGIBLE`** | Clears all ingestion and policy gates successfully. | Authoritative government or primary documentation sources. |
| **`EXCLUDED`** | Fails policy checks or untrusted source criteria. | Untrusted source types or prohibited competitor promotional claims. |
| **`NEEDS_VERIFICATION`** | Requires human review or independent validation. | Generic competitor claims treated as discovery leads rather than automatic proof. |

---

## Known Limitations

* **Keyword-Based Policy Matching:** Promotional claim detection relies on a configurable list of literal keywords (`promotional_keywords`). Highly nuanced or sophisticated marketing copy that avoids these exact terms may require more advanced semantic parsing.
* **Strict ISO Date Formats:** Temporal fields expect standardized string formats (`YYYY-MM-DD`) rather than complex natural language date parsing.

```

