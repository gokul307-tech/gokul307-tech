from collections import deque
from pathlib import Path
import argparse
from html import escape

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


CHARS = " .:-=+*#%@"
BACKGROUND_THRESHOLD = 8
GRID_COLS = 88
GRID_ROWS = 54
VIEW_WIDTH = 980
VIEW_HEIGHT = 640
TEXT_X = 8
TEXT_Y = 20
FONT_SIZE = 10
LINE_HEIGHT = 11.4
PALETTE = ("#7bb88a", "#9bd5a8", "#c7f1cf")


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


def shade_for(luminance, x, y, is_foreground):
    if is_foreground:
        x_fraction = x / (GRID_COLS - 1)
        y_fraction = y / (GRID_ROWS - 1)
        crown_boost = 170 * max(0, 1 - y_fraction / 0.38)
        cheek_x = max(0, 1 - abs(x_fraction - 0.67) / 0.17)
        cheek_y = max(0, 1 - abs(y_fraction - 0.49) / 0.14)
        luminance = min(255, int(luminance + crown_boost + 90 * cheek_x * cheek_y))
    return min(len(PALETTE) - 1, luminance * len(PALETTE) // 256)


def render_ascii(image, mask):
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.25)
    image = image.resize((GRID_COLS, GRID_ROWS), Image.Resampling.LANCZOS)
    mask = mask.resize((GRID_COLS, GRID_ROWS), Image.Resampling.LANCZOS)
    pixels = image.tobytes()
    foreground = mask.tobytes()

    lines = []
    for y in range(GRID_ROWS):
        runs = []
        current_shade = None
        current_alpha = None
        current_text = []

        for x in range(GRID_COLS):
            index = y * GRID_COLS + x
            luminance = pixels[index]
            char = CHARS[(255 - luminance) * (len(CHARS) - 1) // 255]
            shade = shade_for(luminance, x, y, foreground[index] >= 128)
            char_opacity = 1.0

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
    portrait = ImageOps.fit(source, (420, 420))
    mask = foreground_mask(source).resize((420, 420), Image.Resampling.LANCZOS)

    ascii_lines = render_ascii(portrait, mask)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}" viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" role="img" aria-labelledby="title description">
<title id="title">Dense green terminal ASCII portrait</title>
<desc id="description">A chest-up ASCII portrait on a dark terminal canvas, revealed by a top-to-bottom scan.</desc>
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
    font-family: "Courier New", ui-monospace, monospace;
    font-size: {FONT_SIZE}px;
    dominant-baseline: alphabetic;
    white-space: pre;
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
    92% {{ transform: translateY(620px); opacity: .95; }}
    100% {{ transform: translateY(620px); opacity: 0; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    .reveal-window {{ height: {VIEW_HEIGHT}px !important; animation: none !important; }}
    .scan-line {{ opacity: 0 !important; animation: none !important; }}
  }}
</style>
<rect width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}" fill="#080b0a"/>
<g clip-path="url(#portrait-clip)">
{ascii_lines}
</g>
<line class="scan-line" x1="8" y1="8" x2="{VIEW_WIDTH - 8}" y2="8" stroke="#62ffad" stroke-width="1.1" filter="url(#scan-glow)"/>
<line class="scan-line" x1="8" y1="8" x2="{VIEW_WIDTH - 8}" y2="8" stroke="#d8ffea" stroke-width="0.7"/>
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
