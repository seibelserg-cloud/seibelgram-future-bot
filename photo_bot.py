#!/usr/bin/env python3
"""SEIBELGRAM | FUTURE / IMPOSSIBLE: radical concept-car photo candidates.

This module generates images and safe 9:16 previews. IT NEVER POSTS.
Each candidate is a separate photograph; no collages or typography.
"""
import argparse
import datetime as dt
import json
import random
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
from bot import get_image

OUT = Path("photo_output")

# Internal labels are only for metadata/captions; NEVER render labels in artwork.
THEMES = [
    ("MONOLITH",
     "A radically original 2055 monolithic mobility sculpture. One seamless cast-metal volume like a liquid "
     "titanium pebble shaped by supersonic wind. A continuous ultra-low black glass cockpit is fused into the "
     "upper shell; the four enormous wheels emerge from precise circular cutouts in otherwise perfectly calm "
     "surfaces. No visible bonnet seam, conventional grille, door handles or typical passenger-car architecture. "
     "The silhouette must be a striking single architectural gesture, not a familiar coupe. "
     "Two large distinct front/rear wheel arches on the camera-facing side must reveal clearly separated "
     "real rubber tires and mechanical wheel rims; NEVER a featureless wheelless pod."),
    ("AERO BEAST",
     "An unprecedented 2060 high-speed aerodynamic organism, ultra-low and extremely long, with twin huge "
     "load-bearing flying buttresses, open-air tunnels passing THROUGH the sculptural central body, an elongated "
     "fighter-jet glass canopy, an extreme tapered tail, four huge engineered wheels and exceptionally wide track. "
     "Aggressively beautiful, almost impossible but mechanically plausible. No ordinary supercar nose, generic "
     "sports-car proportions, conventional radiator grille or pasted-on wings. "
     "The vehicle must have EXACTLY four conventional ground-contact tires, in a believable front and rear "
     "axle layout. Two distinctly visible wheels on the near side, neither hovering nor merging with wings."),
    ("SPACE LIMO",
     "A visionary 2058 ultra-luxury ground vessel, with extremely long wheelbase, panoramic teardrop-shaped "
     "glass passenger capsule, radically sculpted continuous floating outer hull, dramatically extended rear "
     "deck and four large partly recessed wheels. Futuristic mobile architecture, peaceful yet imposing, "
     "almost spacecraft-like without flying. No typical four-door sedan body, no SUV cabin, no boxy roof, "
     "no familiar luxury brand design or conventional trunk. "
     "It MUST visibly roll on exactly four real rubber tires, two distinct wheels on the visible side, "
     "with realistic front and rear axles and ground contact, never hover or use duplicate wheel pairs.")
]
PALETTES = [
    "brushed liquid platinum with obsidian glazing",
    "deep petroleum blue iridescent titanium",
    "warm oxidized bronze with graphite shadow surfaces",
    "pearl-ceramic white with anthracite glass",
    "satin dark chromium with subtle copper reflections",
    "polished meteorite silver with smoked glass"
]
LOCATIONS = [
    "vast minimal polished-concrete museum with sculptural light openings, dusk",
    "monumental futuristic architecture of curving stone and deep shadow, sunrise",
    "quiet high-end experimental automotive gallery, charcoal walls and soft luminous floor"
]
VIEWS = [
    ("front_three_quarter", "low FRONT three-quarter camera, one complete side and entire nose visible"),
    ("true_side_profile", "STRICT true SIDE PROFILE, perpendicular 90-degree camera, entire silhouette from nose to tail"),
    ("rear_three_quarter", "low REAR three-quarter camera, one complete side and full tapered tail visible"),
    ("front_head_on", "low centered FRONT head-on camera, symmetric nose and both front wheels visible"),
]

CORE_STYLE = (
    "Create a museum-grade radically new transportation sculpture, an unmistakable design leap beyond "
    "ALL contemporary 2020s/2030s production cars. Unforgettable exterior massing and innovative silhouette "
    "are FAR more important than headlights, surface graphics or LED stripes. This is NOT an SUV, "
    "NOT a conventional sports coupe, NOT a facelift, NOT a recognizable brand or current road car. "
    "Photorealistic premium industrial-design CGI, physically coherent surfaces and wheel placement, "
    "4 distinct ground-touching tires on 2 axles, BOTH wheel arches clearly visible on near side, "
    "nonhovering realistic chassis, sophisticated reflections, rich architectural lighting, entirely visible "
    "vehicle with space around its edges, ONE vehicle only."
)
CLEAN = (
    "NO manufacturer identity; completely BLANK nose, hood, body and wheel hubs. "
    "Absolutely no badges, fake emblems, branding, crests, insignia, stickers, letters, numbers, "
    "license plates, inscriptions, text, title, signs, watermark, people, split screen or collage."
)

