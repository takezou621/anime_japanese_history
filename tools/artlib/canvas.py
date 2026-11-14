"""描画基盤 — スーパーサンプリング (2x) 対応キャンバスとプリミティブ.

座標はすべて「最終解像度」系で受け取り、内部で ss 倍して描画する。
Canvas.render() で LANCZOS 縮小し、アンチエイリアスされた画像を返す。
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SS_DEFAULT = 2

# ---------------------------------------------------------------- 色ユーティリティ


def as_rgb(c, default=(0, 0, 0)):
    """hex 文字列 / RGB タプル → RGB タプル."""
    if c is None:
        return tuple(default)
    if isinstance(c, str):
        s = c.lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(v) for v in c[:3])


def with_alpha(c, a):
    r, g, b = as_rgb(c)
    return (r, g, b, int(a))


def shade(c, f=0.82):
    """同系色の濃いフラット影."""
    return tuple(max(0, min(255, int(round(v * f)))) for v in as_rgb(c))


def tint(c, f=0.18):
    """同系色の明るいフラット."""
    return tuple(int(round(v + (255 - v) * f)) for v in as_rgb(c))


def mix(c1, c2, t):
    a, b = as_rgb(c1), as_rgb(c2)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ---------------------------------------------------------------- フォント

_FONT_DIRS = [
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
    Path.home() / ".local/share/fonts",
]
_WEIGHTS = {
    "black": "NotoSansJP-Black.otf",
    "bold": "NotoSansJP-Bold.otf",
    "medium": "NotoSansJP-Medium.otf",
    "regular": "NotoSansJP-Regular.otf",
    "light": "NotoSansJP-Light.otf",
    "demilight": "NotoSansJP-DemiLight.otf",
}
_font_cache: dict = {}


def load_font(px, weight="bold"):
    key = (int(px), weight.lower())
    if key in _font_cache:
        return _font_cache[key]
    fname = _WEIGHTS.get(weight.lower(), _WEIGHTS["bold"])
    path = None
    for d in _FONT_DIRS:
        p = d / fname
        if p.exists():
            path = p
            break
    f = ImageFont.truetype(str(path), int(px)) if path else ImageFont.load_default()
    _font_cache[key] = f
    return f


# ---------------------------------------------------------------- 形状ヘルパー


def qbez(p0, p1, p2, n=18):
    """2次ベジエのサンプリング."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def cbez(p0, p1, p2, p3, n=22):
    """3次ベジエのサンプリング."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        x = (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0])
        y = (u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])
        pts.append((x, y))
    return pts


def almond_pts(cx, cy, w, h, top_flat=0.62, bot_round=1.15, n=26):
    """アニメ目のアーモンド形 (角が尖り・上まぶたがフラット)."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        s = math.sin(math.pi * t)
        pts.append((cx - w / 2 + w * t, cy - h / 2 * (s ** top_flat)))
    for i in range(n - 1, -1, -1):
        t = i / (n - 1)
        s = math.sin(math.pi * t)
        pts.append((cx - w / 2 + w * t, cy + h / 2 * (s ** bot_round)))
    return pts


def blob_pts(cx, cy, rx, ry, seed=0, wobble=0.12, n=28):
    """ゆらぎのある有機形 (雲・木・岩など)."""
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, math.tau) for _ in range(3)]
    pts = []
    for i in range(n):
        t = math.tau * i / n
        m = 1 + wobble * (0.6 * math.sin(2 * t + ph[0]) + 0.4 * math.sin(3 * t + ph[1]))
        pts.append((cx + rx * m * math.cos(t), cy + ry * m * math.sin(t)))
    return pts


# ---------------------------------------------------------------- グラデーション


def gradient(size_px, stops, axis="v"):
    """numpy 線形補間グラデ (RGBA 不透明). stops: [(t0,color0),(t1,color1)...]."""
    w, h = int(size_px[0]), int(size_px[1])
    n = h if axis == "v" else w
    ts = np.array([t for t, _ in stops], float)
    cols = np.array([as_rgb(c) for _, c in stops], float)
    u = np.linspace(0.0, 1.0, n)
    arr = np.zeros((n, 3))
    for ch in range(3):
        arr[:, ch] = np.interp(u, ts, cols[:, ch])
    if axis == "v":
        img = Image.fromarray(np.repeat(arr[:, None, :], w, axis=1).astype("uint8"), "RGB")
    else:
        img = Image.fromarray(np.repeat(arr[None, :, :], h, axis=0).astype("uint8"), "RGB")
    return img.convert("RGBA")


