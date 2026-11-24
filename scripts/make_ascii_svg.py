from collections import deque
from pathlib import Path
import argparse
from html import escape

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


CHARS = " .,:;irsXA253hMHGS#9B&@"
BACKGROUND_THRESHOLD = 8
GRID_COLS = 120
GRID_ROWS = 68
VIEW_WIDTH = 600
VIEW_HEIGHT = 650
TEXT_X = 12
TEXT_Y = 24
FONT_SIZE = 8
LINE_HEIGHT = 9
PALETTE = ("#8A8A8A", "#A1A1A1", "#C6C6C6", "#E6E6E6")


def foreground_mask(image):
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


def render_ascii(image, mask):
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = image.resize((GRID_COLS, GRID_ROWS), Image.Resampling.LANCZOS)
    mask = mask.resize((GRID_COLS, GRID_ROWS), Image.Resampling.LANCZOS)
    pixels = image.tobytes()
    alpha = mask.tobytes()
    lines = []

    for y in range(GRID_ROWS):
        runs = []
        current_style = None
        current_text = []

        for x in range(GRID_COLS):
            index = y * GRID_COLS + x
            luminance = pixels[index]
            opacity = alpha[index]
            char = " " if opacity < 50 else CHARS[
                (255 - luminance) * (len(CHARS) - 1) // 255
            ]
            shade = min(len(PALETTE) - 1, luminance * len(PALETTE) // 256)
            char_opacity = 1.0 if opacity >= 200 else 0.65 if opacity >= 110 else 0.4
            style = (PALETTE[shade], char_opacity)

            if style != current_style:
                if current_text:
                    fill, alpha_value = current_style
                    runs.append(
                        f'<tspan fill="{fill}" opacity="{alpha_value:.2f}">'
                        f"{escape(''.join(current_text))}</tspan>"
                    )
                current_style = style
                current_text = [char]
            else:
                current_text.append(char)

        if current_text:
            fill, alpha_value = current_style
            runs.append(
                f'<tspan fill="{fill}" opacity="{alpha_value:.2f}">'
                f"{escape(''.join(current_text))}</tspan>"
            )
        baseline = TEXT_Y + y * LINE_HEIGHT
        lines.append(
            f'<text x="{TEXT_X}" y="{baseline}" class="portrait-row" xml:space="preserve">'
            f'{"".join(runs)}</text>'
        )
    return "\n".join(lines)


def create_svg(input_path, output_path):
    source = Image.open(input_path).convert("L")
    width, height = source.size
    crop = (round(width * 0.025), 0, round(width * 0.975), height)
    portrait = source.crop(crop)
    mask = foreground_mask(source).crop(crop)
    ascii_lines = render_ascii(portrait, mask)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}" viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="portrait-title portrait-description">
<title id="portrait-title">Grayscale ASCII portrait of Gokul Vasan</title>
<desc id="portrait-description">A transparent chest-up ASCII portrait reconstructed by a grayscale scanning reveal.</desc>
<defs>
  <clipPath id="portrait-clip" clipPathUnits="userSpaceOnUse">
    <rect class="reveal-window" x="0" y="0" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}"/>
  </clipPath>
  <filter id="scan-soften" x="-10%" y="-100%" width="120%" height="300%">
    <feGaussianBlur stdDeviation="1.2"/>
  </filter>
</defs>
<style>
  .portrait-row {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
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
      opacity: .8;
      animation: scan-down 7.2s cubic-bezier(.16,.72,.24,1) forwards;
    }}
  }}
  @keyframes portrait-reveal {{
    to {{ height: {VIEW_HEIGHT}px; }}
  }}
  @keyframes scan-down {{
    0% {{ transform: translateY(0); opacity: .8; }}
    92% {{ transform: translateY(628px); opacity: .8; }}
    100% {{ transform: translateY(628px); opacity: 0; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    .reveal-window {{ height: {VIEW_HEIGHT}px !important; animation: none !important; }}
    .scan-line {{ opacity: 0 !important; animation: none !important; }}
  }}
</style>
<g clip-path="url(#portrait-clip)">
{ascii_lines}
</g>
<line class="scan-line" x1="0" y1="12" x2="{VIEW_WIDTH}" y2="12" stroke="#D5D5D5" stroke-width="1" filter="url(#scan-soften)"/>
<line class="scan-line" x1="0" y1="12" x2="{VIEW_WIDTH}" y2="12" stroke="#E6E6E6" stroke-width="0.55"/>
</svg>
'''
    Path(output_path).write_text(svg, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a transparent grayscale ASCII portrait SVG."
    )
    parser.add_argument("--input", default="local-assets/portrait-source.jpg")
    parser.add_argument("--output", default="avi-ascii.svg")
    args = parser.parse_args()
    create_svg(args.input, args.output)


if __name__ == "__main__":
    main()
