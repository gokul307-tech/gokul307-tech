from urllib.request import Request, urlopen
from html.parser import HTMLParser
from pathlib import Path
import json

USER = "gokul307-tech"
URL = f"https://github.com/users/{USER}/contributions"

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and a.get("data-date"):
            self.days.append({"date": a["data-date"], "level": int(a.get("data-level", "0"))})

def main():
    req = Request(URL, headers={"User-Agent": "Mozilla/5.0 profile-readme-generator"})
    with urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", "replace")
    parser = CalendarParser()
    parser.feed(html)
    if not parser.days:
        raise RuntimeError("Could not parse GitHub contribution calendar; GitHub may have changed its markup.")
    Path("data").mkdir(exist_ok=True)
    Path("data/contributions.json").write_text(json.dumps(parser.days, indent=2), encoding="utf-8")
    print(f"Saved {len(parser.days)} contribution days.")

if __name__ == "__main__":
    main()
