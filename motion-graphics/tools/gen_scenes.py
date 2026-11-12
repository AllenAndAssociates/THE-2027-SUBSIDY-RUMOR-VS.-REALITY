#!/usr/bin/env python3
"""Generates compositions/shotNN.html (Shots 1-33), the full index.html and the chapter tabs.

Shots 34-37 (checklist + contact card) are hand-authored in compositions/checklist.html and
contact.html and are mounted at the global time 248.6 s.

Every graphic is anchored to a spoken word ("w:word" = first word starting with `word`,
"w:word#2" = second occurrence) using transcript.json, so the picture lands on the word.
Visual language follows the USAFacts explainer look: pale-grey data stage, hot pink / cobalt /
deep teal shapes, pale-yellow highlighter label chips, heavy black-outlined caps for headlines,
round icon badges and people pictograms.

Run:  python3 tools/gen_scenes.py        (from the motion-graphics folder)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLIP0 = 248.6            # global time where Shot 34 (checklist/contact scenes) starts
TOTAL = 279.44           # 278.24 s of footage + 1.2 s hold

INK, TEAL, DTEAL, PINK, BLUE, PURP, YEL = "#0B1F3A", "#4F9B22", "#2F6A12", "#D4AF37", "#0484C5", "#1B3F7A", "#F6E4A6"   # PINK is now brand GOLD
# USAFacts-style full-bleed stages, in Allen & Associates brand colours (names kept from the first draft:
# BG_PINK = deep navy, BG_BLUE/BG_SKY = logo blue, BG_GREEN = logo green, BG_NAVY = navy, BG_YEL = light gold)
BG_PINK, BG_BLUE, BG_SKY, BG_GREEN, BG_NAVY, BG_YEL, BG_GRAY = "#10294B", "#0872B3", "#0484C5", "#4A8F1F", "#0B1F3A", "#F1D27A", "#3A4D68"
GRAYT, LGRAY, WHITE, BLACK = "#5B6B82", "#C3CCCC", "#FFFFFF", "#071428"

ICON = {
    "dollar": "M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z",
    "lock": "M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z",
    "calendar": "M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z",
    "bank": "M4 10v7h3v-7H4zm6 0v7h3v-7h-3zM2 22h19v-3H2v3zm14-12v7h3v-7h-3zm-4.5-9L2 6v2h19V6l-9.5-5z",
    "warn": "M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z",
    "check": "M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z",
    "close": "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
    "doc": "M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z",
    "mail": "M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
    "search": "M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
    "phone": "M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z",
    "clock": "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z",
    "up": "M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z",
    "person": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
    "shield": "M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z",
    "chat": "M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z",
    "pin": "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
    "building": "M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z",
    "pill": "M4.22 11.29l7.07-7.07a5 5 0 0 1 7.07 7.07l-7.07 7.07a5 5 0 0 1-7.07-7.07zm1.41 1.41a3 3 0 0 0 4.24 4.24l2.83-2.83-4.24-4.24-2.83 2.83z",
    "help": "M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z",
    "list": "M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z",
    "laptop": "M20 18c1.1 0 1.99-.9 1.99-2L22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z",
    "heart": "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
}

SFX = {  # name -> (file, duration, volume)
    "pop": ("pop_a.mp3", 0.48, 0.22), "pop2": ("pop_b.mp3", 0.48, 0.22),
    "whoosh": ("whoosh_a.mp3", 0.8, 0.26), "whoosh2": ("whoosh_b.mp3", 0.8, 0.26),
    "lock": ("lock_click.mp3", 0.6, 0.35), "stamp": ("stamp_thud.mp3", 0.6, 0.35),
    "ding": ("ding_a.mp3", 0.8, 0.30), "tick": ("tick_a.mp3", 0.48, 1.0),
}

# ------------------------------------------------------------------ transcript / shot timing
words = [w for w in json.load(open(os.path.join(ROOT, "transcript.json")))["words"] if w["type"] == "word"]
sents, cur = [], []
for w in words:
    cur.append(w)
    if w["text"][-1] in ".?!":
        sents.append(cur); cur = []
GROUPS = [(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8),(9,10),(11,11),(12,12),(13,13),(14,15),(16,16),
          (17,17),(18,18),(19,19),(20,20),(21,22),(23,23),(24,24),(25,25),(26,26),(27,27),(28,28),(29,29),
          (30,30),(31,31),(32,32),(33,33),(34,35),(36,36),(37,37)]
assert len(GROUPS) == 33 and len(sents) == 41
starts = [max(0.0, sents[a - 1][0]["start"] - 0.25) for a, b in GROUPS]
starts[0] = 0.0
ends = starts[1:] + [CLIP0]
CHAPTER_START = {1: 0.0, 2: starts[3], 3: starts[10], 4: starts[13], 5: starts[18], 6: CLIP0 + 0.18, 7: CLIP0 + 19.94}


# layout: F = full-bleed graphic (no presenter) | B = full-bleed graphic + presenter in a ring-bordered circle
#         HR / HL = presenter large on the white talk backdrop (right / left), graphic on the other side
# (n: (layout, background, default text colour, header (title, subtitle, icon) or None))
LAYOUT = {
    1: ("F", BG_PINK, "#fff", None), 2: ("HR", "#fff", INK, None), 3: ("HL", "#fff", INK, None),
    4: ("B", BG_BLUE, "#fff", ("Part D funding", "Who pays whom", "bank")),
    5: ("B", BG_NAVY, "#fff", ("Federal subsidies", "The past two years", "dollar")),
    6: ("B", BG_GREEN, "#fff", ("Monthly premium", "With vs. without subsidy", "dollar")),
    7: ("F", BG_PINK, "#fff", None), 8: ("HR", "#fff", INK, None), 9: ("F", BG_YEL, INK, None), 10: ("HR", "#fff", INK, None),
    11: ("B", BG_NAVY, "#fff", ("Locked in by law", "2027 rules", "lock")),
    12: ("F", BG_GREEN, "#fff", None),
    13: ("B", BG_SKY, "#fff", ("Deductible", "Regulated by law", "lock")),
    14: ("HR", "#fff", INK, None),
    15: ("B", BG_PINK, "#fff", ("Premium forecast", "Part D enrollees", "up")),
    16: ("F", BG_BLUE, "#fff", None),
    17: ("B", BG_GREEN, "#fff", ("Formulary", "List of covered drugs", "list")),
    18: ("B", BG_GREEN, "#fff", ("Formulary", "List of covered drugs", "list")),
    19: ("HL", "#fff", INK, None),
    20: ("B", BG_NAVY, "#fff", ("Plan year", "January 1 start", "calendar")),
    21: ("B", BG_NAVY, "#fff", ("Mid-year changes", "Covered drug list", "list")),
    22: ("F", BG_PINK, "#fff", None),
    23: ("B", BG_YEL, INK, ("Appeals", "Exception request", "doc")),
    24: ("B", BG_SKY, "#fff", ("Open enrollment", "Oct 15 – Dec 7", "calendar")),
    25: ("B", BG_GRAY, "#fff", ("Medicare.gov", "Plan finder", "search")),
    26: ("F", BG_PINK, "#fff", None),
    27: ("B", BG_GREEN, "#fff", ("Plan finder", "Enter every medication", "pill")),
    28: ("B", BG_BLUE, "#fff", ("Annual cost", "$0 plan vs. $40 plan", "dollar")),
    29: ("HR", "#fff", INK, None), 30: ("F", BG_NAVY, "#fff", None), 31: ("HL", "#fff", INK, None),
    32: ("B", BG_PINK, "#fff", ("Danger 1", "No out-of-pocket cap", "shield")),
    33: ("B", BG_NAVY, "#fff", ("Danger 2", "Late enrollment penalty", "clock")),
}
STAGE_XY = {"F": (398, 150), "B": (398, 150), "HR": (40, 150), "HL": (756, 150)}
HERO_CX = {"HR": 1470, "HL": 430}
BUBBLE = (1550, 690, 320)     # x, y, outer diameter (ring included)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def contrast_fg(bg):
    """navy on light fills (gold, pale gold, white), white on dark/saturated fills"""
    h = bg.lstrip("#")
    if len(h) != 6:
        return WHITE
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return INK if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else WHITE


class Shot:
    def __init__(self, n):
        self.n, self.start, self.end = n, starts[n - 1], ends[n - 1]
        self.html, self.js, self.sfx, self.k = [], [], [], 0
        self.page = []
        self.layout, self.bg, self.fg, self.header = LAYOUT[n]
        self.missing = []

    # ---- timing
    def T(self, a):
        if isinstance(a, (int, float)):
            return float(a)
        m = re.match(r"w:([^#]+)(?:#(\d+))?$", a)
        q, occ = norm(m.group(1)), int(m.group(2) or 1)
        hits = [w for w in words if self.start - 0.4 <= w["start"] <= self.end + 0.4 and norm(w["text"]).startswith(q)]
        if len(hits) < occ:
            self.missing.append(a); return 0.6
        return max(0.05, hits[occ - 1]["start"] - self.start - 0.05)

    def nid(self):
        self.k += 1
        return "s%02de%d" % (self.n, self.k)

    def tin(self, i, t, anim="pop", dur=0.5, sfx=None, rot=0):
        t = self.T(t)
        sel = "#" + i
        if anim == "pop":
            f, to = "{opacity:0,y:28,scale:.9,rotation:%s}" % rot, "{opacity:1,y:0,scale:1,rotation:%s,duration:%s,ease:'back.out(1.5)'}" % (rot, dur)
        elif anim == "fade":
            f, to = "{opacity:0,rotation:%s}" % rot, "{opacity:1,rotation:%s,duration:%s,ease:'power2.out'}" % (rot, dur)
        elif anim == "wipe":
            f, to = "{clipPath:'inset(0 100% 0 0)'}", "{clipPath:'inset(0 0%% 0 0)',duration:%s,ease:'power2.out'}" % dur
        elif anim == "left":
            f, to = "{opacity:0,x:-80}", "{opacity:1,x:0,duration:%s,ease:'power3.out'}" % dur
        elif anim == "right":
            f, to = "{opacity:0,x:80}", "{opacity:1,x:0,duration:%s,ease:'power3.out'}" % dur
        elif anim == "up":
            f, to = "{opacity:0,y:60}", "{opacity:1,y:0,duration:%s,ease:'power3.out'}" % dur
        elif anim == "zoom":
            f, to = "{opacity:0,scale:.3}", "{opacity:1,scale:1,duration:%s,ease:'back.out(2)'}" % dur
        elif anim == "stamp":
            f = "{opacity:0,scale:2.6,rotation:%s}" % (rot - 12)
            to = "{opacity:1,scale:1,rotation:%s,duration:.28,ease:'power4.in'}" % rot
        elif anim == "growx":
            f, to = "{scaleX:0,transformOrigin:'0% 50%'}", "{scaleX:1,duration:%s,ease:'power2.out'}" % dur
        elif anim == "growy":
            f, to = "{scaleY:0,transformOrigin:'50% 100%'}", "{scaleY:1,duration:%s,ease:'power2.out'}" % dur
        elif anim == "growyb":
            f, to = "{scaleY:0,transformOrigin:'50% 100%'}", "{scaleY:1,duration:%s,ease:'back.out(1.7)'}" % dur
        elif anim == "draw":
            f, to = "{strokeDashoffset:1}", "{strokeDashoffset:0,duration:%s,ease:'power2.inOut'}" % dur
        else:
            raise ValueError(anim)
        self.js.append("tl.fromTo('%s',%s,%s,%.3f);" % (sel, f, to, t))
        if sfx:
            self.sfx.append((self.start + t, sfx))

    def add(self, html, t, anim="pop", dur=0.5, sfx=None, rot=0, page=False):
        i = self.nid()
        (self.page if page else self.html).append(html.replace("@ID", i))
        self.tin(i, t, anim, dur, sfx, rot)
        return i

    # ---- primitives (stage-local coordinates, stage = 1124 x 890)
    def chip(self, text, x, y, t, bg=YEL, fg=INK, size=40, anim="wipe", sfx=None, weight=700, radius=8, pad="8px 18px", w=None):
        ww = "width:%dpx;" % w if w else "white-space:nowrap;"
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;%sbackground:%s;color:%s;font-size:%dpx;font-weight:%d;border-radius:%dpx;padding:%s;line-height:1.15">%s</div>' % (x, y, ww, bg, fg, size, weight, radius, pad, text), t, anim, 0.28 if anim == "wipe" else 0.5, sfx)

    def dark(self, text, x, y, t, size=40, **k):
        """formerly a black caption pill; now plain bold text so nothing pops in/out of the lower third"""
        return self.txt(text, x, y, t, size=size, weight=900, anim="fade")

    def ttl(self, text, x, y, t, size=72, color=None, w=None, outline=False, align="left", anim="pop", sfx=None, upper=True, rot=0):
        color = color or self.fg
        st = "font-family:'Montserrat',sans-serif;font-weight:900;line-height:1.02;font-size:%dpx;color:%s;text-align:%s;" % (size, color, align)
        if upper:
            st += "text-transform:uppercase;"
        if outline:
            st += "-webkit-text-stroke:%dpx #000;paint-order:stroke fill;" % max(8, size // 7)
        st += ("width:%dpx;" % w) if w else "white-space:nowrap;"
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;%s">%s</div>' % (x, y, st, text), t, anim, 0.5, sfx, rot)

    def txt(self, text, x, y, t, size=38, color=None, w=None, weight=700, align="left", anim="fade", sfx=None):
        st = "font-size:%dpx;color:%s;font-weight:%d;text-align:%s;line-height:1.2;" % (size, color or self.fg, weight, align)
        st += ("width:%dpx;" % w) if w else "white-space:nowrap;"
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;%s">%s</div>' % (x, y, st, text), t, anim, 0.45, sfx)

    def badge(self, icon, x, y, d, t, bg=BLUE, fg=None, anim="zoom", sfx=None):
        s = int(d * 0.58)
        fg = fg or contrast_fg(bg)
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:50%%;background:%s"><svg viewBox="0 0 24 24" style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx"><path fill="%s" d="%s"/></svg></div>' % (x, y, d, d, bg, (d - s) // 2, (d - s) // 2, s, s, fg, ICON[icon]), t, anim, 0.5, sfx)

    def num(self, text, x, y, d, t, bg=PINK, fg=None, anim="zoom", sfx=None):
        fg = fg or contrast_fg(bg)
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:50%%;background:%s;color:%s;font-family:\'Montserrat\',sans-serif;font-weight:900;font-size:%dpx;line-height:%dpx;text-align:center">%s</div>' % (x, y, d, d, bg, fg, int(d * 0.58), d, text), t, anim, 0.5, sfx)

    def card(self, x, y, w, h, t, bg=WHITE, radius=26, anim="pop", border=None, rot=0, sfx=None):
        b = "border:%s;" % border if border else ""
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:%s;border-radius:%dpx;box-shadow:0 14px 34px rgba(27,31,75,.16);%s"></div>' % (x, y, w, h, bg, radius, b), t, anim, 0.5, sfx, rot)

    def stat(self, text, x, y, t, size=200, color=None, w=None, align="left", anim="zoom", sfx=None):
        return self.ttl(text, x, y, t, size=size, color=color or self.fg, w=w, align=align, anim=anim, sfx=sfx, upper=False)

    def bar(self, x, y, w, h, t, color=TEAL, anim="growx", radius=14, dur=0.7, sfx=None):
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:%s;border-radius:%dpx"></div>' % (x, y, w, h, color, radius), t, anim, dur, sfx)

    def stamp(self, text, x, y, t, color=PINK, size=84, rot=-8, sfx="stamp", bg="rgba(255,255,255,.92)"):
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;white-space:nowrap;border:10px solid %s;color:%s;background:%s;border-radius:18px;padding:6px 30px;font-family:\'Montserrat\',sans-serif;font-weight:900;font-size:%dpx;line-height:1.1">%s</div>' % (x, y, color, INK, bg, size, text), t, "stamp", 0.3, sfx, rot)

    def arrow(self, x1, y1, x2, y2, t, color=INK, wd=10, dur=0.6, head=True):
        i = self.nid()
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        hx = lambda a: x2 - 34 * math.cos(ang + a)
        hy = lambda a: y2 - 34 * math.sin(ang + a)
        d = "M%d %d L%d %d" % (x1, y1, x2, y2)
        if head:
            d += " M%d %d L%d %d L%d %d" % (hx(.5), hy(.5), x2, y2, hx(-.5), hy(-.5))
        self.html.append('<svg id="%s" class="e" style="left:0;top:0;width:1124px;height:890px;overflow:visible"><path d="%s" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" fill="none" stroke="%s" stroke-width="%d" stroke-linecap="round" stroke-linejoin="round"/></svg>' % (i, d, color, wd))
        self.js.append("tl.fromTo('#%s path',{strokeDashoffset:1},{strokeDashoffset:0,duration:%s,ease:'power2.inOut'},%.3f);" % (i, dur, self.T(t)))
        return i

    def pill(self, x, y, t, rot=-35, ln=170, th=64, c1=PINK, c2=WHITE, anim="pop", sfx=None):
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:%dpx;background:linear-gradient(90deg,%s 50%%,%s 50%%);border:5px solid %s;box-shadow:0 8px 18px rgba(27,31,75,.18)"></div>' % (x, y, ln, th, th // 2, c1, c2, c1), t, anim, 0.5, sfx, rot)

    def cal(self, top, big, x, y, t, w=230, band=PINK, anim="pop", sfx=None):
        h = int(w * 1.0)
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:#fff;border-radius:22px;box-shadow:0 14px 34px rgba(27,31,75,.18);overflow:hidden"><div style="height:%dpx;background:%s;color:#fff;font-weight:900;font-size:%dpx;text-align:center;line-height:%dpx;letter-spacing:.08em">%s</div><div style="font-family:\'Montserrat\',sans-serif;font-weight:900;font-size:%dpx;color:%s;text-align:center;line-height:%dpx">%s</div></div>' % (x, y, w, h, int(h * .3), band, int(w * .17), int(h * .3), top, int(w * .42), INK, int(h * .68), big), t, anim, 0.5, sfx)

    def people(self, x, y, cols, rows, hl, t, size=64, gap=22, c1=PINK, c2=LGRAY, hl_t=None):
        i = self.nid()
        cells = []
        for r in range(rows):
            for c in range(cols):
                n = r * cols + c
                cells.append('<svg class="p" viewBox="0 0 24 24" style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx"><path fill="%s" d="%s"/></svg>' % (c * (size + gap), r * (size + gap), size, size, c1 if n < hl else c2, ICON["person"]))
        self.html.append('<div id="%s" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</div>' % (i, x, y, cols * (size + gap), rows * (size + gap), "".join(cells)))
        self.js.append("tl.fromTo('#%s .p',{opacity:0,scale:.4},{opacity:1,scale:1,duration:.3,ease:'back.out(2)',stagger:.012},%.3f);" % (i, self.T(t)))
        if hl_t is not None:
            self.js.append("tl.to('#%s .p path',{fill:'%s',duration:.01,stagger:.0,overwrite:false},%.3f);" % (i, c2, self.T(hl_t) - 0.01))
            self.js.append("for (let q=0;q<%d;q++) tl.to(document.querySelectorAll('#%s .p path')[q],{fill:'%s',duration:.2},%.3f+q*.03);" % (hl, i, c1, self.T(hl_t)))
        return i

    def drug(self, label, x, y, w, t, ok=True, anim="left"):
        return self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:84px;background:#fff;border-radius:18px;box-shadow:0 8px 20px rgba(27,31,75,.12);font-size:34px;font-weight:700;color:%s;line-height:84px;padding-left:92px"><svg viewBox="0 0 24 24" style="position:absolute;left:22px;top:20px;width:44px;height:44px"><path fill="%s" d="%s"/></svg>%s</div>' % (x, y, w, INK, TEAL if ok else PINK, ICON["pill"], label), t, anim, 0.4)

    def decorate(self):
        """Header (title + icon + subtitle chip) and presenter ring, at page coordinates."""
        if self.header:
            title, sub, icon = self.header
            self.badge(icon, 60, 46, 64, 0.15, bg="#fff", fg=INK, page=True) if False else None
            self.add('<div id="@ID" class="e" style="left:60px;top:46px;width:68px;height:68px;border-radius:16px;background:#fff"><svg viewBox="0 0 24 24" style="position:absolute;left:12px;top:12px;width:44px;height:44px"><path fill="%s" d="%s"/></svg></div>' % (INK, ICON[icon]), 0.15, "zoom", 0.4, page=True)
            self.add('<div id="@ID" class="e" style="left:150px;top:42px;white-space:nowrap;font-size:48px;font-weight:400;color:%s;letter-spacing:-.01em">%s</div>' % (self.fg, title), 0.2, "left", 0.3, page=True)
            self.add('<div id="@ID" class="e" style="left:150px;top:104px;white-space:nowrap;background:%s;color:%s;font-size:22px;font-weight:900;padding:5px 14px;border-radius:5px">%s</div>' % (PINK, INK, sub), 0.3, "wipe", 0.28, page=True)
        if self.layout in ("HR", "HL"):
            cx = HERO_CX[self.layout]
            self.add('<div id="@ID" class="e" style="left:%dpx;top:40px;width:960px;height:1040px;background:radial-gradient(ellipse 50%% 56%% at 50%% 54%%,rgba(11,31,58,.11),rgba(11,31,58,0) 72%%)"></div>' % (cx - 480), 0.0, "fade", 0.6, page=True)
        if self.layout == "B":
            x, y, d = BUBBLE
            ring = INK if self.bg == BG_YEL else PINK
            self.add('<div id="@ID" class="e" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:50%%;background:#0a0a0a;border:10px solid %s;box-shadow:0 16px 40px rgba(0,0,0,.5),0 2px 8px rgba(0,0,0,.35)"></div>' % (x, y, d, d, ring), 0.3, "zoom", 0.5, page=True)

    # ---- output
    def render(self):
        self.decorate()
        n = self.n
        css = open(os.path.join(HERE, "common.css")).read()
        body = "\n    ".join(self.html)
        page = "\n    ".join(self.page)
        sx, sy = STAGE_XY[self.layout]
        js = "\n    ".join(self.js)
        dur = self.end - self.start
        return """<template>
  <style>
