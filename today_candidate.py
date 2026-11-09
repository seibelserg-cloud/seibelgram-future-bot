#!/usr/bin/env python3
"""One dated experimental image for manual editorial review. Does not publish."""
import json
from pathlib import Path
from image_models import get_image
from photo_bot import portrait_frame
from PIL import Image
DEST=Path("today_candidate")
PROMPT=(
 "An unforgettable super-futuristic full-size 2060 hypercar, five meters long and two meters wide, "
 "bright SOLID MATTE cadmium-yellow bodywork with sharp sculptural side cutouts and black glass roof, "
 "completely NEW architecture compared with contemporary exotic cars. Full-size automotive engineering: "
 "four physically plausible black rubber tires in exactly two axles, near-side front and rear wheel "
 "distinctly visible in dramatic body-integrated arches. Extreme dart-shaped front, broad rear aero "
 "fins and two large open through-body air tunnels. Full car visible from a low front three-quarter "
 "angle, no cropping. Large white automotive wind tunnel, huge circular fan in distant background, "
 "dry matte gray floor with dark technical marking lines, brilliant cool neutral DAYLIGHT. "
 "No shiny chrome, no metallic or silver paint, no neon, no sunset, no rain, no night, no mountains, "
 "no luxury pavilion, no glass skyscrapers, no glossy showroom. "
 "Truly stunning high-end crisp photorealistic automotive design render with realistic tire placement, "
 "correct mechanical perspective, sharp focus and cinematic depth. "
 "Entire car unbranded: no badges, logos, symbols, license plates, letters, text or watermarks. "
 "Exactly one original concept vehicle. Single photo, no collage."
)
def main():
    DEST.mkdir(exist_ok=True)
    im=get_image(PROMPT,False,0).convert("RGB")
    im.save(DEST/"source.jpg",quality=93,optimize=True)
    portrait_frame(im).save(DEST/"portrait.jpg",quality=93,optimize=True)
    (DEST/"caption.json").write_text(json.dumps({
        "day":"2026-11-09","status":"UNREVIEWED","published":False,
        "source":"Cloudflare FLUX2 Klein 9B","prompt":PROMPT,
        "caption":"From another century. ⚡ Would you actually drive this? Fictional AI-generated future-car concept. #FutureCars #ConceptCars #CarDesign #Seibelgram"
    },indent=2),encoding="utf-8")
    print("SUCCESS: today's single fresh concept generated, 9:16 portrait ready. NO PUBLICATION.")
if __name__=="__main__": main()
