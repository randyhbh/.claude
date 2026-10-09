# Testing

```bash
cd scripts
python3 -m unittest discover -p "test_*.py" -v
```

All 56 tests are unit tests, no live network calls:
- `test_compute_worklog.py` — segment building, trackable-seconds math,
  overlap splitting, idempotent delta/tagging.
- `test_normalize.py` — JQL building, ADF↔text, changelog/worklog
  normalization, legacy bracketed-tag detection.
- `test_jira_client.py` — request building, pagination, auth headers, error
  handling, exercised against real recorded Jira API responses (see
  `../scripts/fixtures/README.md`) with only the transport (`urlopen`) stubbed.
- `test_run_track_time.py` — exclude-filtering logic.
