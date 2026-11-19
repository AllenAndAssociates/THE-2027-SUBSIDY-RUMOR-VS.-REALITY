#!/usr/bin/env python3
"""Generate the vertical 9:16 shorts that funnel to the full 2027 Medicare costs video.

Native-creator style: the HeyGen avatar fills the frame, bold captions, and the key number
pops in as it is spoken. It ends with one soft line in the ElevenLabs "Arric Allen" clone voice
over a blurred freeze-frame, pointing to the full video on the channel. No logo/card/phone.

Run:  python3 build.py   (writes <slug>/index.html, one project per short)
Render (from <slug>/): npx hyperframes render -f 25 -o ../../renders/shorts/<slug>.mp4
"""
import html
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
WORDS = json.load(open(HERE / "assets/transcript-main.json"))

# Whisper glues a few tokens together and mishears two names; fix them for captions.
FIXES = [
    (r"\bB(monthly|deductible|premium|coinsurance|changes)", r"B \1"),
    (r"\bD(drug|deductible|prescription|so)\b", r"D \1"),
    (r"\bGor\b", "G or"),
    (r"IRMA-A", "IRMAA"),
    (r"\bEric\b", "Arric"),
]

SHORTS = [
    {
        "slug": "part-b",
        "src_in": 50.55, "src_out": 81.4,
        "eyebrow": "2027 Medicare · Part B",
        "hook": "Your Part B premium<br/>is going <span class=\"hot\">UP</span> in 2027",
        "rows": [
            # label, old, new, tag, src time the number is spoken
            ("Monthly premium", "$202.90", "$209.40", "+$6.50/mo", 57.73),
            ("Per year · individual", None, "$2,512.80", None, 65.34),
            ("Per year · married couple", None, "$5,025.60", None, 68.87),
            ("Part B deductible", "$283", "$292", "+$9", 79.1),
        ],
        "stamp": None,
        "cta": "cta-part-b.m4a",
        "cta_line": "That's just Part B.",
    },
    {
        "slug": "medigap",
        "src_in": 81.95, "src_out": 116.0,
        "eyebrow": "2027 Medicare · Medigap",
        "hook": "Have Plan G or Plan N?<br/><span class=\"hot\">Circle this number</span>",
        "rows": [
            ("Plan G & N · 20% coinsurance", None, "Covered ✓", None, 87.72),
            ("Your 2027 deductible to circle", None, "$292", None, 98.82),
            ("High-Deductible G ceiling", "$2,950", "$3,050", "+$100", 108.78),
        ],
        "stamp": None,
        "cta": "cta-medigap.m4a",
        "cta_line": "Every 2027 number in one place.",
    },
    {
        "slug": "irmaa",
        "src_in": 125.1, "src_out": 166.5,
        "eyebrow": "2027 Medicare · IRMAA",
        "hook": "The <span class=\"hot\">$1 IRMAA cliff</span><br/>that costs high earners",
        "rows": [
            ("2027 IRMAA is based on your", None, "2025 tax return", None, 136.56),
            ("Single · no surcharge up to", "$109,000", "$112,000", None, 144.73),
            ("Married jointly · up to", "$218,000", "$224,000", None, 148.32),
        ],
        "stamp": ("$1 OVER = FULL-YEAR SURCHARGE", 156.17),
        "cta": "cta-irmaa.m4a",
        "cta_line": "See what triggers IRMAA and how to appeal it.",
    },
    {
        "slug": "part-a-d",
        "src_in": 197.85, "src_out": 237.7,
        "eyebrow": "2027 Medicare · Part A & D",
        "hook": "2027 hospital & drug<br/>costs are <span class=\"hot\">rising</span>",
        "rows": [
            ("Part A premium (40+ quarters)", None, "$0", None, 206.3),
            ("Part A hospital deductible", "$1,736", "$1,776", "+$40", 216.43),
            ("Part D max deductible", "$615", "$700", "+$85", 227.27),
            ("Part D out-of-pocket cap", "$2,100", "$2,400", "+$300", 234.08),
        ],
        "stamp": None,
        "cta": "cta-part-a-d.m4a",
        "cta_line": "Get the full 2027 picture.",
    },
]


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout
    return float(out)


