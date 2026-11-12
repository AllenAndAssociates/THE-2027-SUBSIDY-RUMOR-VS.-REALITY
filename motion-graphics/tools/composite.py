#!/usr/bin/env python3
"""Lays the keyed presenter over the HyperFrames graphics render, following each shot's layout.

  HR / HL : presenter large (92% height) on the white talk backdrop, right / left of the graphic
  B       : presenter head-and-shoulders inside the gold-ringed circle (ring + dark disc are drawn by the scene)
  F       : no presenter (full-bleed stat / diagram)
  S       : Shots 34-37, presenter in the left third

Usage: composite.py LAYER.mp4 SOURCE.mp4 OUT.mp4 [--ss SECONDS --t SECONDS]   (ss/t = test excerpt)
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_scenes as g

args = sys.argv[1:]
layer, src, out = args[0], args[1], args[2]
ss = float(args[args.index("--ss") + 1]) if "--ss" in args else 0.0
dur = float(args[args.index("--t") + 1]) if "--t" in args else g.TOTAL - ss

# ---- layout schedule: (start, end, layout)
sched = [(g.starts[i], g.ends[i], g.LAYOUT[i + 1][0]) for i in range(33)] + [(g.CLIP0, g.TOTAL, "S")]
win = {k: [] for k in ("HR", "HL", "B", "S")}
for a, b, lay in sched:
    if lay not in win:
        continue
    a2, b2 = max(a, ss) - ss, min(b, ss + dur) - ss
    if b2 > a2:
        win[lay].append((a2, b2))


def en(lay):
    if not win[lay]:
        return "enable=0"
    return "enable='%s'" % "+".join("between(t,%.3f,%.3f)" % w for w in win[lay])


HERO_W, HERO_H = 743, 994                        # 92% of 808x1080
hr_x = g.HERO_CX["HR"] - HERO_W // 2
hl_x = g.HERO_CX["HL"] - HERO_W // 2
bx, by, bd = g.BUBBLE
inner = bd - 20                                  # circle inside the ring
fc = f"""
[1:v]crop=808:1080:556:0,format=yuv420p,split=2[ka][kb];
[ka]chromakey=color=0x08B83C:similarity=0.14:blend=0.07,format=yuva420p,alphaextract,erosion,gblur=sigma=0.6[al];
[kb][al]alphamerge,tpad=stop_mode=clone:stop_duration=1.2,format=yuva420p,split=3[p1][p3][p4];
[p1]scale={HERO_W}:{HERO_H}:flags=lanczos,split=2[hA][hB];
[p3]crop=400:400:204:12,scale={inner}:{inner}:flags=lanczos,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lt(hypot(X-W/2,Y-H/2),W/2),alpha(X,Y),0)'[bub];
[p4]scale=728:972:flags=lanczos[sd];
[0:v][hA]overlay=x={hr_x}:y={1080 - HERO_H}:{en('HR')}:eof_action=pass[v1];
[v1][hB]overlay=x={hl_x}:y={1080 - HERO_H}:{en('HL')}:eof_action=pass[v2];
[v2][bub]overlay=x={bx + 10}:y={by + 10}:{en('B')}:eof_action=pass[v3];
[v3][sd]overlay=x=-29:y=108:{en('S')}:eof_action=pass,format=yuv420p[v]
"""
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats"]
if ss:
    cmd += ["-ss", str(ss)]
cmd += ["-i", layer]
if ss:
    cmd += ["-ss", str(ss)]
cmd += ["-i", src, "-filter_complex", fc.replace("\n", ""), "-map", "[v]", "-map", "0:a?", "-t", str(dur),
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-af", "alimiter=limit=0.891:attack=3:release=60:level=disabled", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
print("windows:", {k: len(v) for k, v in win.items()}, "| excerpt ss=%.1f t=%.1f" % (ss, dur))
sys.exit(subprocess.call(cmd))
