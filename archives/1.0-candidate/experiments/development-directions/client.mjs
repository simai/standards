#!/usr/bin/env node
/** Independent JavaScript interpretation of the experimental domain fixtures. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const source = JSON.parse(fs.readFileSync(path.join(here, 'source.json'), 'utf8'));
const now = '2026-09-12T12:00:00+00:00';

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function digest(value) {
  return crypto.createHash('sha256').update(canonical(value)).digest('hex');
}

function validateObservation(requirement, provider, evidence, method) {
  if (!evidence) return {status: 'unknown', reason: 'observation-missing'};
  const bindings = {
    subject: provider.id,
    providerDigest: digest(provider),
    requirementDigest: digest(requirement),
    tenant: 'fixture-tenant',
    configurationRevision: provider.configurationRevision,
    method,
  };
  if (Object.entries(bindings).some(([key, value]) => evidence[key] !== value)) {
    return {status: 'unknown', reason: 'evidence-binding-mismatch'};
  }
  if (evidence.checker !== 'fixture-checker') return {status: 'unknown', reason: 'untrusted-checker'};
  const observed = Date.parse(evidence.observedAt);
  const expires = Date.parse(evidence.expiresAt);
  const clock = Date.parse(now);
  const offsets = [evidence.observedAt, evidence.expiresAt, now].every(value => /(?:Z|[+-][0-9]{2}:[0-9]{2})$/.test(value));
  if (!offsets || !Number.isFinite(observed) || !Number.isFinite(expires) || !(observed <= clock && clock < expires)) {
    return {status: 'unknown', reason: 'evidence-time-invalid'};
  }
  if (evidence.result !== 'pass') return {status: 'unknown', reason: 'observation-not-passing'};
  return {status: 'usable'};
}

function evidence(requirement, provider, method, metric) {
  return {
    subject: provider.id,
    providerDigest: digest(provider),
    requirementDigest: digest(requirement),
    tenant: 'fixture-tenant',
    configurationRevision: provider.configurationRevision,
    method,
    checker: 'fixture-checker',
    observedAt: '2026-09-12T11:00:00+00:00',
    expiresAt: '2026-09-12T13:00:00+00:00',
    result: 'pass',
    ...metric,
  };
}

function assessImage(requirement, provider, observed) {
  const mismatches = ['input', 'output', 'mode'].filter(field => !provider[field].includes(requirement[field]));
  if (requirement.alpha && !provider.alpha) mismatches.push('alpha');
  if (mismatches.length) return {status: 'incompatible'};
  const common = validateObservation(requirement, provider, observed, 'synthetic-image-observation-v1');
  if (common.status !== 'usable') return common;
  if (!Number.isInteger(observed.testedInputBytes)) return {status: 'unknown', reason: 'observation-not-passing'};
  if (observed.testedInputBytes < requirement.inputBytes) return {status: 'unknown', reason: 'input-size-not-demonstrated'};
  return {status: 'compatible'};
}

function assessDelivery(requirement, provider, observed) {
  const mismatch = !provider.countries.includes(requirement.country)
    || !provider.modes.includes(requirement.mode)
    || (requirement.cashOnDelivery && !provider.cashOnDelivery);
  if (mismatch) return {status: 'incompatible'};
  const common = validateObservation(requirement, provider, observed, 'synthetic-delivery-observation-v1');
  if (common.status !== 'usable') return common;
  if (typeof observed.testedWeightKg !== 'number' || !Number.isFinite(observed.testedWeightKg)) {
    return {status: 'unknown', reason: 'observation-not-passing'};
  }
  if (observed.testedWeightKg < requirement.weightKg) return {status: 'unknown', reason: 'weight-not-demonstrated'};
  return {status: 'compatible'};
}

const imageProvider = source.providers[1];
const deliveryProvider = source.deliveryProviders[1];
const imageEvidence = evidence(source.requirement, imageProvider, 'synthetic-image-observation-v1', {testedInputBytes: 12582912});
const deliveryEvidence = evidence(source.deliveryRequirement, deliveryProvider, 'synthetic-delivery-observation-v1', {testedWeightKg: 20});
const expired = {...deliveryEvidence, expiresAt: '2026-09-12T11:30:00+00:00'};

const result = {
  client: 'javascript-independent-domain-fixture',
  businessExecution: 'not-run',
  cases: {
    imageIncompatible: assessImage(source.requirement, source.providers[0], null).status,
    imageUnknown: assessImage(source.requirement, imageProvider, null).status,
    imageCompatible: assessImage(source.requirement, imageProvider, imageEvidence).status,
    deliveryIncompatible: assessDelivery(source.deliveryRequirement, source.deliveryProviders[0], null).status,
    deliveryUnknown: assessDelivery(source.deliveryRequirement, deliveryProvider, null).status,
    deliveryCompatible: assessDelivery(source.deliveryRequirement, deliveryProvider, deliveryEvidence).status,
    expiredEvidence: assessDelivery(source.deliveryRequirement, deliveryProvider, expired).status,
  },
};

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
