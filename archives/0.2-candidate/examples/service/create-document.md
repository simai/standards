# Create a document

This fictional API contract is provided for discovery tests only. No server is
running and no request should be executed by the reference reader.

## Prerequisites and input
An existing authenticated tenant session and a user-authorized private folder
are required. Supply title and text. The API creates a private document; it does
not publish it, send notifications or charge a fee in this example contract.

## Result and verification
HTTP 201 returns id and status=created. An accepted queue response is not defined
by this example. Read the returned document with the existing application before
claiming its contents are correct.

## Failure and retry
400 means invalid input; 401/403 mean missing authorization. Do not retry writes
after a timeout: completion may be uncertain. Reconcile through the application's
existing document list before any separately authorized retry. This example does
not claim an idempotency-key facility.
