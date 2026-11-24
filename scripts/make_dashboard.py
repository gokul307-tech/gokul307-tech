from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

from make_info_card import COLORS, card_items, collect_stats, create_svg


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
WIDTH = 1280
HEIGHT = 640
LEFT_X = 24
LEFT_Y = 52
LEFT_WIDTH = 500
LEFT_HEIGHT = 566
RIGHT_X = 540
RIGHT_Y = 52
RIGHT_WIDTH = 716
RIGHT_HEIGHT = 566
PANEL = COLORS["background"]
MAIN = COLORS["main"]
SECONDARY = COLORS["secondary"]
BORDER = COLORS["border"]
HIGHLIGHT = COLORS["highlight"]
FONT_CANDIDATES = (
    "C:/Windows/Fonts/consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
)


def tag(name):
    return f"{{{SVG_NS}}}{name}"


def svg_text(parent, x, y, value, size, color, weight="normal", anchor="start"):
    element = ET.SubElement(
        parent,
        tag("text"),
        {
            "x": str(x),
            "y": str(y),
            "fill": color,
            "font-size": str(size),
            "font-family": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "font-weight": weight,
            "text-anchor": anchor,
        },
    )
    element.text = value
    return element


def add_component(parent, path, x, y, width, height):
    component = ET.parse(path).getroot()
    viewbox = component.get("viewBox")
    nested = ET.SubElement(
        parent,
        tag("svg"),
        {
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
            "viewBox": viewbox,
            "preserveAspectRatio": "xMidYMid meet",
        },
    )
    for child in component:
        if child.tag in (tag("title"), tag("desc")):
            continue
        nested.append(deepcopy(child))
    return nested


def generate_dashboard_svg():
    root = ET.Element(
        tag("svg"),
        {
            "width": str(WIDTH),
            "height": str(HEIGHT),
            "viewBox": f"0 0 {WIDTH} {HEIGHT}",
            "role": "img",
            "aria-labelledby": "dashboard-title dashboard-description",
        },
    )
    ET.SubElement(root, tag("title"), {"id": "dashboard-title"}).text = (
        "Gokul Vasan developer profile dashboard"
    )
    ET.SubElement(root, tag("desc"), {"id": "dashboard-description"}).text = (
        "A charcoal two-panel dashboard with an animated grayscale ASCII portrait "
        "and current developer information."
    )
    style = ET.SubElement(root, tag("style"))
    style.text = (
        ".dashboard-title{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}"
        ".panel{fill:#17191B;stroke:#454545;stroke-width:1}"
    )
    ET.SubElement(
        root,
        tag("rect"),
        {"width": str(WIDTH), "height": str(HEIGHT), "fill": "#101112"},
    )
    svg_text(root, 24, 31, "GOKUL.VASAN // DEVELOPER PROFILE", 15, MAIN, "bold")
    svg_text(root, 1256, 31, "PORTFOLIO / 01", 10, SECONDARY, anchor="end")
    ET.SubElement(
        root,
        tag("rect"),
        {
            "class": "panel",
            "x": str(LEFT_X),
            "y": str(LEFT_Y),
            "width": str(LEFT_WIDTH),
            "height": str(LEFT_HEIGHT),
            "rx": "12",
        },
    )
    svg_text(root, LEFT_X + 18, LEFT_Y + 24, "PORTRAIT / GRAYSCALE ASCII", 10, HIGHLIGHT)
    svg_text(root, LEFT_X + 18, LEFT_Y + 42, "TOP-TO-BOTTOM RECONSTRUCTION", 8, SECONDARY)
    add_component(
        root,
        "avi-ascii.svg",
        LEFT_X,
        LEFT_Y + 44,
        LEFT_WIDTH,
        LEFT_HEIGHT - 48,
    )
    add_component(
        root,
        "info-card.svg",
        RIGHT_X,
        RIGHT_Y,
        RIGHT_WIDTH,
        RIGHT_HEIGHT,
    )
    ET.indent(root, space="  ")
    Path("profile-dashboard.svg").write_text(
        ET.tostring(root, encoding="unicode"), encoding="utf-8"
    )


