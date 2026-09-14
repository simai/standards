#!/usr/bin/env python3
"""Report whether AI First 1.0 has the evidence required for stable promotion.

This command is read-only. It verifies the frozen candidate and returned pilot
bundles, but it never executes commands recorded by a product pilot and never
creates or publishes a stable release.
"""
import json
from pathlib import Path

from aifirst import Failure
from check_candidate10 import ROOT, verify
from check_pilot10 import check as check_pilot


REQUIRED_PRODUCTS = ("docara", "larena")
REQUIRED_CHECKS = {
    "repositoryTests", "developmentDirectionExperiments", "candidate01And02Regression",
    "candidate10Integrity", "repositoryPolicy", "pythonJavaScriptSharedCorpus",
    "actorFilteredHttps", "largeCatalog", "migrationAndJointExport",
}


def evaluate(candidate, verification, pilots):
    """Evaluate stable-promotion metadata without reading product bundles."""
    blockers = []
    expected_candidate = candidate.get("candidate")
    expected_lock = candidate.get("lockSha256")

    if candidate.get("status") != "pass":
        blockers.append("candidate-integrity-not-passing")
    if expected_candidate != "1.0.0-rc.1":
        blockers.append("unexpected-candidate")
    if verification.get("candidate") != expected_candidate:
        blockers.append("verification-candidate-mismatch")
    if verification.get("candidateLockSha256") != expected_lock:
        blockers.append("verification-lock-mismatch")

    checks = verification.get("checks", {})
    if not isinstance(checks, dict):
        checks = {}
    blockers.extend("missing-local-check:" + name for name in sorted(REQUIRED_CHECKS - checks.keys()))
    failed_checks = sorted(
        name for name, result in checks.items()
        if not isinstance(result, dict) or result.get("status") != "pass"
    )
    blockers.extend(f"local-check-not-passing:{name}" for name in failed_checks)

    if pilots.get("candidate") != expected_candidate:
        blockers.append("pilot-status-candidate-mismatch")
    if pilots.get("candidateLockSha256") != expected_lock:
        blockers.append("pilot-status-lock-mismatch")

    products = pilots.get("products", {})
    for product in REQUIRED_PRODUCTS:
        record = products.get(product)
        if not isinstance(record, dict):
            blockers.append(f"missing-product-status:{product}")
            continue
        if record.get("implementation") != "accepted":
            blockers.append(f"pilot-not-accepted:{product}")
        if record.get("compatibility") != "verified":
            blockers.append(f"compatibility-not-verified:{product}")
        if not record.get("receipt"):
            blockers.append(f"missing-receipt:{product}")
        if not record.get("artifactRoot"):
            blockers.append(f"missing-artifact-root:{product}")
        if record.get("evidenceReview") != "accepted":
            blockers.append(f"evidence-review-not-accepted:{product}")

    return {
        "status": "ready" if not blockers else "blocked",
        "candidate": expected_candidate,
        "candidateLockSha256": expected_lock,
        "target": "1.0.0",
        "blockers": blockers,
    }


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_evidence_path(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def check(root=ROOT):
    candidate = verify()
    verification = _load(root / "conformance/1.0/verification.json")
    pilots = _load(root / "conformance/1.0/pilots/status.json")
    report = evaluate(candidate, verification, pilots)
    if report["status"] != "ready":
        report["pilotBundlesChecked"] = []
        return report

    checked = []
    for product in REQUIRED_PRODUCTS:
        record = pilots["products"][product]
        try:
            result = check_pilot(
                _resolve_evidence_path(record["receipt"]),
                _resolve_evidence_path(record["artifactRoot"]),
            )
        except (Failure, OSError, ValueError) as exc:
            report["blockers"].append(f"pilot-bundle-invalid:{product}")
            report["status"] = "blocked"
            continue
        if result.get("product") != product:
            report["blockers"].append(f"pilot-product-mismatch:{product}")
            report["status"] = "blocked"
        elif result.get("publicationCompatibility") != "pass":
            report["blockers"].append(f"pilot-publication-failed:{product}")
            report["status"] = "blocked"
        elif result.get("scenarioClaimsRequiringReview"):
            report["blockers"].append(f"pilot-scenarios-not-passing:{product}")
            report["status"] = "blocked"
        else:
            checked.append(product)
    report["pilotBundlesChecked"] = checked
    return report


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "ready" else 1)
