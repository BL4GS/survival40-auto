# Architecture

## Principle
Normal operation must not require the site owner to:
- choose routine article topics
- manually create Amazon links
- paste affiliate links
- manually link related posts
- manually publish routine non-YMYL articles

## Planned modules
1. Scheduler
2. Topic planner
3. Gemini article generator
4. Product discovery provider
5. Affiliate URL builder
6. Internal-link graph
7. SEO/meta writer
8. Publishing gate
9. Performance feedback loop

## Safety gate
Medical/YMYL content should be validated separately and may remain draft if validation fails.

## Product discovery
Amazon Creators API should be treated as one provider, not the architecture itself.
A fallback provider must be available when Creators API eligibility is unavailable.
