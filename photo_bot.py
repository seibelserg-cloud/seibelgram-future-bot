#!/usr/bin/env python3
"""Generate unbranded, no-overlay, no-text concept car PHOTOS for visual approval.

No social publishing happens here. GitHub workflow uploads photos as an artifact.
"""
import argparse
import datetime as dt
import json
import random
from pathlib import Path
from PIL import Image
from bot import get_image

OUT = Path("photo_output")
THEMES = [
    ("SILVER PHANTOM", "silver ceramic electric hypercar, extremely low sweeping roof, sculpted continuous aerodynamic silhouette, full-width diffuse glass lighting, original form never seen in production"),
    ("TOURING ZERO", "long-roof ultra-modern luxury grand touring wagon, elegant floating glass canopy, dramatic wheel arches, sculptural continuous surfaces, athletic proportions"),
    ("NOVA ROADSTER", "open-top all-electric speedster with smooth flowing bodywork, advanced lightweight cockpit, delicate blade-thin lighting surfaces"),
    ("ONYX GT", "black titanium two-seat futuristic grand tourer with intense minimalist body lines, sculpted side air channels and a clean seamless hood"),
    ("ATLAS SEDAN", "radical next-generation executive electric sports sedan, four doors, floating panoramic glazing, wide athletic proportions, sculptural edges"),
    ("AETHER COUPE", "original futuristic fastback coupe, long uninterrupted hood, tiny futuristic light lines, deep flowing wheel arches")
]
PALETTES = ["polished satin platinum","gunmetal graphite","pearl white","oxidized bronze","deep electric cobalt","liquid silver"]
LOCATIONS = [
    "a huge architectural photography studio with warm directional sun and physically accurate soft floor shadows",
    "an illuminated premium concrete pavilion at dusk with soft atmospheric depth and realistic reflected light",
    "a silent minimalist design gallery with sophisticated indirect lighting and dramatic physically realistic shadows"
]
def prompts_for(day,slot):
    rng=random.Random(f"SEIBELGRAM-photos-v1:{day}:{slot}")
    choices=rng.sample(THEMES,2)
    colors=rng.sample(PALETTES,2)
    locations=rng.sample(LOCATIONS,2)
    prompts=[]
    for (name,design),color,place in zip(choices,colors,locations):
        prompts.append(
            f"Commercial luxury automotive concept photography, visually breathtaking original imagined car: {design}. "
            f"Finish: {color}; environment: {place}. Three-quarter SIDE / rear oblique view, whole car visible, "
            "premium high-end CGI indistinguishable from a professional car photography campaign, complex "
            "realistic reflections, rich volumetric shadows, purposeful functional automotive details, "
            "coherent tires and wheels, cinematic photographic lens, no floating car. "
            "The hood and entire body are BLANK unmarked sculptural surfaces. The car is completely UNBRANDED. "
            "Smooth empty wheel hubs, no center caps, blank grille area, no badge platform, no crests, no logos "
            "or symbols, no letters, no numbers, no branding, no license plate, no labels, no text, no watermark. "
            "A novel imagined object, not copied from a manufacturer. Exactly one vehicle, no collage."
        )
    return choices,prompts

def run(day,slot,demo=False):
    themes,prompts=prompts_for(day,slot)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest={
        "day":day,"slot":slot,"demo":demo,"images":[],"requires_visual_review":True,
        "approved_for_publication":False,"ai_generated":True,
        "title":"Which future car would you drive?",
        "caption":"Which one would you drive — the first or the second? ⚡🚘\n\n"
                  "Imaginary AI-generated car concepts. #FutureCars #ConceptCars #CarDesign #Seibelgram",
        "platform":"tiktok","published":False
    }
    for i, ((label,_),prompt) in enumerate(zip(themes,prompts),start=1):
        im=get_image(prompt,demo,i-1).convert("RGB")
        if im.width<512 or im.height<512:
            raise RuntimeError("Generated photo too small")
        filename=f"car-{i}.jpg"
        im.save(OUT/filename, quality=94, optimize=True, subsampling=0)
        manifest["images"].append({"file":filename,"concept":label,"prompt":prompt,
            "width":im.width,"height":im.height})
        print(f"Saved image {i}: {filename}, {im.width}x{im.height}")
    (OUT/"post.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print("SUCCESS: 2 photo previews created. Nothing published. Visual approval is required.")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day",default=dt.date.today().isoformat())
    p.add_argument("--slot",type=int,default=1,choices=[1,2])
    p.add_argument("--demo",action="store_true")
    args=p.parse_args()
    run(args.day,args.slot,args.demo)

if __name__=="__main__":main()
