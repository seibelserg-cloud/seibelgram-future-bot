# SEIBELGRAM | FUTURE CARS

Free-first AI concept channel bot for **@seibelgram** — isolated from APP24K/FLOW24K.

**Current state (2026-11-08):** Code uploaded. GitHub Actions offline preview CI passed. Cloudflare and Buffer account connections still required. **No live posting is enabled.**

- Generate two different futuristic car concepts (A/B format).
- Render vertical 720×1280 MP4 with original synthetic soundtrack using FFmpeg.
- Produce English captions and AI disclosure metadata.
- Use Cloudflare Workers AI REST API when two GitHub Secrets are configured.
- Buffer GraphQL publishing module is present but not called by the current safe workflow.
- GitHub Actions default: offline demo on push; scheduled real generation disabled until enabled separately.

## Quick start

See [instructions in Russian](SETUP_RU.md). Open [Actions](https://github.com/seibelserg-cloud/seibelgram-future-bot/actions) to view the verified offline run and download `seibelgram-preview` MP4.

**Safety:** never commit tokens; don't turn on a paid tier; do not auto-post until preview quality and account targeting have been confirmed.

## Cloudflare verification

GitHub Actions includes a one-off, secret-safe Workers AI connectivity test that requests a single image; social publishing stays disabled.