def radial(size_px, color, alpha_in=180, alpha_out=0, power=2.0):
    """中心から減衰する放射グラデ (光・グロー用 RGBA)."""
    w, h = int(size_px[0]), int(size_px[1])
    y, x = np.mgrid[0:h, 0:w]
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    d = np.sqrt(((x - cx) / max(cx, 1e-6)) ** 2 + ((y - cy) / max(cy, 1e-6)) ** 2)
    a = np.clip(1.0 - d, 0.0, 1.0) ** power * (alpha_in - alpha_out) + alpha_out
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., :3] = np.array(as_rgb(color), np.uint8)
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ---------------------------------------------------------------- G (描画ラッパ)


def _is_translucent(c):
    return (isinstance(c, (tuple, list)) and len(c) == 4 and c[3] < 255)


class G:
    """最終解像度座標を受け取り ss 倍して ImageDraw に渡すラッパ.

    PIL の ImageDraw は半透明インクを「上書き」するため、alpha<255 のインクは
    内部バッファに溜めて alpha_composite で正しくブレンドする (flush() で確定)。
    """

    def __init__(self, img, size, ss=SS_DEFAULT, owner=None):
        self.img = img
        self.size = size
        self.ss = ss
        self.d = ImageDraw.Draw(img)
        self._tb = None      # 半透明用バッファ
        self._td = None
        self._dirty = False
        self._owner = owner  # Canvas / Layer (最終 flush 用に登録)

    # -- 半透明バッファ制御
    def flush(self):
        if self._tb is not None and self._dirty:
            self.img.alpha_composite(self._tb)
        self._tb = None
        self._td = None
        self._dirty = False

    def _target(self, *inks):
        """使うインクに半透明があればバッファ、なければ本体の ImageDraw."""
        trans = any(_is_translucent(c) for c in inks if c is not None)
        if trans:
            if self._tb is None:
                self._tb = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
                self._td = ImageDraw.Draw(self._tb)
            self._dirty = True
            return self._td
        self.flush()
        return self.d

    # -- 内部変換
    def _w(self, v):
        return max(1, int(round(v * self.ss)))

    def _b(self, box):
        return tuple(v * self.ss for v in box)

    def _p(self, pt):
        return (pt[0] * self.ss, pt[1] * self.ss)

    def _pts(self, pts):
        return [self._p(p) for p in pts]

    # -- プリミティブ
    def poly(self, pts, fill=None, outline=None, owidth=0, joint="curve"):
        p = self._pts(pts)
        d = self._target(fill, outline)
        if fill is not None:
            d.polygon(p, fill=fill)
        if outline is not None and owidth > 0:
            d.line(p + [p[0]], fill=outline, width=self._w(owidth), joint=joint)

    def ellipse(self, box, fill=None, outline=None, owidth=0):
        d = self._target(fill, outline)
        d.ellipse(self._b(box), fill=fill,
                  outline=outline, width=self._w(owidth) if outline else 0)

    def circle(self, cx, cy, r, fill=None, outline=None, owidth=0):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, owidth)

    def rrect(self, box, radius, fill=None, outline=None, owidth=0):
        d = self._target(fill, outline)
        d.rounded_rectangle(self._b(box), radius=radius * self.ss,
                            fill=fill, outline=outline,
                            width=self._w(owidth) if outline else 0)

    def line(self, pts, fill, width, joint="curve"):
        d = self._target(fill)
        d.line(self._pts(pts), fill=fill, width=self._w(width), joint=joint)

    def arc(self, box, start, end, fill, width):
        d = self._target(fill)
        d.arc(self._b(box), start, end, fill=fill, width=self._w(width))

    def pieslice(self, box, start, end, fill=None, outline=None, owidth=0):
        d = self._target(fill, outline)
        d.pieslice(self._b(box), start, end, fill=fill,
                   outline=outline, width=self._w(owidth) if outline else 0)

    def chord(self, box, start, end, fill=None, outline=None, owidth=0):
        d = self._target(fill, outline)
        d.chord(self._b(box), start, end, fill=fill,
                outline=outline, width=self._w(owidth) if outline else 0)

    def dot(self, p, r, fill):
        self.circle(p[0], p[1], r, fill=fill)

    # -- テキスト
    def text(self, pos, s, size, fill, weight="bold", anchor="mm",
             stroke_width=0, stroke_fill=None):
        f = load_font(size * self.ss, weight)
        d = self._target(fill, stroke_fill)
        d.text(self._p(pos), s, font=f, fill=fill, anchor=anchor,
               stroke_width=self._w(stroke_width) if stroke_width else 0,
               stroke_fill=stroke_fill)

    def text_lines(self, pos, lines, size, fill, weight="bold", anchor="ma",
                   leading=1.35, align_w=None):
        """複数行テキスト. pos は anchor 基準の先頭行位置."""
        lh = size * leading
        y = pos[1]
        for ln in lines:
            self.text((pos[0], y), ln, size, fill, weight=weight, anchor=anchor)
            y += lh

    def text_size(self, s, size, weight="bold"):
        f = load_font(size * self.ss, weight)
        x0, y0, x1, y1 = f.getbbox(s)
        return ((x1 - x0) / self.ss, (y1 - y0) / self.ss)


