import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


USER = "gokul307-tech"
CARD_WIDTH = 700
CARD_HEIGHT = 560
COLORS = {
    "background": "#17191B",
    "main": "#E6E6E6",
    "secondary": "#A1A1A1",
    "border": "#454545",
    "highlight": "#D5D5D5",
}


def get_json(url):
    request = Request(
        url,
        headers={
            "User-Agent": "gokul307-tech-profile-dashboard",
            "Accept": "application/vnd.github+json",
        },
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def collect_stats():
    stats = {}
    try:
        profile = get_json(f"https://api.github.com/users/{USER}")
        stats.update(
            repositories=profile["public_repos"],
            followers=profile["followers"],
            following=profile["following"],
        )
    except (HTTPError, URLError, TimeoutError, KeyError) as error:
        print(f"GitHub profile statistics unavailable; omitting them: {error}", file=sys.stderr)

    try:
        repositories = get_json(
            f"https://api.github.com/users/{USER}/repos?per_page=100"
        )
        stats["stars"] = sum(
            int(repository.get("stargazers_count", 0))
            for repository in repositories
        )
    except (HTTPError, URLError, TimeoutError, TypeError, ValueError) as error:
        print(f"GitHub star total unavailable; omitting it: {error}", file=sys.stderr)

    contributions_file = Path("data/contributions.json")
    if contributions_file.exists():
        days = json.loads(contributions_file.read_text(encoding="utf-8"))
        if days and all(isinstance(day.get("count"), int) for day in days):
            stats["contributions"] = sum(day["count"] for day in days)
        else:
            print(
                "Exact contribution total unavailable; omitting it from the card.",
                file=sys.stderr,
            )
    return stats


def card_items(stats):
    items = []

    def text(x, y, value, size=12, color="main", anchor="start", weight="normal"):
        items.append(
            {
                "type": "text",
                "x": x,
                "y": y,
                "text": value,
                "size": size,
                "fill": COLORS[color],
                "anchor": anchor,
                "weight": weight,
            }
        )

    def line(x1, y1, x2, y2, color="border", width=1):
        items.append(
            {
                "type": "line",
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "stroke": COLORS[color],
                "width": width,
            }
        )

    text(28, 34, "GOKUL.VASAN // DEVELOPER PROFILE", 17, "main", weight="bold")
    text(28, 55, "Aspiring Software Developer  /  Puducherry, India", 11, "secondary")
    text(672, 34, "PUBLIC PROFILE", 9, "secondary", anchor="end")
    line(28, 72, 672, 72)

    text(28, 96, "IDENTITY", 10, "highlight", weight="bold")
    text(28, 120, "NAME", 9, "secondary")
    text(142, 120, "Gokul Vasan", 12)
    text(28, 142, "ROLE", 9, "secondary")
    text(142, 142, "Aspiring Software Developer", 12)
    text(28, 164, "EDUCATION", 9, "secondary")
    text(142, 164, "B.Tech Information Technology  /  Year 2", 12)
    line(28, 181, 672, 181)

    text(28, 204, "TECHNICAL PROFILE", 10, "highlight", weight="bold")
    text(28, 228, "LANGUAGES", 9, "secondary")
    text(142, 228, "Java  ·  Python  ·  SQL  ·  JavaScript", 11)
    text(28, 250, "FRONTEND", 9, "secondary")
    text(142, 250, "HTML  ·  CSS  ·  Next.js", 11)
    text(28, 272, "BACKEND / DATA", 9, "secondary")
    text(142, 272, "FastAPI  ·  PostgreSQL", 11)
    text(28, 294, "TOOLS", 9, "secondary")
    text(142, 294, "Git  ·  GitHub  ·  VS Code", 11)
    line(28, 311, 672, 311)

    text(28, 334, "CURRENT PROJECTS", 10, "highlight", weight="bold")
    text(28, 357, "SAGE AI", 10, "main", weight="bold")
    text(142, 357, "Personal AI assistant", 11, "secondary")
    text(28, 380, "FEASTYMAP", 10, "main", weight="bold")
    text(142, 380, "Location-based outing and itinerary planning", 11, "secondary")
    line(28, 397, 672, 397)

    text(28, 420, "INTERESTS", 10, "highlight", weight="bold")
    text(142, 420, "Artificial Intelligence  ·  Full-Stack Development  ·  Software Engineering", 10)
    line(28, 439, 672, 439)

    metrics = [
        ("CONTRIB.", stats.get("contributions")),
        ("REPOS", stats.get("repositories")),
        ("STARS", stats.get("stars")),
        ("FOLLOWERS", stats.get("followers")),
        ("FOLLOWING", stats.get("following")),
    ]
    metrics = [(label, value) for label, value in metrics if value is not None]
    width = 644 / max(len(metrics), 1)
    for index, (label, value) in enumerate(metrics):
        center = 28 + width * (index + 0.5)
        text(center, 461, label, 8, "secondary", anchor="middle")
        text(center, 486, f"{value:,}", 16, "main", anchor="middle", weight="bold")
        if index:
            x = 28 + width * index
            line(x, 448, x, 494, width=0.7)
    line(28, 505, 672, 505)
    text(28, 535, "CONTACT", 9, "secondary")
    text(142, 535, "gokulavasan307@gmail.com", 11, "highlight")
    text(672, 535, f"github.com/{USER}", 9, "secondary", anchor="end")
    return items


def item_to_svg(item):
    if item["type"] == "line":
        return (
            f'<line x1="{item["x1"]}" y1="{item["y1"]}" '
            f'x2="{item["x2"]}" y2="{item["y2"]}" '
            f'stroke="{item["stroke"]}" stroke-width="{item["width"]}"/>'
        )
    return (
        f'<text x="{item["x"]}" y="{item["y"]}" fill="{item["fill"]}" '
        f'font-size="{item["size"]}" text-anchor="{item["anchor"]}" '
        f'font-weight="{item["weight"]}">{escape(item["text"])}</text>'
    )


def create_svg(stats, output_path="info-card.svg"):
    contents = "\n".join(item_to_svg(item) for item in card_items(stats))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" role="img" aria-labelledby="card-title card-description">
<title id="card-title">Gokul Vasan developer information</title>
<desc id="card-description">Developer profile, skills, projects, interests, and current public GitHub statistics.</desc>
<rect id="card-background" x="0.5" y="0.5" width="{CARD_WIDTH - 1}" height="{CARD_HEIGHT - 1}" rx="12" fill="{COLORS['background']}" stroke="{COLORS['border']}"/>
<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
{contents}
</g>
</svg>
'''
    Path(output_path).write_text(svg, encoding="utf-8")


def main():
    create_svg(collect_stats())
    print("Generated info-card.svg.")


if __name__ == "__main__":
    main()