%s
  </style>
  <div id="root" data-composition-id="shot%02d" data-width="1920" data-height="1080">
    <div id="s%02d-bg" class="bgf" style="background:%s"></div>
    <div id="s%02d-pg" class="pg">
    %s
    </div>
    <div id="s%02d-st" class="st" style="left:%dpx;top:%dpx">
    %s
    </div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    tl.fromTo('#s%02d-bg', { opacity: 0 }, { opacity: 1, duration: 0.25, ease: 'power2.out' }, 0);
    tl.fromTo('#s%02d-st', { scale: 1 }, { scale: 1.03, duration: %.3f, ease: 'none' }, 0);
    %s
    tl.to(['#s%02d-st', '#s%02d-pg'], { opacity: 0, duration: 0.22, ease: 'power2.in' }, %.3f);
    window.__timelines['shot%02d'] = tl;
  </script>
</template>
""" % (css, n, n, self.bg, n, page, n, sx, sy, body, n, n, dur, js, n, n, dur - 0.26, n)


# ================================================================== SHOT SPECS
def build(n):
    s = Shot(n)
    C = s.chip
    if n == 1:   # the rumor headlines
        s.card(60, 90, 1000, 250, "w:headlines", rot=-2, sfx="pop")
        s.badge("warn", 90, 150, 130, "w:headlines", bg=BG_PINK)
        s.ttl("Medicare Part D<br>is ending in 2027?!", 250, 124, "w:headlines", size=58, color=BLACK, rot=-2)
        s.card(110, 400, 920, 190, "w:prices", rot=1.5, sfx="pop2")
        s.badge("up", 140, 440, 110, "w:prices", bg=PINK)
        s.ttl("Prices are<br>exploding!", 280, 424, "w:prices", size=58, color=BLACK, rot=1.5)
        s.dark("Rumor… or fact?", 130, 690, "w:exploding#1", size=64, anim="pop")
    elif n == 2:  # rumors vs facts
        s.card(30, 60, 510, 740, 0.4, bg=PINK, radius=28)
        s.card(584, 60, 510, 740, "w:facts", bg=TEAL, radius=28)
        s.ttl("Rumors", 70, 100, "w:rumors", size=84, color=WHITE, outline=True, sfx="pop")
        s.badge("chat", 215, 280, 200, "w:media", bg=WHITE, fg=PINK)
        s.txt("Social media<br>rumors", 70, 540, "w:social", size=48, color=WHITE, w=430, align="center")
        s.ttl("Facts", 624, 100, "w:facts", size=84, color=WHITE, outline=True, sfx="pop2")
        s.badge("check", 769, 280, 200, "w:actual", bg=WHITE, fg=TEAL)
        s.txt("Actual<br>facts", 624, 540, "w:actual", size=48, color=WHITE, w=430, align="center")
        s.chip("Protect your wallet", 120, 830, "w:wallet", size=40, sfx="pop")
        s.chip("and prescriptions", 600, 830, "w:prescriptions", size=40, sfx="pop2")
    elif n == 3:  # intro
        s.card(60, 70, 1000, 330, "w:Allen", anim="pop", sfx="whoosh")
        s.add('<img id="@ID" class="e" src="assets/logo.jpg" alt="Allen &amp; Associates" style="left:110px;top:100px;width:900px;height:282px;object-fit:contain">', "w:Allen", "fade")
        s.chip("Plain-English Medicare facts", 60, 470, "w:plain", size=48)
        s.stat("Since 1994", 60, 580, "w:since", size=150, color=BLUE, sfx="pop")
    elif n == 4:  # how funded
        s.chip("How Part D is funded", 60, 40, 0.3, size=48)
        s.badge("bank", 100, 280, 230, 0.4, bg="#fff", fg=INK, sfx="pop")
        s.badge("building", 447, 280, 230, "w:Part", bg=YEL, fg=INK, sfx="pop2")
        s.badge("person", 794, 280, 230, "w:recently", bg=PINK, sfx="pop")
        s.arrow(350, 395, 430, 395, "w:Part", dur=0.4, color="#fff")
        s.arrow(697, 395, 777, 395, "w:recently", dur=0.4, color="#fff")
        s.txt("Federal<br>government", 100, 540, "w:look", size=42, w=230, align="center")
        s.txt("Part D<br>insurers", 447, 540, "w:Part", size=42, w=230, align="center")
        s.txt("You", 794, 540, "w:recently", size=42, w=230, align="center")
    elif n == 5:  # subsidies flow
        s.chip("Special federal subsidies", 60, 40, "w:special", size=48)
        s.badge("bank", 100, 250, 260, "w:federal", bg="#fff", fg=INK, sfx="pop")
        s.badge("building", 764, 250, 260, "w:billion", bg=PINK, sfx="pop2")
        s.arrow(380, 380, 744, 380, "w:paid", dur=0.8, wd=12, color="#fff")
        for k, dt in enumerate((0.0, 0.5, 1.0)):
            i = s.badge("dollar", 392, 320, 120, "w:paid", bg=YEL, fg=INK, anim="fade")
            s.js.append("tl.fromTo('#%s',{x:0},{x:%d,duration:1.4,ease:'none'},%.3f);" % (i, 230, s.T("w:paid") + 0.15 + dt))
            s.js.append("tl.to('#%s',{opacity:0,duration:.25},%.3f);" % (i, s.T("w:paid") + 1.35 + dt))
        s.txt("Federal government", 40, 540, "w:federal", size=44, w=340, align="center")
        s.txt("Billion-dollar<br>Part D insurers", 724, 540, "w:billion", size=44, w=340, align="center")
        s.dark("The past two years", 60, 740, "w:past", size=44)
    elif n == 6:  # premiums kept low
        s.chip("Monthly Part D premium", 60, 40, 0.3, size=48)
        s.bar(220, 330, 280, 430, "w:premiums", color="rgba(255,255,255,.35)", anim="growy")
        s.bar(220, 560, 280, 200, "w:premiums", color="#fff", anim="growy")
        s.bar(220, 330, 280, 230, "w:subsidies", color=YEL, anim="growy")
        s.txt("What you pay", 520, 640, "w:premiums", size=44, w=420)
        s.txt("Taxpayer subsidy", 520, 410, "w:taxpayer", size=44, w=420)
        s.dark("Kept artificially low", 520, 130, "w:artificially", size=52, sfx="pop")
        s.txt("while new program rules rolled out", 520, 215, "w:rolled", size=36, w=520, weight=400)
    elif n == 7:  # profits up, subsidy ended
        s.stat("15–17%", 40, 90, "w:fifteen", size=230, color=YEL, sfx="pop")
        s.add('<div id="@ID" class="e" style="left:520px;top:340px"></div>', 0.1, "fade")
        s.chip("Insurer profits climbed", 60, 360, "w:profits", size=54)
        s.badge("up", 880, 150, 170, "w:climb", bg="#fff", fg=BG_PINK)
        s.badge("dollar", 60, 520, 240, "w:decided", bg=PINK)
        s.txt("Extra insurer<br>subsidy", 330, 570, "w:decided", size=56, w=500)
        s.stamp("Ended", 600, 670, "w:end", color=BG_PINK, size=100, rot=-7)
    elif n == 8:  # stand on own economics
        s.badge("building", 120, 360, 300, "w:Federal", bg=PURP, sfx="pop")
        for k, xx in enumerate((470, 650, 830)):
            i = s.badge("dollar", xx, 120 + 60 * (k % 2), 130, "w:officials", bg=YEL, fg=INK)
            s.js.append("tl.to('#%s',{y:380,opacity:0,duration:.6,ease:'power2.in'},%.3f);" % (i, s.T("w:stand") + 0.12 * k))
        s.chip("Plans must stand on their own economics", 60, 40, "w:stand", size=46, sfx="pop")
        s.txt("No more extra subsidy to lean on", 470, 620, "w:own", size=44, w=600)
    elif n == 9:  # not ending; only subsidy ended
        s.card(40, 70, 1044, 220, "w:no", sfx="pop")
        s.badge("close", 80, 110, 140, "w:no", bg=PINK, sfx="stamp")
        s.txt("Part D ends in 2027", 270, 150, "w:no", size=60, w=760)
        s.add('<div id="@ID" class="e" style="left:270px;top:205px;width:640px;height:10px;background:%s;border-radius:5px"></div>' % PINK, "w:no", "growx", 0.4)
        s.card(40, 330, 1044, 220, "w:not", sfx="pop2")
        s.badge("check", 80, 370, 140, "w:not", bg=TEAL, sfx="ding")
        s.txt("Part D continues", 270, 410, "w:not", size=60, w=760)
        s.txt("Nobody canceled the program", 270, 480, "w:nobody", size=34, w=760, weight=400, color=GRAYT)
        s.card(40, 590, 1044, 220, "w:Only", border="6px solid " + PINK, sfx="pop")
        s.badge("dollar", 80, 630, 140, "w:Only", bg=BLUE)
        s.txt("The extra insurer subsidy", 270, 670, "w:Only", size=52, w=500)
        s.stamp("Ended", 800, 640, "w:ended", size=70, rot=-6)
    elif n == 10:  # big question
        s.badge("help", 60, 190, 400, "w:big", bg=BLUE, sfx="pop")
        s.ttl("How will<br>insurers<br>react?", 520, 160, "w:How", size=84, color=INK, w=560)
        s.badge("building", 520, 560, 150, "w:insurance", bg=PURP)
        i = s.badge("dollar", 720, 560, 150, "w:losing", bg=YEL, fg=INK)
        s.js.append("tl.to('#%s',{y:140,opacity:0.25,duration:1.2,ease:'power1.in'},%.3f);" % (i, s.T("w:losing") + 0.3))
        s.txt("…to losing money?", 700, 700, "w:losing", size=44, w=420)
    elif n == 11:  # two locked things
        s.chip("Locked in by federal law", 60, 40, 0.3, size=48)
        s.card(40, 160, 500, 600, 0.4)
        s.card(584, 160, 500, 600, 0.6)
        s.num("1", 80, 195, 96, 0.5, bg=BG_PINK)
        s.num("2", 624, 195, 96, 0.7, bg=BG_PINK)
        s.badge("lock", 190, 330, 200, 0.8, bg=BLUE)
        s.sfx.append((s.start + s.T("w:locked"), "lock"))
        s.badge("lock", 734, 330, 200, 1.1, bg=BLUE)
        s.ttl("Out-of-pocket cap", 70, 590, "w:two", size=42, w=440, align="center", color=INK)
        s.ttl("Deductible", 614, 590, "w:touch", size=42, w=440, align="center", color=INK)
    elif n == 12:  # $2,400 count-up
        s.chip("2027 maximum annual out-of-pocket cap", 60, 60, 0.25, size=46)
        i = s.stat("$0", 30, 190, 0.6, size=330, color="#fff", w=1064, align="center", sfx="pop")
        t0, t1 = 0.7, max(s.T("w:twenty") + 0.15, 3.0)
        s.js.append("{ const o = { v: 0 }; tl.to(o, { v: 2400, duration: %.3f, ease: 'power2.out', onUpdate: () => { document.getElementById('%s').textContent = '$' + Math.round(o.v).toLocaleString('en-US'); } }, %.3f); }" % (t1 - t0, i, t0))
        s.txt("on covered prescriptions · set by law", 60, 600, "w:covered", size=52, w=1004, align="center")
    elif n == 13:  # deductible inside the cap
        s.chip("Standard maximum deductible: regulated by law", 60, 40, 0.25, size=44)
        s.add('<div id="@ID" class="e" style="left:60px;top:230px;width:1004px;height:80px;background:rgba(255,255,255,.28);border-radius:40px"></div>', 0.4, "fade")
        s.add('<div id="@ID" class="e" style="left:60px;top:230px;width:230px;height:80px;background:%s;border-radius:40px 0 0 40px"></div>' % PINK, "w:deductible", "growx", 0.5)
        s.add('<div id="@ID" class="e" style="left:290px;top:230px;width:774px;height:80px;background:%s;border-radius:0 40px 40px 0"></div>' % TEAL, "w:Once", "growx", 1.4)
        s.txt("Deductible", 60, 330, "w:deductible", size=40, w=230, align="center", weight=900)
        s.txt("$2,400 out-of-pocket cap", 290, 330, "w:Once", size=40, w=774, align="center", weight=900)
        s.txt("Illustration, not to scale", 60, 400, "w:Once", size=26, w=1004, align="center", weight=400)
        s.stat("$0", 60, 470, "w:zero", size=330, color="#fff", w=480, sfx="pop")
        s.txt("you pay", 560, 640, "w:pay", size=72, weight=900, w=520)
    elif n == 14:  # two levers
        s.chip("Insurers' two levers to protect profits", 60, 40, "w:levers", size=46)
        s.card(40, 160, 500, 640, 0.4)
        s.card(584, 160, 500, 640, 0.6)
        s.num("1", 80, 195, 96, 0.5, bg=PINK)
        s.num("2", 624, 195, 96, 0.7, bg=PINK)
        s.badge("dollar", 190, 340, 200, 0.8, bg=BLUE, sfx="pop")
        s.badge("list", 734, 340, 200, 1.1, bg=PURP, sfx="pop2")
        s.ttl("Monthly<br>premiums", 70, 600, "w:premiums", size=48, w=440, align="center")
        s.ttl("Drug<br>formularies", 614, 600, "w:formularies", size=48, w=440, align="center")
    elif n == 15:  # half see higher
        s.chip("Government forecast", 60, 40, "w:forecasts", size=46)
        s.people(110, 150, 10, 5, 25, "w:roughly", size=70, gap=20, c1=YEL, c2="rgba(255,255,255,.45)", hl_t="w:higher")
        s.ttl("About half", 60, 630, "w:half", size=110, color=YEL, sfx="pop")
        s.txt("of people on Part D will see<br>higher monthly premiums next year", 60, 750, "w:higher", size=40, w=1000)
    elif n == 16:  # $0 -> $10-20
        s.chip("Many plans across the country", 60, 40, "w:Across", size=46)
        s.stat("$0", 0, 230, "w:zero", size=270, color="#fff", w=380, align="center", sfx="pop")
        s.txt("per month", 0, 560, "w:zero", size=48, w=380, align="center")
        s.arrow(400, 370, 480, 370, "w:jumping", dur=0.4, wd=14, color="#fff")
        s.stat("$10–20", 500, 300, "w:jumping", size=140, color=YEL, w=624, align="center", sfx="pop2")
        s.txt("per month", 500, 560, "w:jumping", size=48, w=624, align="center")
        s.dark("Plans that used to be free", 160, 720, "w:used", size=48)
    elif n == 17:  # formulary
        s.chip("Lever 2: the formulary", 60, 40, "w:second", size=46)
        s.card(40, 130, 640, 700, 0.35, sfx="pop")
        s.ttl("Covered drug list", 80, 160, 0.5, size=40, color=INK, upper=False)
        for k in range(6):
            s.drug("Drug %s" % "ABCDEF"[k], 70, 240 + k * 96, 580, 0.0 + s.T("w:list") + 0.15 * k if False else "w:list", ok=True)
        s.badge("list", 790, 250, 260, "w:list", bg=PURP)
        s.txt("The list of covered drugs", 720, 560, "w:list", size=44, w=360, align="center")
    elif n == 18:  # slimming
        s.card(40, 130, 640, 700, 0.1, anim="fade")
        s.ttl("Covered drug list", 80, 160, 0.1, size=40, color=INK, upper=False, anim="fade")
        for k in range(6):
            s.drug("Drug %s" % "ABCDEF"[k], 70, 240 + k * 96, 580, 0.2, ok=True, anim="fade")
        for k in (2, 3, 4, 5):
            s.js.append("tl.to('#s18e%d',{opacity:.18,x:60,duration:.5,ease:'power2.in'},%.3f);" % (4 + k, s.T("w:slimming") + 0.18 * (k - 2)))
        s.badge("warn", 760, 150, 170, "w:risk", bg=PINK)
        s.txt("Expensive drugs =<br>big financial risk<br>for insurers", 720, 360, "w:risk", size=44, w=380, align="center")
        s.dark("Fewer drugs covered", 700, 610, "w:slimming", size=38)
    elif n == 19:  # the catch
        s.dark("The unfair catch", 60, 40, "w:catch", size=60, sfx="pop")
        s.badge("lock", 380, 140, 360, "w:locked", bg=PINK, sfx="lock")
        s.ttl("You pick a plan.<br>You're locked in.", 0, 560, "w:pick", size=64, w=1124, align="center")
        s.txt("It surprises most seniors", 0, 770, "w:surprises", size=44, w=1124, align="center", color=GRAYT)
    elif n == 20:  # Jan 1 lock
        s.cal("JAN", "1", 60, 90, "w:January", w=240)
        s.chip("Your plan starts", 330, 140, "w:starts", size=48)
        for k in range(12):
            s.add('<div id="@ID" class="e" style="left:%dpx;top:480px;width:78px;height:76px;background:%s;border-radius:12px"></div>' % (60 + k * 85, TEAL), "w:January", "fade", 0.3)
        s.badge("lock", 480, 600, 160, "w:cannot", bg=PINK, sfx="lock")
        s.chip("No switching mid-year", 660, 650, "w:cannot", bg=PINK, fg=INK, size=40)
        s.chip("Unless you move out of state", 130, 790, "w:unless", size=44)
        s.badge("pin", 60, 780, 70, "w:unless", bg=BLUE)
    elif n == 21:  # drops mid-year
        s.chip("Congress still lets insurers change the list", 60, 40, "w:Congress", size=42)
        for k in range(12):
            s.add('<div id="@ID" class="e" style="left:%dpx;top:520px;width:78px;height:76px;background:%s;border-radius:12px"></div>' % (60 + k * 85, TEAL), 0.3, "fade", 0.3)
        i = s.pill(500, 330, "w:medications", rot=-35)
        s.js.append("tl.to('#%s',{y:300,opacity:0,rotation:40,duration:.8,ease:'power2.in'},%.3f);" % (i, s.T("w:drop") + 0.3))
        s.dark("MID-YEAR", 430, 640, "w:during", size=48, sfx="pop")
        s.badge("list", 120, 200, 180, "w:change", bg=PURP)
        s.txt("Drug list changes", 320, 250, "w:change", size=44, w=420)
    elif n == 22:  # Jan -> Feb letter
        s.cal("JAN", "1", 40, 90, "w:Imagine", w=240, band=TEAL)
        s.txt("Plan starts", 40, 350, "w:Imagine", size=42, w=240, align="center")
        s.arrow(300, 200, 420, 200, "w:February", dur=0.4)
        s.cal("FEB", "!", 440, 90, "w:February", w=240, band=PINK)
        s.badge("mail", 740, 90, 240, "w:letter", bg=PINK, sfx="pop")
        s.card(40, 470, 1044, 290, "w:dropping", border="6px solid " + PINK)
        s.badge("pill", 80, 540, 150, "w:dropping", bg=BG_PINK)
        s.txt("Your most expensive<br>prescription is dropped", 270, 530, "w:dropping", size=54, w=760, color=INK)
        s.stamp("Dropped", 780, 405, "w:expensive", size=56, rot=-6)
    elif n == 23:  # appeal -> no
        s.badge("doc", 80, 130, 280, "w:file", bg=BLUE, sfx="pop")
        s.txt("Exception appeal", 40, 440, "w:appeal", size=52, w=360, align="center")
        s.arrow(400, 270, 600, 270, "w:beg", dur=0.5)
        s.badge("building", 620, 130, 280, "w:insurance", bg=PURP)
        s.txt("Insurer", 600, 440, "w:insurance", size=52, w=320, align="center")
        s.stamp("No", 740, 520, "w:no", size=190, rot=-10)
        s.dark("You can ask. They can still say no.", 60, 740, "w:can", size=46)
    elif n == 24:  # shop every fall
        s.chip("Shop your Part D plan every fall", 60, 40, "w:shopping", size=50)
        s.cal("OCT", "15", 60, 200, "w:fifteenth", w=300, band=TEAL, sfx="pop")
        s.cal("DEC", "7", 764, 200, "w:seventh", w=300, band=PINK, sfx="pop2")
        s.bar(380, 330, 364, 40, "w:between", color="rgba(255,255,255,.35)", anim="fade")
        s.bar(380, 330, 364, 40, "w:between", color="#fff", anim="growx", dur=1.4)
        s.dark("Every single fall", 280, 600, "w:every", size=64)
        s.txt("It is so critical", 280, 720, "w:critical", size=48, w=560, align="center", color=GRAYT)
    elif n == 25:  # biggest mistake on medicare.gov
        s.card(40, 90, 1044, 620, "w:Medicare", radius=22, sfx="pop")
        s.add('<div id="@ID" class="e" style="left:40px;top:90px;width:1044px;height:76px;background:%s;border-radius:22px 22px 0 0"></div>' % INK, "w:Medicare", "fade")
        s.txt("Medicare.gov", 80, 105, "w:Medicare", size=40, color=WHITE, w=400)
        s.chip("Sort: lowest monthly premium ▼", 80, 200, "w:sorting", size=40)
        for k, (nm, pr) in enumerate((("Plan A", "$0"), ("Plan B", "$0"), ("Plan C", "$7"))):
            s.add('<div id="@ID" class="e" style="left:80px;top:%dpx;width:964px;height:86px;background:#F1F4F4;border-radius:14px;font-size:38px;font-weight:700;line-height:86px;padding-left:30px;color:%s">%s<span style="position:absolute;left:520px">%s / month</span></div>' % (290 + k * 100, INK, nm, pr), "w:lowest", "left", 0.4)
        s.stat("", 0, 0, 0.1, size=1)  # spacer
        s.add('<div id="@ID" class="e" style="left:760px;top:590px;width:284px;height:80px;background:%s;color:#fff;border-radius:40px;font-size:38px;font-weight:900;line-height:80px;text-align:center">ENROLL</div>' % BLUE, "w:enroll", "zoom")
        s.stamp("Biggest mistake", 220, 745, "w:biggest", size=64, rot=-4)
    elif n == 26:  # $0 is no bargain
        s.card(40, 70, 480, 420, "w:zero", sfx="pop")
        s.stat("$0", 40, 80, "w:zero", size=250, color=TEAL, w=480, align="center")
        s.txt("per month", 40, 380, "w:zero", size=44, w=480, align="center", color=INK)
        s.dark("No bargain if…", 580, 90, "w:bargain", size=60)
        s.badge("close", 580, 260, 110, "w:cover", bg=PINK, sfx="stamp")
        s.txt("It doesn't cover<br>your actual medications", 720, 262, "w:cover", size=44, w=370)
        s.badge("close", 580, 480, 110, "w:tiers", bg=PINK, sfx="stamp")
        s.txt("It uses expensive<br>pharmacy tiers", 720, 482, "w:tiers", size=44, w=370)
        s.chip("Zero-dollar plan", 60, 560, "w:zerodollar", size=44) if False else None
    elif n == 27:  # enter meds, calc cost
        s.chip("On Medicare.gov, enter every…", 60, 40, "w:enter", size=46)
        s.drug("Medication A · 10 mg", 60, 160, 560, 0.45, ok=True)
        s.drug("Medication B · 25 mg", 60, 270, 560, "w:milligram", ok=True)
        s.drug("Medication C · 5 mg", 60, 380, 560, "w:dosage", ok=True)
        s.arrow(640, 330, 740, 330, "w:calculate", dur=0.4, color="#fff")
        s.card(760, 190, 320, 400, "w:calculate", sfx="pop")
        s.badge("dollar", 840, 220, 160, "w:calculate", bg=TEAL)
        s.txt("Your lowest<br>annual cost", 760, 420, "w:lowest", size=44, w=320, align="center", color=INK)
        s.dark("Not the lowest premium", 120, 640, "w:lowest", size=52)
    elif n == 28:  # $40 plan saves thousands
        s.chip("Often…", 60, 40, "w:Often", size=50)
        s.bar(160, 240, 300, 520, "w:forty", color=BG_PINK, anim="growyb", dur=0.9)
        s.bar(660, 480, 300, 280, "w:forty", color=YEL, anim="growyb", dur=0.9)
        s.txt("$0 plan", 160, 780, "w:forty", size=44, w=300, align="center")
        s.txt("Higher yearly cost", 110, 160, "w:forty", size=40, w=400, align="center", color="#fff")
        s.txt("$40 plan", 660, 780, "w:forty", size=44, w=300, align="center")
        s.txt("Lower yearly cost", 655, 405, "w:forty", size=36, w=330, align="center", color=YEL)
        s.arrow(470, 215, 625, 415, "w:thousands", color=YEL, wd=14, dur=0.7)
        s.chip("Saves thousands", 620, 140, "w:thousands", size=56, sfx="pop")
    elif n == 29:  # healthy
        s.badge("heart", 100, 180, 300, "w:healthy", bg=TEAL, sfx="pop")
        s.chip("Completely healthy", 60, 40, "w:healthy", size=50)
        s.stat("0", 480, 150, "w:zero", size=300, color=BLUE, w=240, align="center")
        s.txt("medications", 440, 480, "w:zero", size=52, w=320, align="center")
        s.txt("or", 760, 280, "w:one", size=48, w=80, align="center", color=GRAYT)
        s.pill(870, 280, "w:cheap", rot=-35, ln=170, th=64, c1=TEAL)
        s.txt("one cheap generic<br>blood pressure pill", 780, 420, "w:generic", size=40, w=300, align="center")
    elif n == 30:  # tempted to drop
        s.stat("$0", 30, 110, "w:formerly", size=240, color="#fff", w=330, align="center")
        s.arrow(370, 250, 470, 250, "w:twenty", dur=0.4, wd=14, color="#fff")
        s.stat("$20", 470, 110, "w:twenty", size=240, color=YEL, w=330, align="center", sfx="pop")
        s.txt("per month", 470, 380, "w:twenty", size=44, w=330, align="center")
        s.card(260, 520, 600, 220, "w:tempted", sfx="pop")
        s.add('<div id="@ID" class="e" style="left:300px;top:575px;width:520px;height:110px;background:%s;color:#fff;border-radius:55px;font-size:48px;font-weight:900;line-height:110px;text-align:center">Drop Part D?</div>' % PINK, "w:tempted", "zoom")
    elif n == 31:  # do not make that mistake
        s.badge("close", 20, 150, 360, "w:Do", bg=PINK, sfx="stamp")
        s.ttl("Don't drop<br>Part D", 420, 140, "w:Do", size=80, w=700)
        s.chip("without other credible drug coverage", 420, 380, "w:credible", size=40, w=640)
        s.num("2", 420, 560, 150, "w:two", bg=BLUE, sfx="pop")
        s.ttl("dangers", 600, 595, "w:two", size=64, w=420)
        s.badge("warn", 20, 560, 220, "w:exposed", bg=YEL, fg=INK)
        s.txt("completely exposed", 0, 800, "w:exposed", size=38, w=260, align="center", color=GRAYT)
    elif n == 32:  # first danger
        s.num("1", 40, 60, 130, 0.2, bg=PINK)
        s.chip("An unexpected illness…", 200, 85, "w:unexpected", size=50)
        s.cal("MAR", "", 60, 260, "w:March", w=250, band=PINK)
        s.badge("pill", 400, 270, 200, "w:costly", bg=PURP)
        s.txt("Costly<br>medication", 340, 490, "w:costly", size=44, w=320, align="center")
        s.badge("shield", 720, 250, 280, "w:cap", bg=LGRAY, fg=WHITE)
        s.badge("close", 880, 230, 130, "w:not", bg=PINK, sfx="stamp")
        s.txt("No $2,400 cap", 690, 560, "w:cap", size=50, w=360, align="center")
    elif n == 33:  # second danger
        s.num("2", 40, 60, 130, 0.2, bg=PINK)
        s.chip("Enroll in Part D later…", 200, 85, "w:later", size=50)
        s.badge("clock", 80, 270, 300, "w:eventually", bg="#fff", fg=INK, sfx="pop")
        s.ttl("Permanent<br>lifetime<br>late penalty", 430, 250, "w:permanent", size=84, w=640, color=PINK, sfx="stamp")
        s.dark("Charged by Medicare", 430, 650, "w:Medicare", size=48)
    else:
        raise ValueError(n)
    return s


def main():
    shots = [build(n) for n in range(1, 34)]
    os.makedirs(os.path.join(ROOT, "compositions"), exist_ok=True)
    bad = 0
    for s in shots:
        open(os.path.join(ROOT, "compositions", "shot%02d.html" % s.n), "w").write(s.render())
        if s.missing:
            bad += 1
            print("shot %d: anchors not found: %s" % (s.n, s.missing))
    # --- index.html
    hosts = []
    for s in shots:
        hosts.append('      <div id="shot%02d" class="clip" data-composition-id="shot%02d" data-composition-src="compositions/shot%02d.html" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 3"></div>' % (s.n, s.n, s.n, s.start, s.end - s.start, 1 + (s.n % 2)))
    audio = []
    aid = 0

    def au(src, start, dur, vol, fade_out=None, name=None):
        nonlocal aid
        aid += 1
        fo = ' data-fade-out="%s"' % fade_out if fade_out else ""
        audio.append('      <audio id="%s" src="assets/audio/%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-volume="%s"%s></audio>' % (name or "a%03d" % aid, src, start, dur, 10 + (aid % 12), vol, fo))

    au("voice_full.wav", 0, TOTAL, 1, name="voice")
    au("bed_full.mp3", 0, 268.6, 0.10, fade_out=2.0, name="bed")
    for s in shots:
        for t, nm in s.sfx:
            f, d, v = SFX[nm]
            au(f, t, d, v)
    # chapter whooshes
    for ch in (2, 3, 4, 5):
        au("whoosh_a.mp3", CHAPTER_START[ch] - 0.05, 0.8, 0.26)
    # Shots 34-37 audio (clip time + CLIP0)
    for src, t, d, v, fo in (("paper_unfold.mp3", 0.3, 1.48, 2, None), ("ding_a.mp3", 2.96, 0.8, 0.32, None), ("ding_b.mp3", 9.98, 0.8, 0.32, None),
                             ("ding_a.mp3", 12.98, 0.8, 0.32, None), ("bell_ping.mp3", 13.4, 1.48, 2.2, None), ("marker_swipe.mp3", 15.8, 1.2, 0.4, None),
                             ("tick_a.mp3", 23.5, 0.48, 1.1, None), ("tick_b.mp3", 24.34, 0.48, 1.4, None), ("tick_a.mp3", 24.9, 0.48, 1.1, None),
                             ("mouse_click.mp3", 29.02, 0.48, 0.22, None), ("chord.mp3", 29.4, 1.44, 0.4, 0.5)):
        au(src, CLIP0 + t, d, v, fade_out=fo)
    au("music.mp3", CLIP0 + 20.1, 10.74, 0.14, fade_out=0.9, name="finale-music")
    index = INDEX_TMPL % ("%.2f" % TOTAL, "%.2f" % TOTAL, "\n".join(hosts), CLIP0, CLIP0, "%.2f" % (TOTAL - CLIP0), "%.2f" % TOTAL, "\n".join(audio))
    open(os.path.join(ROOT, "index.html"), "w").write(index)
    # --- tabs
    open(os.path.join(ROOT, "compositions", "tabs.html"), "w").write(tabs_html())
    print("generated 33 shots; chapter starts:", {k: round(v, 2) for k, v in CHAPTER_START.items()}, "| anchor problems:", bad)


INDEX_TMPL = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #ffffff; }
      #main { position: absolute; inset: 0; }
    </style>
  </head>
  <body>
    <!-- GENERATED by tools/gen_scenes.py - edit the generator (or the hand-authored checklist/contact scenes), not this file. -->
    <div id="main" data-composition-id="main" data-start="0" data-duration="%s" data-width="1920" data-height="1080" data-fps="25">
      <div id="bg" class="clip" data-composition-id="bg" data-composition-src="compositions/bg.html" data-start="0" data-duration="%s" data-track-index="0" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 1"></div>
%s
      <div id="checklist" class="clip" data-composition-id="checklist" data-composition-src="compositions/checklist.html" data-start="%.3f" data-duration="20.5" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 3"></div>
      <div id="contact" class="clip" data-composition-id="contact" data-composition-src="compositions/contact.html" data-start="%.3f" data-duration="%s" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 4"></div>
      <div id="tabs" class="clip" data-composition-id="tabs" data-composition-src="compositions/tabs.html" data-start="0" data-duration="%s" data-track-index="3" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 5"></div>
%s
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
# (the %s order above: dur, bg dur, hosts, checklist start, contact start, contact dur, tabs dur, audio)


def tabs_html():
    names = ["The Rumor", "Subsidy", "Locked-In", "Levers", "Shop Smart", "ANOC &amp; Dec 7", "Free Review"]
    tabs = "\n      ".join('<div class="tab" id="tab%d"><div class="doneov" id="tab%d-done"></div><div class="fill" id="tab%d-fill"></div><div class="in"><span class="num" id="tab%d-num">%d</span><span class="lbl" id="tab%d-lbl">%s</span></div></div>' % (i + 1, i + 1, i + 1, i + 1, i + 1, i + 1, nm) for i, nm in enumerate(names))
    base = open(os.path.join(HERE, "tabs_base.html")).read()
    tw = []
    for i in range(1, 8):
        a = CHAPTER_START[i]
        b = CHAPTER_START[i + 1] if i < 7 else None
        tw.append("light(%d, %.3f);" % (i, max(a, 0.18)))
        if b is not None:
            tw.append("done(%d, %.3f);" % (i, b))
    return base.replace("@@TABS@@", tabs).replace("@@TW@@", "\n    ".join(tw))


if __name__ == "__main__":
    main()
