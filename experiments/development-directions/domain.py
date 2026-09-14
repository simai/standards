"""Synthetic domain adapter, not an AI First profile or execution engine."""
import copy
import hashlib
import json
from datetime import datetime


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def project(composition, audience):
    """Publisher filters identities before serialization, not after denial."""
    visible = [r for r in composition['resources'] if audience in r['audiences']]
    return {'installation': composition['installation'], 'revision': composition['revision'],
            'coverage': 'complete' if len(visible) == len(composition['resources']) else 'restricted',
            'resources': [{k: copy.deepcopy(v) for k, v in r.items() if k != 'audiences'} for r in visible]}


def locate(composition, capability, installation):
    if composition['installation'] != installation:
        return {'status': 'unknown', 'reason': 'installation-mismatch'}
    matches = [r for r in composition['resources'] if capability in r['provides']]
    if not matches:
        return {'status': 'missing' if composition['coverage'] == 'complete' else 'unknown',
                'reason': 'not-in-authorized-view'}
    if len(matches) != 1:
        return {'status': 'unknown', 'reason': 'ambiguous-provider'}
    selected = matches[0]
    if selected['availability'] != 'available':
        return {'status': 'unknown', 'reason': 'provider-unavailable'}
    return {'status': 'declared', 'provider': selected['id'], 'contract': selected['contract'],
            'installedVerified': False}


def assess_scenario(scenario, composition, installation):
    results = [locate(composition, c, installation) for c in scenario['requires']]
    return {'status': 'missing-prerequisite' if any(r['status'] == 'missing' for r in results)
            else 'unknown' if any(r['status'] == 'unknown' for r in results) else 'declared-prerequisites-present',
            'requirements': results, 'execution': 'not-run', 'approvalGranted': False}


def validate_observation(requirement, provider, evidence, *, now, tenant,
                         trusted_checkers, method):
    """Validate common evidence bindings without interpreting domain results."""
    if not evidence:
        return {'status': 'unknown', 'reason': 'observation-missing'}
    bindings = {'subject': provider['id'], 'providerDigest': digest(provider),
                'requirementDigest': digest(requirement), 'tenant': tenant,
                'configurationRevision': provider['configurationRevision'],
                'method': method}
    if any(evidence.get(k) != v for k, v in bindings.items()):
        return {'status': 'unknown', 'reason': 'evidence-binding-mismatch'}
    if evidence.get('checker') not in trusted_checkers:
        return {'status': 'unknown', 'reason': 'untrusted-checker'}
    try:
        observed = datetime.fromisoformat(evidence['observedAt'])
        expires = datetime.fromisoformat(evidence['expiresAt'])
        clock = datetime.fromisoformat(now)
        valid = all(t.tzinfo is not None for t in (observed, expires, clock)) and observed <= clock < expires
    except (ValueError, TypeError, KeyError): valid = False
    if not valid: return {'status': 'unknown', 'reason': 'evidence-time-invalid'}
    if evidence.get('result') != 'pass':
        return {'status': 'unknown', 'reason': 'observation-not-passing'}
    return {'status': 'usable', 'bindings': bindings}


def assess_images(requirement, provider, evidence, *, now, tenant, trusted_checkers):
    """Compare one fixed domain. No universal matching language or runtime call."""
    failures = []
    for field in ('input', 'output', 'mode'):
        if requirement[field] not in provider[field]: failures.append(field)
    if requirement['alpha'] and not provider['alpha']: failures.append('alpha')
    if failures:
        return {'status': 'incompatible', 'basis': 'provider-declaration', 'mismatches': failures}
    common = validate_observation(requirement, provider, evidence, now=now, tenant=tenant,
                                  trusted_checkers=trusted_checkers,
                                  method='synthetic-image-observation-v1')
    if common['status'] != 'usable':
        return common
    if type(evidence.get('testedInputBytes')) is not int:
        return {'status': 'unknown', 'reason': 'observation-not-passing'}
    if evidence['testedInputBytes'] < requirement['inputBytes']:
        return {'status': 'unknown', 'reason': 'input-size-not-demonstrated'}
    return {'status': 'compatible', 'basis': 'synthetic-scoped-observation',
            'requirementDigest': digest(requirement), 'providerDigest': digest(provider),
            'execution': 'not-run', 'configurationChanged': False}


def assess_delivery(requirement, provider, evidence, *, now, tenant, trusted_checkers):
    """Compare delivery while reusing only the evidence envelope."""
    failures = []
    if requirement['country'] not in provider['countries']: failures.append('country')
    if requirement['mode'] not in provider['modes']: failures.append('mode')
    if requirement['cashOnDelivery'] and not provider['cashOnDelivery']:
        failures.append('cashOnDelivery')
    if failures:
        return {'status': 'incompatible', 'basis': 'provider-declaration', 'mismatches': failures}
    common = validate_observation(requirement, provider, evidence, now=now, tenant=tenant,
                                  trusted_checkers=trusted_checkers,
                                  method='synthetic-delivery-observation-v1')
    if common['status'] != 'usable':
        return common
    weight = evidence.get('testedWeightKg')
    if type(weight) not in (int, float):
        return {'status': 'unknown', 'reason': 'observation-not-passing'}
    if weight < requirement['weightKg']:
        return {'status': 'unknown', 'reason': 'weight-not-demonstrated'}
    return {'status': 'compatible', 'basis': 'synthetic-scoped-observation',
            'requirementDigest': digest(requirement), 'providerDigest': digest(provider),
            'execution': 'not-run', 'configurationChanged': False}
