# Frontend Investment Review Plan

## Goals
- Present the deal review flow in a way that portfolio owners can quickly judge rental vs. flip fit without underwriting jargon.
- Reduce coupling in the landing page by extracting reusable UI primitives and clarifying state responsibilities.
- Keep additions compatible with the existing FastAPI endpoints and assumptions models.

## Planned Surface
- **Overview tab**: property snapshot, quick facts, and data-source context once a property is fetched.
- **Acquisition tab**: purchase target inputs aligned to the active strategy (rental vs. flip), paired with value/rent guidance and closing cost callouts.
- **Financing tab**: derived loan metrics (LTV, loan amount, monthly debt service, DSCR when rental analysis is available) using the current assumptions.
- **Cashflow & Returns tab**: displays rental or flip outputs with language tailored to the chosen strategy, plus guardrails when no run has occurred.
- **Data Room tab**: provider payload selector and merged snapshot viewer for auditability.

## Implementation Notes
- Preserve the existing address intake and analysis flows but reorganize the right-hand column into a single tabbed experience.
- Add small UI primitives (tab buttons, metric rows) to keep the page JSX concise and easier to extend with future investment modules.
- Keep client-side derived calculations transparent with inline comments and defensive null handling to avoid breaking when API data is incomplete.