# ---------------------------------------------------------------- Layer / Canvas


class Layer:
    """同じ ss の透明レイヤー. composite() で Canvas に重ねる."""

    def __init__(self, w, h, ss=SS_DEFAULT, ox=0, oy=0):
        self.w, self.h, self.ss = w, h, ss
        self.ox, self.oy = ox, oy
        self.img = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
        self._gs = []

    def g(self):
        g = G(self.img, (self.w, self.h), self.ss, owner=self)
        self._gs.append(g)
        return g

    def flush(self):
        for g in self._gs:
            g.flush()


class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0, 0), ss=SS_DEFAULT):
        self.w, self.h, self.ss = w, h, ss
        if bg is None:
            bg = (0, 0, 0, 0)
        bg = bg if len(bg) == 4 else tuple(as_rgb(bg)) + (255,)
        self.img = Image.new("RGBA", (int(w * ss), int(h * ss)), bg)
        self._gs = []

    def g(self):
        g = G(self.img, (self.w, self.h), self.ss, owner=self)
        self._gs.append(g)
        return g

    def flush(self):
        for g in self._gs:
            g.flush()

    def layer(self, rect=None):
        if rect is None:
            return Layer(self.w, self.h, self.ss)
        x0, y0, x1, y1 = rect
        return Layer(x1 - x0, y1 - y0, self.ss, x0, y0)

    def composite(self, layer):
        layer.flush()
        self.flush()
        self.img.alpha_composite(layer.img,
                                 (int(round(layer.ox * self.ss)), int(round(layer.oy * self.ss))))

    def paste_img(self, img, pos=(0, 0)):
        self.flush()
        self.img.alpha_composite(img, (int(round(pos[0] * self.ss)), int(round(pos[1] * self.ss))))

    def render(self):
        self.flush()
        return self.img.resize((self.w, self.h), Image.LANCZOS)


def sublayer(cv):
    """Canvas/Layer と同サイズの透明レイヤーを作る."""
    return Layer(cv.w, cv.h, cv.ss)


def paste_masked(dst_img, src_img, mask):
    """src を mask (L) で切り抜いて dst にアルファ合成."""
    cut = Image.new("RGBA", src_img.size, (0, 0, 0, 0))
    cut.paste(src_img, (0, 0), mask)
    dst_img.alpha_composite(cut)


# ---------------------------------------------------------------- テクスチャ系


def speckle(g, box, n, colors, r=(1.5, 4.0), seed=0, alpha=None, squash=0.7):
    """地面・壁のごま塩テクスチャ."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        rr = rnd.uniform(*r)
        c = rnd.choice(colors)
        if alpha is not None:
            c = with_alpha(c, alpha)
        g.ellipse((x - rr, y - rr * squash, x + rr, y + rr * squash), fill=c)


def dots_pattern(g, box, spacing, r, color, alpha=40, falloff=None, seed=0):
    """ハーフトーン風ドット (UI 背景)."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    y = y0
    row = 0
    c = with_alpha(color, alpha)
    while y <= y1:
        x = x0 + (spacing / 2 if row % 2 else 0)
        while x <= x1:
            rr = r
            if falloff is not None:
                t = falloff(x, y, cx, cy)
                rr = r * max(0.0, min(1.0, t))
            if rr > 0.4:
                g.circle(x, y, rr, fill=c)
            x += spacing
        y += spacing
        row += 1


# ---------------------------------------------------------------- 保存


def save(img, path, optimize=True):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, optimize=optimize)
    return p


def render_ov(draw_fn, w, h, ss=SS_DEFAULT):
    """透明 Canvas に draw_fn(canvas) を描いて最終サイズ RGBA を返す."""
    cv = Canvas(w, h, ss=ss)
    draw_fn(cv)
    return cv.render()
