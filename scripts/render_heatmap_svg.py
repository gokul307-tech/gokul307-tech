import json
from pathlib import Path
from xml.sax.saxutils import escape

COLORS = ["#252729", "#414447", "#62666a", "#92969a", "#d5d5d5"]

def main():
    days = json.loads(Path("data/contributions.json").read_text(encoding="utf-8"))[-364:]
    cells = []
    for i, day in enumerate(days):
        x, y = 24+(i%52)*16, 52+(i//52)*14
        level = max(0, min(4, int(day.get("level", 0))))
        title = escape(f'{day["date"]}: contribution level {level}')
        cells.append(f'<rect x="{x}" y="{y}" width="11" height="9" rx="2" fill="{COLORS[level]}"><title>{title}</title></rect>')
    legend = "".join(f'<rect x="{60+i*17}" y="136" width="11" height="9" rx="2" fill="{c}"/>' for i,c in enumerate(COLORS))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="155" viewBox="0 0 900 155">
<rect width="900" height="155" rx="14" fill="#17191B" stroke="#454545"/>
<text x="24" y="30" fill="#D5D5D5" font-family="monospace" font-size="15">GitHub contribution activity · last 52 weeks</text>
{"".join(cells)}
<text x="24" y="145" fill="#A1A1A1" font-family="monospace" font-size="10">Less</text>{legend}
<text x="155" y="145" fill="#A1A1A1" font-family="monospace" font-size="10">More</text></svg>'''
    Path("contrib-heatmap.svg").write_text(svg, encoding="utf-8")

if __name__ == "__main__":
    main()
