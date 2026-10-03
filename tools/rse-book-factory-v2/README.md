# RSE Book Factory v2

This directory is the migration target for the existing `tools/detective-book-factory`.

The old factory is already advanced and contains valuable source and validation logic. v2 does not discard it. v2 separates source truth from visual rendering so content cannot drift while layouts evolve.

## Build philosophy

`canonical sources -> normalized JSON -> fixed page components -> publication PDF -> deterministic QA`

The renderer never rewrites copy.

See central architecture:
`riseshineevolve-source/agency-agents/orchestration/architecture/RSE_BOOK_FACTORY_V2_DECISION_2026-10-03.md`

## Initial implementation order

1. source adapter / normalizer
2. asset registry + checksum validation
3. page manifest
4. fixed-page React shell
5. theme/tokens
6. Vivliostyle build
7. frozen-page adapter
8. Case Intro
9. HM Comms
10. Witness Board
11. Live Map + Verdict
12. Case 02 proof
13. visual + logic QA
14. owner gate
