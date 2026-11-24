from collections import deque
from pathlib import Path
import argparse
from html import escape

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


CHARS = " .,:-/\\135"
BACKGROUND_THRESHOLD = 8
GRID_COLS = 88
GRID_ROWS = 63
VIEW_WIDTH = 720
VIEW_HEIGHT = 750
TEXT_X = 85
TEXT_Y = 26
FONT_SIZE = 10.4
LINE_HEIGHT = 11.4
PALETTE = ("#00a93f", "#00cc48", "#35f35d")


def foreground_mask(image):
    """Mark dark pixels connected to the image edge as background."""
    width, height = image.size
    pixels = image.tobytes()
    background = bytearray(width * height)
    queue = deque()

    def enqueue(index):
        if not background[index] and pixels[index] <= BACKGROUND_THRESHOLD:
            background[index] = 1
            queue.append(index)

    for x in range(width):
        enqueue(x)
        enqueue((height - 1) * width + x)
    for y in range(height):
        enqueue(y * width)
        enqueue(y * width + width - 1)

    while queue:
        index = queue.popleft()
        x = index % width
        y = index // width
        if x:
            enqueue(index - 1)
        if x + 1 < width:
            enqueue(index + 1)
        if y:
            enqueue(index - width)
        if y + 1 < height:
            enqueue(index + width)

    mask = Image.new("L", image.size)
    mask.putdata([0 if is_background else 255 for is_background in background])
    return mask.filter(ImageFilter.GaussianBlur(radius=0.55))


def shade_for(luminance, x, y):
    x_fraction = x / (GRID_COLS - 1)
    y_fraction = y / (GRID_ROWS - 1)
    crown_boost = 170 * max(0, 1 - y_fraction / 0.38)
    cheek_x = max(0, 1 - abs(x_fraction - 0.72) / 0.18)
    cheek_y = max(0, 1 - abs(y_fraction - 0.49) / 0.14)
    cheek_boost = 90 * cheek_x * cheek_y
    luminance = min(255, int(luminance + crown_boost + cheek_boost))
    return min(len(PALETTE) - 1, luminance * len(PALETTE) // 256)


def render_ascii(image, mask):
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.12)
    image = image.resize((GRID_COLS, GRID_ROWS), Image.Resampling.LANCZOS)
    mask = mask.resize((GRID_COLS, GRID_ROWS), Image.Resampling.LANCZOS)
    pixels = image.tobytes()
    alpha = mask.tobytes()

    lines = []
    for y in range(GRID_ROWS):
        runs = []
        current_shade = None
        current_alpha = None
        current_text = []

        for x in range(GRID_COLS):
            index = y * GRID_COLS + x
            luminance = pixels[index]
            opacity = alpha[index]
            if opacity < 50:
                char = " "
            elif y < GRID_ROWS // 4 and luminance < 120:
                char = "."
            else:
                char = CHARS[(255 - luminance) * (len(CHARS) - 1) // 255]
            shade = shade_for(luminance, x, y)
            char_opacity = 1.0 if opacity >= 200 else 0.65 if opacity >= 110 else 0.4

            if (shade, char_opacity) != (current_shade, current_alpha):
                if current_text:
                    runs.append(
                        f'<tspan fill="{current_shade}" opacity="{current_alpha:.2f}">'
                        f"{escape(''.join(current_text))}</tspan>"
                    )
                current_shade = PALETTE[shade]
                current_alpha = char_opacity
                current_text = [char]
            else:
                current_text.append(char)

        if current_text:
            runs.append(
                f'<tspan fill="{current_shade}" opacity="{current_alpha:.2f}">'
                f"{escape(''.join(current_text))}</tspan>"
            )
        baseline = TEXT_Y + y * LINE_HEIGHT
        lines.append(
            f'<text x="{TEXT_X}" y="{baseline:.1f}" class="portrait-row" xml:space="preserve">'
            f'{"".join(runs)}</text>'
        )
    return "\n".join(lines)


def create_svg(input_path, output_path):
    source = Image.open(input_path).convert("L")
    width, height = source.size
    left = round(width * 0.12)
    right = round(width * 0.88)
    crop = (left, 0, right, height)
    portrait = source.crop(crop)
    mask = foreground_mask(source).crop(crop)

    ascii_lines = render_ascii(portrait, mask)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}" viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" role="img" aria-labelledby="title description">
<title id="title">Green terminal ASCII portrait</title>
<desc id="description">A transparent chest-up ASCII portrait revealed by a top-to-bottom scanning line.</desc>
<defs>
  <clipPath id="portrait-clip" clipPathUnits="userSpaceOnUse">
    <rect class="reveal-window" x="0" y="0" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}"/>
  </clipPath>
  <filter id="scan-glow" x="-10%" y="-100%" width="120%" height="300%">
    <feGaussianBlur stdDeviation="2.2"/>
  </filter>
</defs>
<style>
  .portrait-row {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    font-size: {FONT_SIZE}px;
    dominant-baseline: alphabetic;
    white-space: pre;
    paint-order: stroke;
    stroke: #006126;
    stroke-width: 0.12px;
  }}
  .reveal-window {{ height: {VIEW_HEIGHT}px; }}
  .scan-line {{ opacity: 0; }}
  @supports (animation-name: portrait-reveal) {{
    .reveal-window {{
      height: 0;
      animation: portrait-reveal 7.2s cubic-bezier(.16,.72,.24,1) forwards;
    }}
    .scan-line {{
      opacity: .95;
      animation: scan-down 7.2s cubic-bezier(.16,.72,.24,1) forwards;
    }}
  }}
  @keyframes portrait-reveal {{
    to {{ height: {VIEW_HEIGHT}px; }}
  }}
  @keyframes scan-down {{
    0% {{ transform: translateY(0); opacity: .95; }}
    92% {{ transform: translateY(728px); opacity: .95; }}
    100% {{ transform: translateY(728px); opacity: 0; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    .reveal-window {{ height: {VIEW_HEIGHT}px !important; animation: none !important; }}
    .scan-line {{ opacity: 0 !important; animation: none !important; }}
  }}
</style>
<g clip-path="url(#portrait-clip)">
{ascii_lines}
</g>
<line class="scan-line" x1="8" y1="13" x2="{VIEW_WIDTH - 8}" y2="13" stroke="#62ffad" stroke-width="1.1" filter="url(#scan-glow)"/>
<line class="scan-line" x1="8" y1="13" x2="{VIEW_WIDTH - 8}" y2="13" stroke="#d8ffea" stroke-width="0.7"/>
</svg>
'''
    Path(output_path).write_text(svg, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a transparent, animated ASCII portrait SVG."
    )
    parser.add_argument("--input", default="local-assets/portrait-source.jpg")
    parser.add_argument("--output", default="avi-ascii.svg")
    args = parser.parse_args()
    create_svg(args.input, args.output)


if __name__ == "__main__":
    main()