def portrait_frame(image):
    """Vertical 9:16; preserve whole original geometry (no fake new camera view)."""
    canvas = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
    canvas = canvas.filter(ImageFilter.GaussianBlur(42)).convert("RGB")
    art = ImageOps.contain(image, (1080, 1680), method=Image.Resampling.LANCZOS).convert("RGB")
    canvas.paste(art, ((1080-art.width)//2, (1920-art.height)//2))
    return canvas

def prompts_for(day, slot, showcase=False):
    # Distinct silhouettes each slot, rotating 3 families. Different dates/slots diversify.
    rng = random.Random(f"SEIBELGRAM-IMPOSSIBLE-01:{day}:{slot}")
    choices = list(THEMES) if showcase else rng.sample(THEMES, 2)
    colors = rng.sample(PALETTES, len(choices))
    locations = rng.sample(LOCATIONS, len(choices))
    base = (int(day.replace("-", "")) + slot*2) % len(VIEWS)
    # Fixed three-quarter / full side views expose axle geometry during showcase review.
    views = [VIEWS[0], VIEWS[2], VIEWS[1]] if showcase else [
        VIEWS[(base+i) % len(VIEWS)] for i in range(len(choices))
    ]
    prompts = []
    for (_, design), color, place, (_, view) in zip(choices, colors, locations, views):
        prompt = (
            f"{design} Finish: {color}. Location: {place}. Camera: {view}. "
            f"{CORE_STYLE} {CLEAN}"
        )
        # The currently used Flux endpoint in bot.py caps outgoing prompt at 2048 chars.
        if len(prompt) > 2048:
            raise ValueError("Future concept prompt exceeds Cloudflare Flux request cap")
        prompts.append(prompt)
    return choices, prompts

def run(day, slot, demo=False, showcase=False):
    themes, prompts = prompts_for(day, slot, showcase=showcase)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "day": day, "slot": slot, "creative_version": "FUTURE-IMPOSSIBLE-01",
        "showcase": showcase,
        "demo": demo, "images": [],
        "requires_visual_review": True,
        "approved_for_publication": False,
        "ai_generated": True,
        "title": "FUTURE / IMPOSSIBLE — which vision wins?",
        "caption": "Which impossible car would you actually drive: 1 or 2? "
                   "⚡ Fictional AI-generated car concept art. "
                   "#FutureCars #ConceptCars #ImpossibleDesign #Seibelgram",
        "platform": "tiktok", "published": False
    }
    for i, ((label, _), prompt) in enumerate(zip(themes, prompts), start=1):
        im = get_image(prompt, demo, i-1).convert("RGB")
        if im.width < 512 or im.height < 512:
            raise RuntimeError("Generated photo too small")
        filename = f"car-{i}.jpg"
        im.save(OUT/filename, quality=94, optimize=True, subsampling=0)
        portrait_name = f"portrait-car-{i}.jpg"
        portrait_frame(im).save(OUT/portrait_name, quality=90, optimize=True, subsampling=0)
        manifest["images"].append({
            "file": filename, "portrait_file": portrait_name,
            "concept": label, "prompt": prompt, "width": im.width, "height": im.height
        })
        print(f"Saved FUTURE / IMPOSSIBLE concept {i}: {label}, {im.width}x{im.height}")
    (OUT/"post.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created {len(prompts)} radical concept photos + separate 9:16 portraits. NOTHING published.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--day", default=dt.date.today().isoformat())
    p.add_argument("--slot", type=int, default=1, choices=[1, 2])
    p.add_argument("--demo", action="store_true")
    p.add_argument("--showcase", action="store_true", help="Generate one separate still for each of 3 design families")
    args = p.parse_args()
    run(args.day, args.slot, args.demo, showcase=args.showcase)

if __name__ == "__main__":
    main()
