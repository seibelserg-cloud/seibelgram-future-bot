#!/usr/bin/env python3
"""SEIBELGRAM: AI concept battle -> vertical MP4. Default is offline demo."""
import argparse
import base64
import datetime as dt
import io
import json
import math
import os
import random
import subprocess
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
import requests

ROOT=Path(__file__).resolve().parent
SITE=ROOT/"site"
MODEL="@cf/black-forest-labs/flux-1-schnell"
CARS=[
 ("HYPERCAR","radical two-seat electric hypercar with aerodynamic channels"),
 ("GT TOURING","sleek futuristic long-roof grand touring shooting brake"),
 ("LUXURY SEDAN","four-door high-performance executive sports sedan"),
 ("CYBER ROADSTER","low futuristic open-cockpit two-seat roadster"),
 ("TRACK PROTOTYPE","dramatic experimental track-inspired coupe"),
 ("FUTURE WAGON","muscular aerodynamic luxury electric touring car"),
 ("ELECTRIC COUPE","avant-garde sculptural electric sport coupe")
]
COLORS=["liquid chrome","champagne titanium","deep emerald metallic","graphite silver","pearl white","cobalt blue","warm bronze metallic"]
PLACES=["a monumental polished-concrete architectural studio","a coastal modernist pavilion at dusk","a minimalist glass-and-steel automotive design museum","a white futuristic design laboratory"]

def concept(day, slot):
    rng=random.Random(f"SEIBELGRAM-03:{day}:{slot}")
    (na,sa),(nb,sb)=rng.sample(CARS,2)
    ca,cb=rng.sample(COLORS,2)
    place=rng.choice(PLACES)
    year=rng.randint(2040,2065)
    def prompt(subject,color):
        return (f"Photorealistic high-end automotive CGI photograph of ONE original concept car for year {year}: "
                f"{subject}, {color} paint. Located in {place}. Full car visible from a low front 3/4 angle, "
                "four believable rubber tires, crisp natural cinematic studio lighting, coherent headlights, "
                "realistic reflections, daring futuristic industrial design, premium magazine composition. "
                "No existing brand logos, no letters, no watermark, no people, no collage, no distorted anatomy.")
    return dict(title=f"FUTURE CARS {year}: A vs B",date=day,slot=slot,
                prompts=[prompt(sa,ca),prompt(sb,cb)],
                labels=[na,nb],
                caption=(f"Which future car wins? ⚡ {year} design battle: A ({na}) vs B ({nb}). "
                         "Comment A or B 👇\n\n#FutureCars #ConceptCars #CarDesign #Seibelgram #AIArt\n"
                         "Fictional AI-generated concepts. Not real vehicles."),
                ai_generated=True)

def get_image(prompt, demo, index):
    if demo:
        im=Image.new("RGB",(1024,1024),(12,19,34))
        d=ImageDraw.Draw(im)
        d.ellipse((105,480,910,820),fill=(65,110+index*40,140+index*30))
        d.polygon([(100,660),(300,430),(700,425),(905,670)],fill=(165,190,205))
        d.ellipse((220,690,355,820),fill=(5,11,20))
        d.ellipse((645,690,780,820),fill=(5,11,20))
        d.text((25,30),"OFFLINE DEMO — NOT AI ART",fill="white")
        return im
    account=os.environ.get("CF_ACCOUNT_ID","").strip()
    token=os.environ.get("CF_API_TOKEN","").strip()
    if not account or not token:
        raise RuntimeError("Cloudflare secrets missing: CF_ACCOUNT_ID / CF_API_TOKEN")
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    response=requests.post(url,json={"prompt":prompt[:2048],"steps":6},
                headers={"Authorization":f"Bearer {token}"},timeout=150)
    response.raise_for_status()
    body=response.json()
    if not body.get("success") or not body.get("result",{}).get("image"):
        raise RuntimeError("Cloudflare image generation returned no image")
    raw=base64.b64decode(body["result"]["image"],validate=True)
    image=Image.open(io.BytesIO(raw)).convert("RGB")
    if min(image.size)<256: raise RuntimeError("Generated image unexpectedly small")
    return image

