# Live readiness — evidence package

Status: **BLOCKED**. This repository is a paper/sandbox build and contains no
supported live activation path.

## Automated prerequisites

- G1 accounting reconciliation: see `GET /admission`.
- G2 reproducible backtest and leakage checks: see persisted experiment.
- G3 prospective paper-forward: must finish its pre-registered period.
- G4 timeout/restart/stale/duplicate/limit drills: see `GET /admission`.
- Runtime safety: startup rejects truthy `TINKOFF_LIVE`.

## Required independent work

These items cannot be approved by the implementation itself:

1. Independent security review: secrets, authentication, authorization,
   dependencies, host hardening and incident response.
2. Legal/regulatory review for the jurisdiction, operating model and user.
3. Broker execution audit: live order lifecycle, partial fills, cancellation,
   reconciliation, rate limits, outages and recovery.
4. Explicit owner decision based on signed versions of all evidence.
5. A separately designed and reviewed live activation mechanism.

## Decision rule

Missing, expired or inconsistent evidence is a denial. Passing G1–G4 does not
authorize live trading. `GET /live/preflight` remains blocked and explains every
missing prerequisite.

## Current safety boundary

- Paper/sandbox only.
- Human approval remains mandatory for proposals.
- Unknown broker state blocks risk increases.
- No production change may set `TINKOFF_LIVE=1`.
