# SEIBELGRAM | FUTURE CARS

Free-first AI concept channel bot for **@seibelgram** — isolated from APP24K/FLOW24K.

**Current state (2026-11-08):** Code uploaded. GitHub Actions CI passed. Cloudflare Workers AI token verified; two real images and one MP4 already generated successfully. Buffer API authenticated and the TikTok channel @seibelgram verified in read-only mode (2026-11-08). **One public photo test succeeded on 2026-11-08. Scheduled candidate generation plus conservative vision QA are installed twice daily; continuous automatic public posting remains disabled pending QA calibration, anti-duplicate verification and the ongoing Buffer TikTok photo incident.**

- Generate two futuristic car concepts (A/B format, differentiated in the post description only).
- Render clean vertical 720×1280 MP4 with the original synthetic soundtrack using FFmpeg: **no titles, overlaid text, captions, logos, labels or watermark**.
- Produce English *post-description* copy and AI disclosure metadata, never text burned onto frames.
- Use Cloudflare Workers AI REST API when two GitHub Secrets are configured.
- Buffer GraphQL publishing module is present but not called by the current safe workflow.
- GitHub Actions default: offline demo on push; scheduled real generation disabled until enabled separately.

## Quick start

See [instructions in Russian](SETUP_RU.md). Open [Actions](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions) to view the verified offline run and download `seibelgram-preview` MP4.

**Safety:** never commit tokens; don't turn on a paid tier; do not auto-post until preview quality and account targeting have been confirmed.

## Cloudflare verification

GitHub Actions includes a one-off, secret-safe Workers AI connectivity test that requests a single image; social publishing stays disabled.

## Creative policy — 2026-11-08

The client explicitly requested **no typography in the video** and **no fictional branding or badges on cars**. The generation prompts forbid any emblems. This is a request to the model, not a proven guarantee; inspect each generated image before enabling automatic publishing. Audio generation remains unchanged; movement is optional (only a subtle transition between photos in this version). The TikTok AI-label, if required, must be applied in platform metadata rather than burned into the video.

## Buffer verification

**Verified on 2026-11-08:** Buffer API key works; the TikTok channel is @seibelgram. The read-only GitHub Actions check passed and created no posts. Secrets remain in GitHub Actions and are not printed. The posting pipeline stays locked pending public MP4 hosting and approval of emblem-free images.

## First verified public TikTok photo — 2026-11-08

The one-shot workflow published exactly one approved silver concept image as a vertical **1080×1920** photo through Buffer. GitHub Actions returned `sending`, then public TikTok was independently checked: [the post is live](https://www.tiktok.com/@seibelgram/photo/7705791143073598753), with the exact expected caption `A car from tomorrow. Would you drive it? ⚡ Fictional AI-generated concept. #FutureCars #ConceptCars #Seibelgram`. No automatic retry was attempted. The one-shot lock is saved in the repository; rerunning must never create a duplicate. This confirms a single successful live test **but does not authorize unattended repeat publishing**. Buffer's TikTok photo-post incident remains active at the time of testing.

## Autonomous visual QA and proposed publishing frequency — 2026-11-09

- **Target plan (not yet active public schedule):** 2 posts per day at **12:30 and 19:00 Europe/Berlin**. These are experimental slots, not proven best performing times.
- **Currently enabled:** GitHub Actions `daily_candidate_qa` on the two existing daily UTC cron events. It generates a pair of new AI photo candidates at each run, prepares a **separate 1080×1920 portrait per candidate** (blurred fill, untouched central car image), and runs `quality_gate.py --online` using Workers AI **`@cf/cloudflare/clef`**, within the Free quota. It stores the candidate photographs and `qa-report.json` as a seven-day Actions artifact. It does **not** call Buffer or TikTok.
- **Two independent checks:** Python checks image readability, resolution, nonblankness and similarity to stored images (difference hash). Clef makes conservative judgments about unbranded design, text/emblems, wheel/body geometry, futurism and professional photographic quality. If uncertain, API unavailable or out of quota, the candidate is rejected.
- **Vision test:** [GitHub Actions 42539316760](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions/runs/42539316760) ran the real visual QA successfully against two previous concept images. **Both were withheld:** original silver for uncertain geometric/photo quality and second image additionally for possible marks and weak futurism. These are model judgments and can contain false positives/negatives. The real public first post was manually approved by the owner before this model was added.
- **Public posting safety:** No unattended photo posts until we can avoid duplicates during Buffer's active TikTok photo issue and validate the AI gate. No paid subscriptions or required human daily work. A failed QA means *skip*, not *publish anyway*.
- The two generated photos are **separate files, no collage or overlay**. Camera prompts now vary across front three-quarter, true side, rear three-quarter and head-on.
- Quality gate tests: `python -m unittest -v test_quality_gate test_photos test_bot`.