def clean(t):
    for a, b in FIXES:
        t = re.sub(a, b, t)
    return t


def chunk(ws, total_end):
    """ws: [{t,s}] in film time -> [(start, end, text)] chunks of <=3 words."""
    chunks, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        if len(cur) >= 3 or re.search(r"[.,?!]$", w["t"]) or nxt is None or nxt["s"] - w["s"] > 0.9:
            chunks.append(cur)
            cur = []
    out = []
    for i, c in enumerate(chunks):
        end = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else total_end
        out.append((max(0, c[0]["s"]), end, " ".join(x["t"] for x in c)))
    return out


def avatar_words(src_in, src_out):
    ws = []
    for w in WORDS:
        if src_in - 0.05 <= w["start"] < src_out:
            for i, part in enumerate(clean(w["text"]).split()):
                ws.append({"t": part, "s": round(w["start"] - src_in + i * 0.12, 2)})
    return ws


def cta_words(slug, offset):
    raw = json.load(open(HERE / f"assets/cta-{slug}.words.json"))
    ws, i = [], 0
    while i < len(raw):
        t = raw[i]["text"]
        # spoken "twenty twenty-seven" -> caption "2027"
        if t.lower() == "twenty" and i + 1 < len(raw) and raw[i + 1]["text"].lower().startswith("twenty-seven"):
            t = "2027" + raw[i + 1]["text"][len("twenty-seven"):]
            ws.append({"t": t, "s": round(raw[i]["start"] + offset, 2)})
            i += 2
            continue
        ws.append({"t": t, "s": round(raw[i]["start"] + offset, 2)})
        i += 1
    return ws, raw[-1]["end"]


def mark(text):
    return re.sub(r"(\$[\d,.]+|\b\d[\d,.%]*\b|IRMAA|SSA-44|Part [ABD]\b|channel\.?)", r"<b>\1</b>", html.escape(text))


def build(sh):
    slug = sh["slug"]
    seg = round(sh["src_out"] - sh["src_in"], 2)
    rel = lambda t: round(t - sh["src_in"], 2)
    cta_start = round(seg + 0.15, 2)
    cws, cta_len = cta_words(slug, cta_start)
    total = round(cta_start + cta_len + 1.2, 2)

    caps = chunk(avatar_words(sh["src_in"], sh["src_out"]), seg) + chunk(cws, total - 0.4)
    caps_html = "\n".join(f'<div class="cap" id="c{i}">{mark(t)}</div>' for i, (_, _, t) in enumerate(caps))

    # number pops: each holds until the next one (or the segment end)
    pops = [{"label": l, "old": o, "new": n, "tag": g, "t": rel(t)} for (l, o, n, g, t) in sh["rows"]]
    if sh["stamp"]:
        pops.append({"label": None, "old": None, "new": sh["stamp"][0], "tag": None, "t": rel(sh["stamp"][1]), "alert": True})
    pops.sort(key=lambda p: p["t"])
    for i, p in enumerate(pops):
        p["end"] = pops[i + 1]["t"] if i + 1 < len(pops) else seg
        p["i"] = i
    pops_html = []
    for p in pops:
        lbl = f'<div class="lbl">{html.escape(p["label"])}</div>' if p["label"] else ""
        old = f'<span class="old">{html.escape(p["old"])}</span>' if p["old"] else ""
        tag = f'<span class="tag">{html.escape(p["tag"])}</span>' if p["tag"] else ""
        cls = "pop alert" if p.get("alert") else "pop"
        pops_html.append(f'<div class="{cls}" id="p{p["i"]}">{lbl}<div class="big">{old}<span class="n" id="p{p["i"]}n">{html.escape(p["new"])}</span></div>{tag}</div>')

    freeze = f"freeze-{slug}.jpg"
    fp = HERE / "assets" / freeze
    if not fp.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(sh["src_out"] - 0.1), "-i", str(HERE / "assets/avatar.mp4"),
                        "-frames:v", "1", "-q:v", "3", str(fp)], check=True)

    return TEMPLATE.format(
        slug=slug, total=total, seg=seg, src_in=sh["src_in"], cta_start=cta_start, cta_hold=round(total - cta_start, 2),
        cta_len=round(cta_len, 2), hook=sh["hook"].replace("<br/>", " "), eyebrow=html.escape(sh["eyebrow"]),
        caps=caps_html, caps_js=json.dumps([[a, b] for a, b, _ in caps]), pops="\n".join(pops_html),
        pops_js=json.dumps([{"i": p["i"], "t": p["t"], "end": p["end"], "old": p["old"], "new": p["new"], "tag": bool(p["tag"])} for p in pops]),
        freeze=freeze, tail=round(total - seg, 2), first_pop=pops[0]["t"] if pops else seg,
    )


