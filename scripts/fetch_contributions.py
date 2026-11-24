from urllib.request import Request, urlopen
from html.parser import HTMLParser
from pathlib import Path
import json
import re

USER = "gokul307-tech"
URL = f"https://github.com/users/{USER}/contributions"

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []
        self.days_by_id = {}
        self.active_day = None
        self.tooltip_text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and a.get("data-date"):
            day = {"date": a["data-date"], "level": int(a.get("data-level", "0"))}
            self.days.append(day)
            if a.get("id"):
                self.days_by_id[a["id"]] = day
        elif tag == "tool-tip" and a.get("for") in self.days_by_id:
            self.active_day = self.days_by_id[a["for"]]
            self.tooltip_text = []

    def handle_data(self, data):
        if self.active_day is not None:
            self.tooltip_text.append(data)

    def handle_endtag(self, tag):
        if tag != "tool-tip" or self.active_day is None:
            return
        tooltip = " ".join(self.tooltip_text).strip()
        if "no contributions" in tooltip.lower():
            self.active_day["count"] = 0
        else:
            match = re.search(r"\b(\d+)\s+contributions?\b", tooltip, re.IGNORECASE)
            if match:
                self.active_day["count"] = int(match.group(1))
        self.active_day = None
        self.tooltip_text = []

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
    counted_days = sum("count" in day for day in parser.days)
    if counted_days == len(parser.days):
        print(f"Saved {len(parser.days)} contribution days; {sum(day['count'] for day in parser.days)} contributions.")
    else:
        print(f"Saved {len(parser.days)} contribution days; exact contribution counts unavailable.")

if __name__ == "__main__":
    main()
