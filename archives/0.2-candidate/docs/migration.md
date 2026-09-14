# Migration and coexistence

## From the discussion illustrations
The initial discussion's JSON fragments were non-normative. The implemented 0.1
format adds document kind and publication revision, a publisher assertion, item
revisions and source links. Use `items` directly in ai.json for a small resource;
use `catalogs` for separate inventory files. HTML/Markdown alternatives belong in
item `representations`, not in an untyped list of links. Product versions use
`appliesTo` rather than formatVersion or publication revision.

## Existing ai.json files
Do not overwrite another application's file merely because this specification
uses the same filename. Publish the AI First document at a distinct explicit URL,
for example ai-first.json, and use the marked HTML alternate link or direct-manifest
reader mode. Unknown-format is the correct response to someone else's ai.json;
field-name guessing and merging unrelated formats are not compatibility.

## Future wire versions
Preserve the old publication while introducing a separately addressed new one.
Document field mappings, changed requirements and known information loss. A reader
for 0.1 must reject unknown versions instead of treating them as equivalent. There
is no implemented migration from a hypothetical 0.2, and no claimed wire stability
beyond the stated compatibility policy.