# Source avatar is 1920x1080; scaled x1.778 to fill the 1920-tall frame, cropped on his face.
AV = 'left: -1167px; top: 0; width: 3413px; height: 1920px'

TEMPLATE = r"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      /* generated by build.py — edit the template there, not this file.
         Text stays inside the Reels/Shorts safe area (x 70–880, y 290–1245). */
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; color: #fff;
        font-family: "Montserrat", "Helvetica Neue", Arial, sans-serif; background: #000; }}
      .clip {{ position: absolute; inset: 0; }}
      #avatar {{ object-fit: cover; }}
      #shade {{ position: absolute; inset: 0; pointer-events: none;
        background: linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 34%, rgba(0,0,0,0.5) 50%, rgba(0,0,0,0.6) 68%, rgba(0,0,0,0.3) 100%); }}
      .stroke {{ text-shadow: 0 0 2px #000, 3px 3px 0 #000, -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 0 6px 18px rgba(0,0,0,0.6); }}

      #hook {{ position: absolute; left: 70px; right: 200px; top: 740px; }}
      #hook .eb {{ font-size: 30px; font-weight: 800; color: #ffd166; letter-spacing: 0.04em; }}
      #hook .tx {{ margin-top: 6px; font-size: 64px; font-weight: 900; line-height: 1.04; }}
      #hook .hot {{ color: #ffd166; }}

      .pop {{ position: absolute; left: 70px; right: 200px; top: 770px; opacity: 0; }}
      .pop .lbl {{ font-size: 34px; font-weight: 800; }}
      .pop .big {{ display: flex; align-items: baseline; gap: 18px; margin-top: 2px; }}
      .pop .n {{ font-size: 112px; font-weight: 900; color: #ffd166; letter-spacing: -0.02em; line-height: 1; }}
      .pop .old {{ font-size: 44px; font-weight: 800; color: rgba(255,255,255,0.75); text-decoration: line-through; text-decoration-thickness: 4px; }}
      .pop .tag {{ display: inline-block; margin-top: 10px; font-size: 34px; font-weight: 900; color: #fff; background: #ef4444;
        padding: 4px 16px; border-radius: 10px; text-shadow: none; }}
      .pop.alert .n {{ font-size: 58px; color: #fff; background: #ef4444; padding: 10px 18px; border-radius: 14px; line-height: 1.1; text-shadow: none; }}

      #caps {{ position: absolute; left: 70px; width: 810px; top: 1040px; height: 200px; }}
      .cap {{ position: absolute; left: 0; right: 0; bottom: 0; text-align: center; opacity: 0;
        font-size: 66px; font-weight: 900; line-height: 1.08; text-transform: uppercase; }}
      .cap b {{ color: #ffd166; font-weight: 900; }}

      #freeze {{ position: absolute; inset: 0; overflow: hidden; }}
      #freeze img {{ position: absolute; {AV}; object-fit: cover; filter: blur(14px) brightness(0.55); }}
      #nudge {{ position: absolute; left: 70px; right: 200px; top: 700px; text-align: center; }}
      #nudge .a {{ font-size: 40px; font-weight: 800; color: #ffd166; }}
      #nudge .b {{ margin-top: 10px; font-size: 72px; font-weight: 900; line-height: 1.04; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="{slug}" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
      <video id="avatar" class="clip" src="assets/avatar.mp4" muted playsinline data-start="0" data-duration="{seg}"
        data-media-start="{src_in}" data-track-index="0" style="{AV}"></video>
      <audio id="voice" src="assets/avatar-voice.m4a" data-start="0" data-duration="{seg}" data-media-start="{src_in}" data-fade-out="0.15" data-track-index="5"></audio>

      <div id="end" class="clip" data-start="{seg}" data-duration="{tail}" data-track-index="1" data-hold>
        <div id="freeze"><img src="assets/{freeze}" alt="" /></div>
        <div id="nudge" class="stroke"><div class="a">Want every 2027 number?</div><div class="b">Full breakdown<br/>on my channel</div></div>
      </div>
      <audio id="cta-vo" src="assets/cta-{slug}.m4a" data-start="{cta_start}" data-duration="{cta_len}" data-track-index="6"></audio>

      <div id="ui" class="clip" data-start="0" data-duration="{total}" data-track-index="2" data-hold>
        <div id="shade" data-layout-ignore></div>
        <div id="hook" class="stroke"><div class="eb">{eyebrow}</div><div class="tx">{hook}</div></div>
        {pops}
        <div id="caps" class="stroke">
{caps}
        </div>
      </div>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      const CAPS = {caps_js}, POPS = {pops_js}, SEG = {seg};
      const parse = (s) => parseFloat(String(s).replace(/[$,]/g, ""));
      const fmt = (v, dec) => "$" + v.toLocaleString("en-US", {{ minimumFractionDigits: dec, maximumFractionDigits: dec }});

      // slow push-in keeps the talking head alive, like a handheld creator video
      tl.fromTo("#avatar", {{ scale: 1 }}, {{ scale: 1.06, duration: SEG, ease: "none", transformOrigin: "50% 30%" }}, 0);

      // hook is on frame 0 (social thumbnail), leaves before the first number
      tl.fromTo("#hook .hot", {{ scale: 1 }}, {{ scale: 1.1, duration: 0.2, yoyo: true, repeat: 1, transformOrigin: "0% 60%" }}, 0.4);
      tl.to("#hook", {{ opacity: 0, y: -20, duration: 0.3 }}, Math.min(4.0, {first_pop} - 0.4));

      CAPS.forEach(([s, e], i) => {{
        tl.fromTo("#c" + i, {{ opacity: 0, scale: 0.8, y: 10 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.12, ease: "back.out(3)" }}, s);
        tl.set("#c" + i, {{ opacity: 0 }}, e);
      }});

      POPS.forEach((p) => {{
        const id = "#p" + p.i, nEl = document.querySelector(id + "n");
        tl.fromTo(id, {{ opacity: 0, scale: 0.6, rotation: -4 }}, {{ opacity: 1, scale: 1, rotation: 0, duration: 0.3, ease: "back.out(2.4)", transformOrigin: "0% 50%" }}, p.t - 0.1);
        if (p.old && /^\$/.test(p.new)) {{
          const a = parse(p.old), b = parse(p.new), dec = /\./.test(p.new) ? 2 : 0, o = {{ v: a }};
          tl.set(nEl, {{ textContent: p.old }}, 0);
          tl.to(o, {{ v: b, duration: 1.0, ease: "steps(10)", onUpdate: () => {{ nEl.textContent = fmt(o.v, dec); }} }}, p.t + 0.25);
        }}
        if (p.tag) tl.fromTo(id + " .tag", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "back.out(3)" }}, p.t + 1.3);
        tl.to(id, {{ opacity: 0, x: -30, duration: 0.2 }}, p.end - 0.2);
      }});

      // soft spoken CTA over a blurred freeze-frame
      tl.fromTo("#end", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25 }}, SEG);
      tl.fromTo("#nudge", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }}, SEG + 0.2);

      window.__timelines["{slug}"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
""".replace("{AV}", AV)

if __name__ == "__main__":
    for sh in SHORTS:
        d = HERE / sh["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(build(sh))
        link = d / "assets"
        if not link.exists():
            link.symlink_to("../assets")
        (d / "hyperframes.json").write_text((HERE / "hyperframes.json").read_text())
        print(sh["slug"], "written")
