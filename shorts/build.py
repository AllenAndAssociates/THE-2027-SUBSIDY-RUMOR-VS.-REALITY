#!/usr/bin/env python3
"""Generate the vertical 9:16 shorts that funnel to the full 2027 Medicare costs video.

Each short = one segment of the HeyGen avatar video + burned-in captions + a stat card
synced to the spoken numbers + a CTA end screen voiced with the ElevenLabs "Arric Allen" clone.

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


def caption_chunks(src_in, src_out):
    """Group words into short caption chunks (<=3 words, break on punctuation or pauses)."""
    ws = []
    for w in WORDS:
        if w["start"] >= src_in - 0.05 and w["start"] < src_out:
            for i, part in enumerate(clean(w["text"]).split()):
                ws.append({"t": part, "s": w["start"] + i * 0.12, "e": w["end"]})
    chunks, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        brk = (len(cur) >= 3 or re.search(r"[.,?!]$", w["t"]) or nxt is None
               or nxt["s"] - w["s"] > 0.9)
        if brk:
            chunks.append(cur)
            cur = []
    out = []
    for i, c in enumerate(chunks):
        start = c[0]["s"] - src_in
        end = (chunks[i + 1][0]["s"] - src_in) if i + 1 < len(chunks) else (src_out - src_in)
        out.append((max(0, start), end, " ".join(x["t"] for x in c)))
    return out


def money_js(v):
    return json.dumps(v)


def build(sh):
    seg = round(sh["src_out"] - sh["src_in"], 2)
    cta_len = dur(HERE / "assets" / sh["cta"])
    cta_start = round(seg, 2)
    total = round(cta_start + cta_len + 1.4, 2)
    rel = lambda t: round(t - sh["src_in"], 2)

    rows_html, rows_js = [], []
    for i, (label, old, new, tag, t) in enumerate(sh["rows"]):
        old_html = f'<span class="old">{html.escape(old)}</span><span class="arr">➔</span>' if old else ""
        tag_html = f'<span class="tag">{html.escape(tag)}</span>' if tag else ""
        rows_html.append(
            f'<div class="row" id="r{i}"><div class="k">{html.escape(label)}</div>'
            f'<div class="v">{old_html}<span class="new" id="r{i}n">{html.escape(new)}</span></div>{tag_html}</div>')
        rows_js.append({"i": i, "t": rel(t), "old": old, "new": new, "tag": bool(tag)})

    caps = caption_chunks(sh["src_in"], sh["src_out"])
    caps_html = "\n".join(
        f'<div class="cap" id="c{i}">' + re.sub(r"(\$[\d,.]+|\b\d[\d,.%]*\b|IRMAA|SSA-44)", r'<b>\1</b>', html.escape(text)) + "</div>"
        for i, (_, _, text) in enumerate(caps))
    caps_js = json.dumps([[s, e] for s, e, _ in caps])

    stamp_html, stamp_js = "", "null"
    if sh["stamp"]:
        stamp_html = f'<div id="stamp">⚠️ {html.escape(sh["stamp"][0])}</div>'
        stamp_js = json.dumps(rel(sh["stamp"][1]))

    return TEMPLATE.format(
        slug=sh["slug"], total=total, cta_hold=round(total - cta_start, 2), seg=seg, src_in=sh["src_in"], cta_start=cta_start,
        cta_len=round(cta_len, 2), cta=sh["cta"], eyebrow=html.escape(sh["eyebrow"]), hook=sh["hook"],
        rows="\n".join(rows_html), rows_js=json.dumps(rows_js), caps=caps_html, caps_js=caps_js,
        stamp=stamp_html, stamp_js=stamp_js, cta_line=html.escape(sh["cta_line"]),
        n_rows=len(sh["rows"]),
    )


TEMPLATE = r"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      /* generated by build.py — edit the template there, not this file */
      :root {{
        --navy: #0b2545; --navy-2: #13315c; --navy-3: #1c3f73; --gold: #f2b84b;
        --blue: #1b75bc; --green: #8dc63f; --emerald: #22b07d; --coral: #ef5b5b;
        --ink: #fff; --ink-dim: #b9c7dc; --card-ink: #0b2545; --card-dim: #5a6b85;
        --font: "Montserrat", "Helvetica Neue", Arial, sans-serif;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: var(--navy); }}
      #root {{
        position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: var(--font); color: var(--ink);
        background:
          radial-gradient(900px 700px at 90% 5%, #1c4a86 0%, rgba(28,74,134,0) 60%),
          radial-gradient(800px 700px at 0% 100%, #0f3a66 0%, rgba(15,58,102,0) 60%),
          linear-gradient(160deg, #0b2545 0%, #0d2b52 60%, #0a2140 100%);
      }}
      .clip {{ position: absolute; inset: 0; }}
      #grid {{ position: absolute; inset: 0; opacity: 0.07;
        background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px);
        background-size: 60px 60px; }}

      /* Safe area = Instagram Reels ∩ YouTube Shorts: text lives in x 70–880, y 290–1245.
         Only decoration (grid, avatar edges, logo strip) sits outside it. */
      #head {{ position: absolute; left: 70px; right: 200px; top: 290px; }}
      #eyebrow {{ font-size: 28px; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; color: var(--gold); }}
      #hook {{ margin-top: 4px; font-size: 48px; font-weight: 900; line-height: 1.05; letter-spacing: -0.01em; }}
      #hook .hot {{ color: var(--gold); display: inline-block; }}

      /* avatar */
      #avatar-panel {{ position: absolute; left: 70px; top: 432px; width: 810px; height: 410px; border-radius: 26px; overflow: hidden;
        background: #000; border: 4px solid rgba(242,184,75,0.9); box-shadow: 0 24px 60px rgba(0,0,0,0.5); }}
      #avatar {{ object-fit: cover; }}
      #caps {{ position: absolute; left: 80px; width: 790px; top: 700px; height: 130px; }}
      .cap {{ position: absolute; left: 10px; right: 10px; bottom: 0; text-align: center; opacity: 0;
        font-size: 50px; font-weight: 900; line-height: 1.08; color: #fff;
        text-shadow: 0 4px 0 #0b2545, 0 0 18px rgba(0,0,0,0.8), 3px 3px 0 #0b2545, -3px -3px 0 #0b2545, 3px -3px 0 #0b2545, -3px 3px 0 #0b2545; }}
      .cap b {{ color: var(--gold); font-weight: 900; }}

      /* stat card */
      #card {{ position: absolute; left: 70px; top: 858px; width: 810px; background: #fff; color: var(--card-ink);
        border-radius: 22px; padding: 6px 22px; box-shadow: 0 24px 60px rgba(0,0,0,0.35); }}
      .row {{ display: flex; align-items: center; gap: 12px; height: 92px; border-top: 2px solid #e6ebf3; }}
      .row:first-child {{ border-top: 0; }}
      .row .k {{ flex: 1; font-size: 28px; font-weight: 700; color: var(--card-dim); line-height: 1.1; }}
      .row .v {{ display: flex; align-items: baseline; gap: 8px; font-size: 40px; font-weight: 900; white-space: nowrap; }}
      .row .old {{ font-size: 28px; font-weight: 700; color: var(--card-dim); text-decoration: line-through; }}
      .row .arr {{ font-size: 28px; color: var(--blue); }}
      .row .tag {{ font-size: 28px; font-weight: 800; color: #fff; background: var(--coral); padding: 4px 12px; border-radius: 999px; }}
      #stamp {{ position: absolute; left: 90px; width: 770px; top: 1158px; padding: 12px 16px; text-align: center;
        border: 5px solid var(--coral); border-radius: 16px; color: var(--coral); background: rgba(11,37,69,0.95);
        font-size: 32px; font-weight: 900; transform: rotate(-2deg); opacity: 0; }}
      #strip {{ position: absolute; left: 0; right: 0; top: 1290px; display: flex; justify-content: center; }}
      #strip .lg {{ background: #fff; border-radius: 14px; padding: 8px 12px; width: 300px; opacity: 0.95; }}
      #strip .lg img {{ width: 100%; display: block; }}

      /* CTA end screen */
      #cta {{ background: linear-gradient(170deg, #0b2545 0%, #13315c 100%); }}
      #cta .eb {{ position: absolute; left: 70px; right: 200px; top: 290px; text-align: center; font-size: 30px; font-weight: 800;
        letter-spacing: 0.16em; color: var(--gold); }}
      #cta .line {{ position: absolute; left: 70px; right: 200px; top: 338px; text-align: center; font-size: 30px; font-weight: 800; color: var(--ink-dim); }}
      #cta .ttl {{ position: absolute; left: 70px; right: 200px; top: 390px; text-align: center; font-size: 52px; font-weight: 900; line-height: 1.05; }}
      #cta .ttl span {{ color: var(--gold); }}
      #thumb {{ position: absolute; left: 115px; top: 520px; width: 720px; height: 405px; border-radius: 22px; overflow: hidden;
        border: 5px solid var(--gold); box-shadow: 0 30px 80px rgba(0,0,0,0.55); }}
      #thumb img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
      #thumb .play {{ position: absolute; left: 50%; top: 50%; width: 130px; height: 130px; margin: -65px 0 0 -65px; border-radius: 50%;
        background: rgba(239,91,91,0.95); display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
      #thumb .play i {{ display: block; width: 0; height: 0; border-left: 46px solid #fff; border-top: 28px solid transparent;
        border-bottom: 28px solid transparent; margin-left: 10px; }}
      #thumb .len {{ position: absolute; left: 14px; bottom: 14px; background: rgba(0,0,0,0.8); padding: 4px 12px; border-radius: 8px;
        font-size: 28px; font-weight: 800; }}
      #chips {{ position: absolute; left: 70px; right: 200px; top: 945px; display: flex; flex-wrap: nowrap; justify-content: center; gap: 10px; }}
      #chips div {{ font-size: 28px; font-weight: 800; padding: 8px 14px; border-radius: 12px; background: rgba(255,255,255,0.1);
        border: 2px solid rgba(242,184,75,0.7); white-space: nowrap; }}
      #tap {{ position: absolute; left: 130px; right: 260px; top: 1018px; height: 100px; border-radius: 999px; background: var(--gold);
        color: var(--navy); display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: 900; }}
      #brand {{ position: absolute; left: 70px; right: 200px; top: 1140px; text-align: center; }}
      #brand .ph {{ font-size: 30px; font-weight: 800; color: var(--ink); line-height: 1.35; }}
      #brand .ph span {{ color: var(--gold); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="{slug}" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
      <div id="bg" class="clip" data-start="0" data-duration="{total}" data-track-index="0" data-hold><div id="grid"></div></div>

      <!-- avatar + its loudness-normalized voice, trimmed to this short's segment -->
      <div id="avatar-panel"><video id="avatar" class="clip" src="assets/avatar.mp4" muted playsinline data-start="0" data-duration="{seg}"
        data-media-start="{src_in}" data-track-index="1" style="left: -195px; top: -8px; width: 1190px; height: 670px"></video></div>
      <audio id="voice" src="assets/avatar-voice.m4a" data-start="0" data-duration="{seg}" data-media-start="{src_in}" data-fade-out="0.2" data-track-index="5"></audio>

      <div id="main" class="clip" data-start="0" data-duration="{cta_start}" data-track-index="2" data-hold>
        <div id="head"><div id="eyebrow">{eyebrow}</div><div id="hook">{hook}</div></div>
        <div id="caps">
{caps}
        </div>
        <div id="card">
{rows}
        </div>
        {stamp}
      </div>
      <div id="strip" data-layout-allow-safe-zone><div class="lg"><img src="assets/allen-associates-logo.png" alt="Allen &amp; Associates" /></div></div>

      <div id="cta" class="clip" data-start="{cta_start}" data-duration="{cta_hold}" data-track-index="3" data-hold>
        <div class="eb">▶ WATCH THE FULL VIDEO</div>
        <div class="line">{cta_line}</div>
        <div class="ttl">Official <span>2027</span> Medicare<br/>Premiums &amp; Deductibles</div>
        <div id="thumb"><img src="assets/full-video-thumb.jpg" alt="Full video thumbnail" /><div class="play"><i></i></div><div class="len">4:48</div></div>
        <div id="chips"><div>Part B</div><div>Medigap</div><div>IRMAA</div><div>Part A</div><div>Part D</div></div>
        <div id="tap">Tap the link to watch ▶</div>
        <div id="brand"><div class="ph"><span>800-324-9986</span><br/>allenandassociates.agency</div></div>
      </div>
      <audio id="cta-vo" src="assets/{cta}" data-start="{cta_start}" data-duration="{cta_len}" data-track-index="6"></audio>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      const ROWS = {rows_js};
      const CAPS = {caps_js};
      const STAMP = {stamp_js};
      const parse = (s) => parseFloat(String(s).replace(/[$,]/g, ""));
      const fmt = (v, dec) => "$" + v.toLocaleString("en-US", {{ minimumFractionDigits: dec, maximumFractionDigits: dec }});

      tl.fromTo("#grid", {{ backgroundPosition: "0px 0px" }}, {{ backgroundPosition: "0px 600px", duration: {total}, ease: "none" }}, 0);

      // open
      // frame 0 is the thumbnail on social players: title, avatar and card are on screen from the first frame
      tl.fromTo("#hook .hot", {{ scale: 1 }}, {{ scale: 1.08, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.out", transformOrigin: "0% 50%" }}, 0.3);

      // captions: one chunk at a time
      CAPS.forEach(([s, e], i) => {{
        tl.fromTo("#c" + i, {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.12, ease: "back.out(2.5)" }}, s);
        tl.set("#c" + i, {{ opacity: 0 }}, e);
      }});

      // stat rows: dim until spoken, then reveal / count
      ROWS.forEach((r) => {{
        const row = "#r" + r.i, nEl = document.querySelector("#r" + r.i + "n");
        tl.set(row + " .v, " + row + " .tag", {{ opacity: 0 }}, 0);
        tl.set(row + " .k", {{ opacity: 0.45 }}, 0);
        tl.to(row + " .k", {{ opacity: 1, duration: 0.2 }}, r.t - 0.2);
        tl.fromTo(row + " .v", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2.2)", transformOrigin: "100% 50%" }}, r.t);
        if (r.old && /^\$/.test(r.new)) {{
          const a = parse(r.old), b = parse(r.new), dec = /\./.test(r.new) ? 2 : 0, o = {{ v: a }};
          tl.set(nEl, {{ textContent: r.old }}, 0);
          tl.to(o, {{ v: b, duration: 1.2, ease: "steps(12)", onUpdate: () => {{ nEl.textContent = fmt(o.v, dec); }} }}, r.t + 0.3);
        }}
        if (r.tag) tl.fromTo(row + " .tag", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(3)" }}, r.t + 1.5);
        tl.fromTo(row, {{ backgroundColor: "rgba(242,184,75,0.35)" }}, {{ backgroundColor: "rgba(242,184,75,0)", duration: 1.6, immediateRender: false }}, r.t);
      }});
      if (STAMP !== null) {{
        tl.fromTo("#stamp", {{ opacity: 0, scale: 2.4, rotation: -10 }}, {{ opacity: 1, scale: 1, rotation: -4, duration: 0.28, ease: "power4.in" }}, STAMP);
        tl.fromTo("#card", {{ x: 0 }}, {{ x: 10, duration: 0.05, yoyo: true, repeat: 5, ease: "none" }}, STAMP + 0.28);
      }}

      // CTA
      const C = {cta_start};
      tl.fromTo("#cta", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.out" }}, C);
      tl.fromTo("#cta .eb", {{ y: -30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "power3.out" }}, C + 0.2);
      tl.fromTo("#cta .line", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, C + 0.3);
      tl.fromTo("#cta .ttl", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "power3.out" }}, C + 0.4);
      tl.fromTo("#thumb", {{ scale: 0.8, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.6, ease: "back.out(1.6)" }}, C + 0.6);
      tl.fromTo("#thumb .play", {{ scale: 1 }}, {{ scale: 1.12, duration: 0.5, yoyo: true, repeat: 7, ease: "sine.inOut" }}, C + 1.2);
      tl.fromTo("#chips div", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, stagger: 0.15, ease: "back.out(2)" }}, C + 1.2);
      tl.fromTo("#tap", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "back.out(2)" }}, C + 2.0);
      tl.fromTo("#tap", {{ scale: 1 }}, {{ scale: 1.05, duration: 0.45, yoyo: true, repeat: 9, ease: "sine.inOut" }}, C + 2.6);
      tl.fromTo("#brand", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, C + 2.4);
      tl.to("#strip", {{ y: 0 }}, C); // strip stays on the end screen too

      window.__timelines["{slug}"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    for sh in SHORTS:
        d = HERE / sh["slug"]          # one HyperFrames project per short
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(build(sh))
        link = d / "assets"
        if not link.exists():
            link.symlink_to("../assets")
        (d / "hyperframes.json").write_text((HERE / "hyperframes.json").read_text())
        print(sh["slug"], "written")
