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
from image_models import get_image

OUT = Path("photo_output")

# Internal labels are only for metadata/captions; NEVER render labels in artwork.
THEMES = [
    ("MONOLITH",
     "An editorial photograph of a full-size 2070 experimental grand touring coupe, "
     "five meters long, very wide and extremely low. Its unbroken wedge-shaped sculpted "
     "body forms an architectural faceted ceramic shell. A long low front hood and a "
     "stretched rear deck frame a narrow windshield and a beautifully engineered canopy. "
     "The front wheel is plainly visible inside its own front wheel arch, and the rear "
     "wheel inside its separate rear wheel arch, with the rubber tires firmly on the ground. "
     "All four wheels are mechanically plausible; the near-side pair is visually distinct. "
     "The car has unusual open aerodynamic side channels and a breathtaking silhouette."),
    ("AERO BEAST",
     "A high-end automotive design photograph of an enormous 2060 experimental hypercar "
     "with an exceptionally long, flat aerodynamic nose, a low double-bubble glass roof, "
     "wide front fenders and twin structural flying buttresses sweeping toward the tail. "
     "The four black road wheels are correctly aligned on two axles, each visible "
     "near-side tire seated deeply inside its own integrated sculptural fender. "
     "A full-length ground-hugging body with engineered air channels creates an "
     "extraordinary but physically buildable new automotive silhouette."),
    ("SPACE LIMO",
     "A professional design-studio photograph of a six-meter 2075 executive grand tourer "
     "with a radical low-slung fastback profile, an impossibly elegant long wheelbase, "
     "beautifully stretched wheel-to-wheel proportions, blade-shaped aerodynamic sides "
     "and a continuous low dark glass roof. Both near-side black rubber wheels are "
     "clearly visible in conventional front and rear wheel arches with a long gap "
     "between the axles. The concept is a dramatic, enormous roadgoing grand tourer "
     "with coherent, production-feasible wheel and body engineering."),
]
# Deliberately NOT a catalog of chrome/silver cars at sunset.
# Keep color and location diversified independently across days and slots.
PALETTES = [
    "solid matte signal orange, black glass, absolutely no metallic flakes",
    "opaque acid-lime green ceramic paint with black graphite details",
    "flat electric ultramarine blue paint, black ceramic canopy",
    "saturated vermilion red matte enamel, dark smoky windows",
    "solid pastel-lilac pearlescent-free finish, charcoal glass",
    "vivid sunflower yellow smooth nonmetallic paint, ink-black glazing",
    "matte turquoise with restrained off-white secondary pieces",
    "deep solid raspberry-magenta enamel, black tires and glass",
    "muted terracotta orange clay-ceramic paint, dark gray windows",
    "opaque pale mint-green finish, graphite shadow details",
    "matte cobalt-violet finish with absolutely no reflective chrome",
    "powder-blue satin ceramic paint, cream accent surfaces",
]
LOCATIONS = [
    "empty white full-scale automotive wind tunnel, technical test lights and dry matte floor, neutral midday illumination",
    "vast chalk-white salt flats under clean bright noon sunshine, hard shadows, empty horizon, no buildings",
    "snow-covered Arctic wind-farm service road, pale winter morning, matte snow, clear blue daylight",
    "industrial shipping-container yard in cloudy daytime, rows of colorful freight containers, dry asphalt",
    "empty racing test runway with yellow road markings, overcast bright noon, grassy horizon, no buildings",
    "red volcanic gravel field with distant black lava cliffs, hard midmorning natural light, dusty ground",
    "color-blocked electric-blue photography cyclorama studio with hard frontal light, no architecture",
    "dry tropical coastal highway with palms and a turquoise sea, clear bright morning, no buildings",
    "fluorescent clean aerospace testing hangar with white modular walls, bright evenly diffused artificial lighting",
    "autumn farmland concrete lane with golden wheat and wind turbines, low-cloud daytime, no sunset",
    "large urban skatepark with colorful painted concrete ramps under bright noon daylight, no pavillion",
    "purple-gray high-altitude gravel road in a dry mountain plateau, midday sun and crisp distant peaks",
]
NO_OLD_LOOK = (
    "Absolutely NO sunset or sunrise, golden-hour lighting, wet reflective floor, marble-and-glass "
    "pavilion, curved luxury villa, mountain resort, glossy metallic silver, champagne gold, "
    "neon cyberpunk streets or repetitive architectural showroom. Different lighting and place."
)
VIEWS = [
    ("front_three_quarter", "low FRONT three-quarter camera, one complete side and entire nose visible"),
    ("true_side_profile", "STRICT true SIDE PROFILE, perpendicular 90-degree camera, entire silhouette from nose to tail"),
    ("rear_three_quarter", "low REAR three-quarter camera, one complete side and full tapered tail visible"),
    ("front_three_quarter_right", "low FRONT three-quarter camera from the opposite side, both axles and broad side silhouette visible"),
]

