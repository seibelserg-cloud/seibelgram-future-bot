#!/usr/bin/env python3
"""SEIBELGRAM: make a 9-second vertical short with ORIGINAL synthesized music.

No samples, copyrighted tracks, TikTok audio-library access, paid APIs or posting.
Source JPG remains visually intact except for subtle cinematic parallax movement.
"""
import argparse
import json
import math
import subprocess
import wave
from array import array
from pathlib import Path
from PIL import Image

DURATION=9
FPS=24
RATE=22050
WIDTH=720
HEIGHT=1280

STYLES={
    "neon-pulse":{"bpm":114,"root":110.0,"notes":[0,3,7,10],"pulse":0.16},
    "deep-motion":{"bpm":104,"root":82.407,"notes":[0,5,7,12],"pulse":0.21},
    "glacier-drive":{"bpm":96,"root":123.47,"notes":[0,4,7,11],"pulse":0.13}
}

def original_soundtrack(path,style="neon-pulse",seconds=DURATION):
    """Deterministic original non-sampled soundtrack with tonal pad, sub pulses and hi-hats."""
    if style not in STYLES:raise ValueError("Unknown soundtrack style")
    a=STYLES[style]
    bpm=a["bpm"];period=60.0/bpm;root=a["root"]
    chord=[root*(2**(n/12)) for n in a["notes"]]
    samples=array("h")
    # deterministic percussive micro-noise (not copied recorded audio)
    noise=0xAC451
    for i in range(int(seconds*RATE)):
        t=i/RATE
        envelope=min(1.0,t/.42,max(0.0,(seconds-t)/.75))
        # transparent evolving 4-note synth pad
        pad=sum(math.sin(2*math.pi*f*t + .065*math.sin(2*math.pi*.18*t))*0.17
                for f in chord)
        pad += .09*math.sin(2*math.pi*root*.5*t)
        # soft bass throb at beats
        phase=t%period
        beat_env=math.exp(-phase*11)
        kick=.34*beat_env*math.sin(2*math.pi*55*t-19*math.exp(-phase*32))
        # high frequency tick pulses on offbeats
        hat_phase=(t+period/2)%period
        hat_env=math.exp(-hat_phase*65)
        noise=(noise*1664525+1013904223)&0xFFFFFFFF
        white=((noise>>16)/32768)-1
        tick=.055*hat_env*white
        # light 4-step arpeggio in original modal chord
        note_index=int(t/(period/2))%4
        arpf=chord[note_index]*2
        arp_env=math.exp(-(t%(period/2))*10)
        arp=.13*arp_env*math.sin(2*math.pi*arpf*t)
        output=(pad*a["pulse"]/.16+kick+tick+arp)*envelope
        samples.append(int(max(-.96,min(.96,output))*23000))
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(p),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(samples.tobytes())
    return p

def build(image,output,style="neon-pulse"):
    src=Path(image);dst=Path(output)
    if not src.is_file():raise FileNotFoundError(src)
    with Image.open(src) as im:
        if im.width<512 or im.height<512:raise RuntimeError("Image too small")
        if not 0.50<=im.width/im.height<=0.58:
            raise RuntimeError("Input must already be a vertical 9:16 photograph, not a collage")
    dst.parent.mkdir(parents=True,exist_ok=True)
    audio=dst.with_suffix(".original-audio.wav")
    original_soundtrack(audio,style)
    # Slightly overscale 9:16 artwork and pan a few pixels across 9s.
    # No titles, captions, logos, overlays, samples or music platform dependencies.
    vf=("scale=768:1366:flags=lanczos,"
        "crop=720:1280:x='24+10*sin(n/40)':y='43+17*cos(n/55)',"
        "fps=24,format=yuv420p,fade=t=in:st=0:d=0.25,"
        "fade=t=out:st=8.65:d=0.35")
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-loop","1","-framerate",str(FPS),"-i",str(src),
         "-i",str(audio),
         "-vf",vf,"-t",str(DURATION),
         "-map","0:v:0","-map","1:a:0",
         "-c:v","libx264","-preset","veryfast","-crf","22",
         "-pix_fmt","yuv420p","-r",str(FPS),
         "-c:a","aac","-b:a","128k","-ar","44100",
         "-movflags","+faststart","-shortest",str(dst)]
    try:
        subprocess.run(cmd,check=True,timeout=150)
        if dst.stat().st_size<30_000:
            raise RuntimeError("Encoded video suspiciously small")
    finally:
        audio.unlink(missing_ok=True)
    return dst

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--image",required=True)
    ap.add_argument("--output",default="music_preview/seibelgram-original-sound.mp4")
    ap.add_argument("--style",choices=list(STYLES),default="neon-pulse")
    a=ap.parse_args()
    p=build(a.image,a.output,a.style)
    print(json.dumps({"result":"review_only","mp4":str(p),"duration_s":DURATION,
        "resolution":[WIDTH,HEIGHT],"original_audio":True,"copyrighted_samples":False,
        "published":False,"style":a.style},ensure_ascii=False))
if __name__=="__main__":main()
