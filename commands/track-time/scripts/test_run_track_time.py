import unittest

from run_track_time import filter_excluded


class FakeResult:
    def __init__(self, key, skip_reason=None):
        self.key = key
        self.skip_reason = skip_reason


class TestFilterExcluded(unittest.TestCase):
    def test_drops_excluded_keys(self):
        results = [FakeResult("A-1"), FakeResult("A-2"), FakeResult("A-3")]
        postable = filter_excluded(results, {"A-2"})
        self.assertEqual([r.key for r in postable], ["A-1", "A-3"])

    def test_always_drops_skipped_results(self):
        results = [FakeResult("A-1"), FakeResult("A-2", skip_reason="no new time to log")]
        postable = filter_excluded(results, set())
        self.assertEqual([r.key for r in postable], ["A-1"])

    def test_empty_exclude_set_keeps_all_postable(self):
        results = [FakeResult("A-1"), FakeResult("A-2")]
        postable = filter_excluded(results, set())
        self.assertEqual([r.key for r in postable], ["A-1", "A-2"])


if __name__ == "__main__":
    unittest.main()