CORE_STYLE = (
    "This must be a startling design leap beyond today's road cars. Not an SUV, not a "
    "normal contemporary coupe. Photograph one complete and clearly recognizable "
    "full-scale automobile from bumper to bumper, all four tires connected to the "
    "body on two normal axles. Precisely engineered fender/wheel geometry with natural "
    "tire-to-ground contact. The subject fills most of the wide composition while "
    "leaving breathing room around all corners. Photorealistic automotive CGI with "
    "precise surface materials, plausible glass reflections, detailed rubber tires, "
    "professionally balanced lighting, clean crisp industrial design and natural shadows."
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
    rng = random.Random(f"SEIBELGRAM-VARIETY-03:{day}:{slot}")
    choices = list(THEMES) if showcase else rng.sample(THEMES, 2)
    # Deterministically rotate ALL 12 color/scene combinations before repeating.
    # Slots alternate between distant palette/setting indices, never same batch duplicates.
    ordinal = dt.date.fromisoformat(day).toordinal()
    base_color = (ordinal * 2 + slot - 1) % len(PALETTES)
    base_scene = (ordinal * 5 + (slot-1)*2) % len(LOCATIONS)
    colors = [PALETTES[(base_color + 5*i) % len(PALETTES)] for i in range(len(choices))]
    locations = [LOCATIONS[(base_scene + 5*i) % len(LOCATIONS)] for i in range(len(choices))]
    base = (int(day.replace("-", "")) + slot*2) % len(VIEWS)
    # Fixed three-quarter / full side views expose axle geometry during showcase review.
    views = [VIEWS[0], VIEWS[2], VIEWS[1]] if showcase else [
        VIEWS[(base+i) % len(VIEWS)] for i in range(len(choices))
    ]
    prompts = []
    for (_, design), color, place, (_, view) in zip(choices, colors, locations, views):
        prompt = (
            f"{design} Finish: {color}. Location: {place}. Camera: {view}. "
            f"{CORE_STYLE} {CLEAN} {NO_OLD_LOOK}"
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
        "day": day, "slot": slot, "creative_version": "FUTURE-VARIETY-03",
        "showcase": showcase, "image_model": "@cf/black-forest-labs/flux-2-klein-9b",
        "demo": demo, "images": [], "generation_errors": [],
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
        try:
            im = get_image(prompt, demo, i-1).convert("RGB")
            if im.width < 512 or im.height < 512:
                raise RuntimeError("Generated photo too small")
        except Exception as exc:
            # A temporary model failure must NEVER substitute another car or
            # silently publish. Keep working on the remaining concepts.
            manifest["generation_errors"].append({"concept":label,"error":type(exc).__name__})
            print(f"Generation FAILED for {label}: {type(exc).__name__}. Not publishing.")
            continue
        filename = f"car-{i}.jpg"
        im.save(OUT/filename, quality=94, optimize=True, subsampling=0)
        portrait_name = f"portrait-car-{i}.jpg"
        portrait_frame(im).save(OUT/portrait_name, quality=90, optimize=True, subsampling=0)
        manifest["images"].append({
            "file": filename, "portrait_file": portrait_name,
            "concept": label, "prompt": prompt, "width": im.width, "height": im.height
        })
        print(f"Saved FUTURE / IMPOSSIBLE concept {i}: {label}, {im.width}x{im.height}")
    manifest["generation_complete"]=(len(manifest["images"])==len(prompts))
    (OUT/"post.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created {len(manifest['images'])}/{len(prompts)} radical concepts; kept {len(manifest['generation_errors'])} failures for review. NOTHING published.")
    if not manifest["images"]:
        raise RuntimeError("No candidate image generated; inspect post.json, no publication.")

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
