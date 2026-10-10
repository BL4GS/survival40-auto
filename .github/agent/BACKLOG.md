# Autonomous development backlog (review stage)

The agent is currently **advisory only**, not an autonomous code writer. Select a single safe improvement per run.

## Highest priority
1. Establish production backup and rollback verification, without logging into the live site or altering production.
2. Check real GitHub Update URI metadata behavior in an isolated environment.
3. Verify the delivered release ZIP contains exactly the tested PHP and four Shiori/navigator image assets.
4. Preserve zero-ad explanatory articles and prevent unintended affiliate insertion.
5. Identify smallest regression tests before changes.

## Guardrails
- Follow PROJECT_VISION.md and docs/release-01921-production-safety.md.
- No production publication, branch protection changes, deployments, secret reads/prints, or ad activation.
- No auto-merge. No claim of implementation from a suggestion.
- First verify nightly reporting and cost, then consider a separate bounded patch-PR stage.
