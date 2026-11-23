from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance
import argparse

CHARS = " .:-=+*#%@"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="local-assets/portrait-source.jpg")
    parser.add_argument("--output", default="avi-ascii.svg")
    args = parser.parse_args()
    image = Image.open(args.input).convert("L")
    image = ImageOps.fit(image, (420, 420))
    image = ImageEnhance.Contrast(ImageOps.autocontrast(image)).enhance(1.25)
    cols, rows = 88, 54
    image = image.resize((cols, rows))
    px = list(image.getdata())
    lines = []
    for y in range(rows):
        line = "".join(CHARS[int((255-px[y*cols+x])/255*(len(CHARS)-1))] for x in range(cols)).rstrip()
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f'<text x="8" y="{22+y*11}" class="line" style="--i:{y}">{line}</text>')
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="980" height="640" viewBox="0 0 980 640">
<rect width="100%" height="100%" fill="#080b0a"/>
<style>.line{font:10px "Courier New",monospace;fill:#b8d8c0;opacity:0;animation:typeIn .45s steps(1,end) forwards;animation-delay:calc(var(--i)*.035s)}@keyframes typeIn{to{opacity:1}}@media(prefers-reduced-motion:reduce){.line{animation:none;opacity:1}}</style>
''' + "".join(lines) + "</svg>"
    Path(args.output).write_text(svg, encoding="utf-8")

if __name__ == "__main__":
    main()
