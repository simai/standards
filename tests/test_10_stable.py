import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from check_stable10 import evaluate, REQUIRED_CHECKS


LOCK = "1a5010469988a9fcdaf76799e30897130e62cc16a821933109d67a160655aab3"


def ready_records():
    candidate = {"status": "pass", "candidate": "1.0.0-rc.1", "lockSha256": LOCK}
    verification = {
        "candidate": "1.0.0-rc.1",
        "candidateLockSha256": LOCK,
        "checks": {name: {"status": "pass"} for name in REQUIRED_CHECKS},
    }
    product = {
        "implementation": "accepted",
        "compatibility": "verified",
        "receipt": "evidence/pilot-result.json",
        "artifactRoot": "evidence/bundle",
        "evidenceReview": "accepted",
    }
    pilots = {
        "candidate": "1.0.0-rc.1",
        "candidateLockSha256": LOCK,
        "products": {"docara": copy.deepcopy(product), "larena": copy.deepcopy(product)},
    }
    return candidate, verification, pilots


class StablePromotionTests(unittest.TestCase):
    def test_complete_evidence_is_ready(self):
        self.assertEqual(evaluate(*ready_records())["status"], "ready")

    def test_one_missing_product_receipt_blocks_promotion(self):
        candidate, verification, pilots = ready_records()
        pilots["products"]["larena"]["receipt"] = None
        result = evaluate(candidate, verification, pilots)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("missing-receipt:larena", result["blockers"])

    def test_current_repository_status_is_honestly_blocked(self):
        candidate = {"status": "pass", "candidate": "1.0.0-rc.1", "lockSha256": LOCK}
        verification = json.loads((ROOT / "conformance/1.0/verification.json").read_text())
        pilots = json.loads((ROOT / "conformance/1.0/pilots/status.json").read_text())
        result = evaluate(candidate, verification, pilots)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("pilot-not-accepted:docara", result["blockers"])
        self.assertIn("pilot-not-accepted:larena", result["blockers"])

    def test_empty_checks_do_not_certify_readiness(self):
        candidate, verification, pilots = ready_records()
        verification["checks"] = {}
        result = evaluate(candidate, verification, pilots)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("missing-local-check:repositoryTests", result["blockers"])

    def test_omitted_required_check_blocks_even_with_other_passes(self):
        candidate, verification, pilots = ready_records()
        del verification["checks"]["actorFilteredHttps"]
        result = evaluate(candidate, verification, pilots)
        self.assertIn("missing-local-check:actorFilteredHttps", result["blockers"])


if __name__ == "__main__":
    unittest.main()
