# topolograph-sdk v0.1.14

Tag: `v0.1.14`
Requires: Topolograph >= 2.72

IS-IS Traffic Engineering support: per-level CSPF, TE link filter and edge editing.

## CSPF

- `cspf_path(..., level=1|2)`: restrict the path to one IS-IS level (RFC 1195 S1.2).
  Omit it for no level restriction.

## Edges (`graph.edges`)

- `edges_list(is_te_link=True|False)`: keep only links that carry TE data, or only those that do not.
- `add_edge`, `update_edge`, `replace_edge`, `delete_edge`, `edge`: edge CRUD.
  `update_edge(..., isis_level=1|2)` writes metric and TE values into one level only.
- Supported TE attributes per vendor: see the [documentation](https://docs.topolograph.com/reference/supported-vendors/#te-attributes-by-vendor).

## Errors

- `ValidationError` now carries the API's detail message instead of a generic text.
