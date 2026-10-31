# Product OS evidence ledger

Use stable record IDs to keep project facts, task dependencies and competitor claims auditable across weekly updates. This package contains a standard-library Python CLI and a reusable [skill](skills/product-evidence-ledger/SKILL.md).

```sh
python3 os/product/skills/product-evidence-ledger/scripts/ledger.py sync evidence.sqlite facts.csv market.csv
python3 os/product/skills/product-evidence-ledger/scripts/ledger.py queue evidence.sqlite
python3 os/product/skills/product-evidence-ledger/scripts/test_ledger.py
```

Each CSV needs a unique `id` column and a lowercase ASCII filename. Keep source dates, observed status, ownership, evidence location and verification boundaries in separate columns. Dataset identity is the filename stem, so do not rename a dataset during routine updates.

The database stores append-only revisions and a `current` view. Repeated unchanged imports add no revisions. Missing records are retained, so withdrawal requires an explicit status update. A malformed record rolls back the whole import batch. Network access and third-party dependencies are not required.

## Weekly workflow

1. Collect authorized evidence and distinguish a target date from a confirmed release.
2. Update the same record ID for corrections; assign a new ID for a new observation.
3. Import the CSV batch, review the revision count and inspect the review queue.
4. Generate private reports from current records. Preserve corrections and uncertainty in reader-facing output.
5. Publish only independently reviewed, sanitized material. The CLI does not publish or send messages.

The research queue selects records whose core claim lacks primary-source support. It does not certify every detail of the other records. Source availability is separate from factual verification. A successful import does not establish that a project shipped or achieved a business outcome.

## Validation

Eight automated tests cover idempotence, revision history, full-batch rollback, missing-row preservation, malformed inputs, concurrent writers, Unicode/SQL-like text and queue behavior. Private project documents, company metrics, screenshots, local paths and production databases are intentionally outside this package.
