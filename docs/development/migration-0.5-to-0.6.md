# migrating from 0.5.x to 0.6.0

shadlet 0.6.0 keeps protocol version 2 and is intended to be source-compatible
with 0.5.x applications.

## Upgrade

Update the dependency to `shadlet>=0.6.0`. Regenerate a project with `shadlet
create` only if you want the updated built-in templates; existing applications
do not need to be recreated.

## Corrected semantic tags

`Box`, `Grid`, and `Text` now serialize their Python `as_` option to the
renderer prop `as`. Custom tags that were silently rendered as their default in
0.5.x now render with the requested tag. `Box` and `Grid` also accept `id` for
in-page fragment navigation.

## Server-side tables

`DataTable.page_size` is now limited to 1–500, matching the validated
`DataTableQuery` range. Reduce larger server-side page sizes before upgrading.

## Protocol and templates

The wire protocol remains version 2. New built-in templates are optional
starting points. The auth and CRUD templates are local demonstrations; they do
not provide production identity, database persistence, or authorization.