@lru_cache(maxsize=32)
def load_font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def color(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def draw_card(draw, stats):
    scale = min(RIGHT_WIDTH / 700, RIGHT_HEIGHT / 560)
    offset_x = RIGHT_X + (RIGHT_WIDTH - 700 * scale) / 2
    offset_y = RIGHT_Y + (RIGHT_HEIGHT - 560 * scale) / 2
    for item in card_items(stats):
        if item["type"] == "line":
            draw.line(
                (
                    offset_x + item["x1"] * scale,
                    offset_y + item["y1"] * scale,
                    offset_x + item["x2"] * scale,
                    offset_y + item["y2"] * scale,
                ),
                fill=color(item["stroke"]),
                width=max(1, round(item["width"] * scale)),
            )
            continue

        font = load_font(max(7, round(item["size"] * scale)))
        x = offset_x + item["x"] * scale
        if item["anchor"] == "middle":
            x -= draw.textlength(item["text"], font=font) / 2
        elif item["anchor"] == "end":
            x -= draw.textlength(item["text"], font=font)
        draw.text(
            (x, offset_y + item["y"] * scale),
            item["text"],
            font=font,
            fill=color(item["fill"]),
            anchor="ls",
        )


def draw_portrait(draw, progress):
    root = ET.parse("avi-ascii.svg").getroot()
    viewbox = [float(value) for value in root.get("viewBox").split()]
    source_width, source_height = viewbox[2], viewbox[3]
    target_x = LEFT_X + 8
    target_y = LEFT_Y + 44
    target_width = LEFT_WIDTH - 16
    target_height = LEFT_HEIGHT - 48
    scale = min(target_width / source_width, target_height / source_height)
    offset_x = target_x + (target_width - source_width * scale) / 2
    offset_y = target_y + (target_height - source_height * scale) / 2
    reveal_edge = source_height * progress
    font_size = max(5, round(8 * scale))

    for row in root.findall(f".//{tag('text')}"):
        baseline = float(row.get("y"))
        if baseline > reveal_edge:
            continue
        x = float(row.get("x"))
        cursor = offset_x + x * scale
        for span in row.findall(tag("tspan")):
            run = span.text or ""
            opacity = float(span.get("opacity", "1"))
            rgb = color(span.get("fill", "#E6E6E6"))
            fill = tuple(round(channel * opacity) for channel in rgb)
            font = load_font(font_size)
            draw.text(
                (cursor, offset_y + baseline * scale),
                run,
                font=font,
                fill=fill,
                anchor="ls",
            )
            cursor += draw.textlength(run, font=font)


def render_frame(stats, progress):
    frame = Image.new("RGB", (WIDTH, HEIGHT), "#101112")
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle(
        (LEFT_X, LEFT_Y, LEFT_X + LEFT_WIDTH, LEFT_Y + LEFT_HEIGHT),
        radius=12,
        fill=PANEL,
        outline=BORDER,
        width=1,
    )
    draw.rounded_rectangle(
        (RIGHT_X, RIGHT_Y, RIGHT_X + RIGHT_WIDTH, RIGHT_Y + RIGHT_HEIGHT),
        radius=12,
        fill=PANEL,
        outline=BORDER,
        width=1,
    )
    draw_card(draw, stats)
    title_font = load_font(15)
    label_font = load_font(10)
    draw.text((24, 31), "GOKUL.VASAN // DEVELOPER PROFILE", font=title_font, fill=color(MAIN), anchor="ls")
    draw.text((1256, 31), "PORTFOLIO / 01", font=label_font, fill=color(SECONDARY), anchor="rs")
    draw.text(
        (LEFT_X + 18, LEFT_Y + 24),
        "PORTRAIT / GRAYSCALE ASCII",
        font=load_font(10),
        fill=color(HIGHLIGHT),
        anchor="ls",
    )
    draw.text(
        (LEFT_X + 18, LEFT_Y + 42),
        "TOP-TO-BOTTOM RECONSTRUCTION",
        font=load_font(8),
        fill=color(SECONDARY),
        anchor="ls",
    )
    draw_portrait(draw, progress)

    if progress < 1:
        image_y = LEFT_Y + 44
        image_height = LEFT_HEIGHT - 48
        line_y = image_y + 12 + (image_height - 12) * progress
        alpha = min(1.0, (1 - progress) / 0.08) * 0.75
        shade = round(80 + 110 * alpha)
        draw.line(
            (LEFT_X + 12, line_y, LEFT_X + LEFT_WIDTH - 12, line_y),
            fill=(shade, shade, shade),
            width=1,
        )
    return frame


def generate_dashboard_gif(stats):
    frame_count = 24
    frames = [
        render_frame(stats, index / (frame_count - 1))
        for index in range(frame_count)
    ]
    frames.append(frames[-1].copy())
    frames[0].save(
        "profile-dashboard.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[300] * frame_count + [2200],
        disposal=2,
        optimize=True,
    )


def main():
    stats = collect_stats()
    create_svg(stats, "info-card.svg")
    generate_dashboard_svg()
    generate_dashboard_gif(stats)
    print("Generated info-card.svg, profile-dashboard.svg, and profile-dashboard.gif.")


if __name__ == "__main__":
    main()
