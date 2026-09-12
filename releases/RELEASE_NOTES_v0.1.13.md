# topolograph-sdk v0.1.13

Tag: `v0.1.13`
Requires: Topolograph >= 2.70

Node identity fixes for Topolograph's v2.70 canonical node-identity contract.

## `NodesManager` (`client.graphs.get(...).nodes`)

- `get_by_id` / `update` / `patch`: `node_id` is now typed `str` (was `int`).
  Accepts the canonical node name, IS-IS System ID, discovered hostname, or
  an operator display override, matched case-insensitively.
- `get_by_id` no longer overwrites the server's canonical `id` with whatever
  alias was requested for the lookup.
- `get_by_id` no longer swallows an ambiguous-identifier error (the API's 400
  when an alias matches more than one node) into `None` — only a genuine
  not-found (404) returns `None` now; other errors raise as documented on
  `update`/`patch` (`NotFoundError`, `ValidationError`).
- `update` / `patch` refetch by the new canonical name when the call renamed
  the node, instead of the identifier that no longer resolves.
- `nodes_list` / `get` responses documented to include the new `display_name`
  field (human-readable text: operator override, hostname, System ID, or the
  canonical name).