def get_font(size,bold=False):
    files=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for f in files:
        if Path(f).exists(): return ImageFont.truetype(f,size)
    return ImageFont.load_default()

def slide(image,label,index,demo):
    im=ImageOps.fit(image,(720,1280)).filter(ImageFilter.GaussianBlur(30)).convert("RGBA")
    im=Image.alpha_composite(im,Image.new("RGBA",(720,1280),(3,8,16,135)))
    art=ImageOps.contain(image,(690,790)).convert("RGBA")
    im.alpha_composite(art,((720-art.width)//2,210+(790-art.height)//2))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((18,28,702,135),radius=16,fill=(5,9,18,220))
    d.text((40,47),"SEIBELGRAM  /  FUTURE CARS",font=get_font(28,True),fill="white")
    d.text((40,98),"ORIGINAL AI CONCEPT ART",font=get_font(17),fill="#92bbd7")
    d.rounded_rectangle((18,1080,702,1250),radius=20,fill=(5,9,18,215))
    d.text((42,1100),f"CONCEPT {'A' if index==0 else 'B'}",font=get_font(53,True),fill="white")
    d.text((42,1180),("DEMO ONLY — NOT PUBLISHED" if demo else "AI GENERATED • COMMENT A OR B"),
           font=get_font(21),fill="#b8cedb")
    return im.convert("RGB")

def original_audio(path,seconds=17):
    from array import array
    rate=22050
    pcm=array("h")
    for i in range(rate*seconds):
        t=i/rate
        envelope=min(1,t/1.3,max(0,(seconds-t)/1.2))
        v=(math.sin(2*math.pi*110*t)+.22*math.sin(2*math.pi*165*t))
        pcm.append(int(2100*v*envelope))
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())

def render(day,slot,demo):
    meta=concept(day,slot)
    SITE.mkdir(exist_ok=True)
    (SITE/"media").mkdir(exist_ok=True)
    paths=[]
    for idx,prompt in enumerate(meta["prompts"]):
        art=get_image(prompt,demo,idx)
        path=SITE/f"slide-{idx+1}.jpg"
        slide(art,meta["labels"][idx],idx,demo).save(path,quality=90)
        paths.append(path)
    audio=SITE/"sound.wav"
    original_audio(audio)
    video=SITE/"media"/f"{day}-{slot}.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-loop","1","-t","9","-i",str(paths[0]),
         "-loop","1","-t","9","-i",str(paths[1]),"-i",str(audio),
         "-filter_complex","[0:v]fps=24,format=yuv420p[v0];[1:v]fps=24,format=yuv420p[v1];"
                           "[v0][v1]xfade=transition=fade:duration=1:offset=8[v]",
         "-map","[v]","-map","2:a","-c:v","libx264","-preset","veryfast",
         "-crf","24","-pix_fmt","yuv420p","-c:a","aac","-b:a","96k",
         "-movflags","+faststart","-t","17",str(video)]
    subprocess.run(cmd,check=True)
    audio.unlink(missing_ok=True)
    if video.stat().st_size<10000:raise RuntimeError("Bad video output")
    meta["video_file"]=f"media/{video.name}"
    meta["demo"]=demo
    (SITE/"post.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    (SITE/"index.html").write_text("<!doctype html><meta charset='utf-8'><h1>SEIBELGRAM AI concepts</h1>",encoding="utf-8")
    print(f"Created {video} ({video.stat().st_size} bytes), demo={demo}")
    return video

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true")
    p.add_argument("--day",default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    p.add_argument("--slot",type=int,choices=(1,2),default=1)
    a=p.parse_args()
    render(a.day,a.slot,a.demo)

if __name__=="__main__":main()
