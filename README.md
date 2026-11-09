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

## FUTURE / IMPOSSIBLE launch — 2026-11-09

The creative engine in `photo_bot.py` now uses **three extreme separate design directions**, replacing generic sedans, SUVs and coupes:

- **MONOLITH:** a single cast-metal vehicle architecture, radical glass capsule, giant recessed wheels
- **AERO BEAST:** a very long and low machine with enormous through-body air tunnels and fighter-style canopy
- **SPACE LIMO:** an extreme ultra-luxury ground vessel with a very long panorama capsule, no traditional sedan shell

Each prompt prioritizes unmistakable silhouette innovation over common LED facelift styling, and explicitly forbids text, badges, watermarks, brand marks, plates and collages. The video generator `bot.py` uses the same 3 directions. Photos are prepared as individual 1080×1920 portrait JPGs (with original image preserved in center); they are **not** actual new CAD camera angles and may still contain invented marks from the diffusion model.

`python photo_bot.py --showcase` requests all **three** designs in one run for offline review; ordinary scheduled generation still makes 2 candidates per batch. GitHub Actions is configured for a single showcase run; AI image QA and visual human review occur before **any** public post. Automatic public TikTok posting stays disabled.

### Showcase QA iteration 1

Run [42540650445](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions/runs/42540650445) generated three real AI concept photos and three 1080×1920 portraits. All passed code tests; automated visual QA declined all 3 for uncertain wheel/vehicle geometry and/or photo quality, so nothing was posted. This drove a second iteration: fixed front/rear axle and tire-ground-contact requirements and more informative front/side three-quarter views. The following showcase run tests those corrections.

### Showcase QA iteration 2

[Action 42540959213](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions/runs/42540959213) ran all photo tests and generated three separate 1024×1024 concept photographs plus 1080×1920 previews; artifact **seibelgram-photo-preview** contains images and `qa-report.json`. All three were conservatively rejected by the AI visual QA (questionable geometry/typography/professional quality). On manual inspection MONOLITH became an enclosed wheelless pod, AERO BEAST had a small mark and ambiguous wheel/layout geometry, and SPACE LIMO still lacked credible wheel architecture. Therefore **do not auto-post these photos**; improve model fidelity and visual QA before any unattended release. The new creative prompts and workflow remain in the repo for further tests.

Editorial benchmarks can be prepared separately, but generating a higher-quality image with an interactive image model does NOT mean the free Cloudflare generator has acquired that capability. Keep the unattended publishing safety lock in place.

### Free-plan alternative quality test

Cloudflare Workers AI lists `@cf/black-forest-labs/flux-2-klein-9b` as a hosted text-to-image model with multi-reference support. Official free-plan quota is 10,000 Neurons/day; a single 1024×1024 output uses about 1,364 Neurons at published rates. `verify_flux2_klein.py` requests **ONE** sample using multipart form data and existing Cloudflare Free secrets; it does not enable a paid tier or send any post. Production generators stay on the known model until the sample succeeds and visual quality is reviewed.

### Verified FLUX.2 Klein 9B on existing Free account

[Actions run 42541515481](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions/runs/42541515481) confirmed one actual `@cf/black-forest-labs/flux-2-klein-9b` generation using the existing Cloudflare Free token and multipart form API. The output is a recognizable 4-wheeled radical concept compared with earlier FLUX.1 batches. **No paid plan, API billing, or public social posting was activated.**

`photo_bot.py` now uses the tested `image_models.py` backend for candidate photos. This backend **fails closed** when free-tier capacity is exhausted or a token is unavailable, with no fallback to paid services or the low-fidelity generator. The legacy `bot.py` video path is unchanged to keep within the daily quota; FLUX.2 9B pricing currently uses roughly **1,364 Neurons per 1024² image**, with 10,000 free daily Neurons shared by all Workers AI inference. Two daily batches of two photos are approximately 5,455 Neurons before QA, but manual tests and other usage can consume additional daily allocation.

The FLUX.2 candidate batch is reviewed by `quality_gate.py` and archived. The scheduled jobs still do **not** publish to TikTok/Instagram.

### First 9B photo batch and transient error protection

[Workflow 42541887962](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions/runs/42541887962) confirmed new 9B photo engine and 26 offline tests, but after the first image Cloudflare returned **HTTP 500** during the second image. No public post was attempted. The bot now retries a **temporary model-side HTTP 500/502/503/504 only once**; it never retries Buffer publishing or Free quota errors, and it records partial successful photos in the Actions artifact. This update is tested by offline simulated 500 and partial-batch tests.

### FLUX.2 first successful full candidate batch — 2026-11-09

[Run 42542160170](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions/runs/42542160170): Both real FLUX.2 Klein 9B images generated successfully using the **existing Cloudflare Free account**, and every offline test passed. The artifact `seibelgram-photo-preview` contains two independent originals, two vertical 1080×1920 versions, metadata and quality report. Automated vision **withheld both**: the MONOLITH candidate did not meet the conservative confidence requirements for complete single vehicle/geometry/pro quality; the SPACE LIMO candidate also had possible branding. Manual review found designs not yet at high enough editorial standard for publication. Therefore **zero new social posts**; unattended publishing remains disabled.

The Free model experiment proved API compatibility but not automatic editorial-grade content. The strict gate is intentional. Separately created high-quality 9:16 concept artwork inside ChatGPT is an editorial benchmark, not a claim that unattended GitHub + Cloudflare will generate the same visuals.
