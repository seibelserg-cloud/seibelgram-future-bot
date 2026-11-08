# SEIBELGRAM | FUTURE CARS

Free-first AI concept channel bot for **@seibelgram** — isolated from APP24K/FLOW24K.

**Current state (2026-11-08):** Code uploaded. GitHub Actions CI passed. Cloudflare Workers AI token verified; two real images and one MP4 already generated successfully. Buffer still not connected. **No live posting is enabled.**

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

A read-only Buffer API connection check can verify the configured TikTok account without making any posts. Secrets remain in GitHub Actions and are not printed.
