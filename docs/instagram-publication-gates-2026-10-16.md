# Instagram automated publication: actual gates (2026-10-16 JST)

## Confirmed
- Connected Metricool brand Survival40 / 7444916, Instagram @survival40_jp.
- One Metricool pilot article #516 is scheduled for 2026-10-17 10:00 JST, automatic feed-post publication enabled. It has not yet been confirmed PUBLISHED.
- Public Shiori original-image cards (1080x1350) are prepared from the verified Pinterest source. The live WordPress ordinary RSS og:image was unsuitable for an Instagram autolist because earlier tests surfaced affiliate-banner preview images.
- Separate Pinterest native RSS is connected and awaiting proof of native Pin creation; do not conflate the one-off Metricool Pinterest Pin with a native RSS pin.

## Safe independent GitHub pipeline
1. Existing Pinterest RSS generator verifies and saves public article data and original Shiori artwork.
2. Existing Instagram card generator prepares non-affiliate 1080x1350 images and source-faithful text with PR disclosure and an Instagram-profile-link call to action. It never publishes.
3. scripts/instagram/prepare_queue.py validates the source, publication date, article title, canonical article URL, exact original image filename and 1080x1350 PNG dimensions, and caption against article metadata.
4. The generated instagram/publish-queue.json intentionally has publishing_enabled=false, pilot_success_verified=false. It skips article IDs #512 (older vetted seed) and #516 (already booked pilot). Entries are candidates, not confirmed scheduled posts.
5. GitHub scheduled workflow creates and commits the queue alongside static images; it does not publish to Instagram or change WordPress/Pinterest/Threads.

## Remaining hard blockers
- Verify Metricool status for pilot #516 after 10:00 JST Oct 17. A PENDING, FAILED, or missing status cannot unlock automatic scheduling.
- Obtain a supported method for actual unattended Metricool scheduling. The official REST API requires Advanced or Custom; Metricool MCP via ChatGPT works even on Free, but ChatGPT plugin permissions do not hand GitHub a reusable token. Never put a password, OAuth cookie or API token into code, queue JSON, or public repo.
- Review live Metricool scheduled/recently published posts for same article ID/URL/title immediately before each new schedule. The GitHub queue alone has no visibility into live Metricool and cannot guarantee uniqueness. Do not rely only on local JSON as an authoritative remote ledger.
- Confirm Instagram auto-publish is supported and the image is accepted (pilot first). Keep one candidate per execution; future slot strictly later than current time, do not invent immediate backfills. On ambiguous API outcomes, stop rather than retrying duplicate posts.
- Metricool's official autolist pulls images from article webpage og:image, not from RSS enclosure. Do not enable an autolist against the ordinary WordPress RSS or parallel to another Instagram publisher without verifying images and duplicate prevention.

## Operational choice
On Free/Starter, schedule through the already connected Metricool MCP in a requested chat or an available ChatGPT task; adding a ChatGPT task may hit the five-active-task limit. The owner may choose to reuse/pause an existing task, but this queue does not modify their existing recurring task settings. On Advanced/Custom, a future separately verified API worker could be designed with repository secrets, pilot gate, duplicate checks, one-post quota, and manual activation. Never silently upgrade a paid plan or enable an unattended publisher.

Official sources:
- https://help.metricool.com/mcp-vs-api-access-what-is-the-difference-5y3ib
- https://help.metricool.com/basic-guide-for-api-integration-r97af
- https://help.metricool.com/what-is-an-rss-feed-and-how-does-it-work-in-metricool-1tupq
