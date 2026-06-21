import re

def clean(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def to_seconds(ts: str) -> int:
    parts = list(map(int, ts.split(":")))

    if len(parts) == 2:
        m, s = parts
        return m * 60 + s

    h, m, s = parts
    return h * 3600 + m * 60 + s


def to_hms(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    return f"{h:02}:{m:02}:{s:02}"


def parse_tracks(text: str, total_duration: int):
    tracks = []

    for line in text.splitlines():
        m = re.match(
            r"^\s*((?:\d{1,2}:)?\d{1,2}:\d{2})\s*[-–—]?\s*(.+?)\s*$",
            line
        )

        if not m:
            continue

        tracks.append({
            "start": to_seconds(m.group(1)),
            "title": clean(m.group(2)),
        })

    result = []

    for i, track in enumerate(tracks):
        start = track["start"]

        if i + 1 < len(tracks):
            end = tracks[i + 1]["start"]
        else:
            end = total_duration

        result.append({
            "title": track["title"],
            "start": to_hms(start),
            "end": to_hms(end),
        })

    return result

#with open("codes", 'r') as f:
#    s = parse_tracks(f.read(), 1841)
#print(s)