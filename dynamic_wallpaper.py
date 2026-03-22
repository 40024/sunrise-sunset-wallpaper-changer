#!/usr/bin/env python3

from datetime import datetime, time
from zoneinfo import ZoneInfo
import subprocess
import sys
from pathlib import Path
import requests
import json
import logging


logging.basicConfig(level=logging.WARNING)


def gse(api_info: dict, event_wanted: str) -> time:
    """
    Retrieve solar time for event
    Args:
        event_wanted: Specific solar event to retrieve time for
    Returns:
        parsed time objecttime: Parsed time for the specified solar event
    Raises:
        ValueError: If an invalid event is provided
    """

    if event_wanted not in ["first_light", "dawn", "sunrise", "golden_hour", "sunset"]:
        raise ValueError("Invalid solar event")

    time_of_day = api_info["results"][event_wanted]
    hours, minutes, _seconds_meridiem = time_of_day.split(":")
    seconds, meridiem = _seconds_meridiem[:2], _seconds_meridiem[3:]

    if meridiem == "PM":
        logging.debug(f"PM meridiem detected for {event_wanted}")
        hours = int(hours) + 12
    else:
        logging.debug(f"AM meridiem detected for {event_wanted}")

    time_obj = time(int(hours), int(minutes), int(seconds))
    logging.info(f"{event_wanted} {time_obj}")

    return time_obj


def now_period(PERIODS, datetime_obj: datetime) -> str:
    time = datetime_obj.time()
    for name, (start, end) in PERIODS.items():
        # Check for midnight
        if start <= end:
            if start <= time < end:
                logging.debug(f"Time {time} detected as: {name}")
                return name
        # Wrapping midnight
        else:
            if time >= start or time < end:
                logging.debug(f"Midnight wrap Time {time} detected as: {name}")
                return name
    return "night"


def read_last(STATE_FILE) -> str | None:
    return STATE_FILE.read_text().strip()


def write_last(STATE_FILE, path: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(path)


def set_wallpaper(path: str) -> int:
    cmd = ["/usr/bin/swww", "img", path]
    res = subprocess.run(cmd, check=False)
    return res.returncode


def main():
    # TODO cache api call, currently made every MINUTE
    r = requests.get(
        "https://api.sunrisesunset.io/json?lat=37.3346&lng=-122.0090&timezone=lax"
    )
    api_info = json.loads(r.content)

    # Map period names to image paths (full paths)
    WALLPAPERS = {
        "dawn":  "/home/v/Pictures/Wallpapers/Tahoe/26-Tahoe-Beach-Dawn.png",
        "day":   "/home/v/Pictures/Wallpapers/Tahoe/26-Tahoe-Beach-Day.png",
        "dusk":  "/home/v/Pictures/Wallpapers/Tahoe/26-Tahoe-Beach-Dusk.png",
        "night": "/home/v/Pictures/Wallpapers/Tahoe/26-Tahoe-Beach-Night.png",
    }

    # Define periods intervals
    PERIODS = {
        "dawn":  (gse(api_info, "first_light"), gse(api_info, "sunrise")),
        "day":   (gse(api_info, "sunrise"),     gse(api_info, "golden_hour")),
        "dusk":  (gse(api_info, "golden_hour"), gse(api_info, "sunset")),
        "night": (gse(api_info, "sunset"),      gse(api_info, "first_light")),
    }

    TZ = ZoneInfo("America/Los_Angeles")
    STATE_FILE = Path.home() / ".cache" / "dynamic_wallpaper_last"

    datetime_obj = datetime.now(TZ)
    period = now_period(PERIODS, datetime_obj)

    wallpaper = WALLPAPERS.get(period)
    if not wallpaper:
        logging.error(f"No wallpaper configured for period {period}")
        return 2

    last = read_last(STATE_FILE)
    if last == period:
        print(
            "Dynamic wallpaper ran, but current wallpaper matches what it should be for period, not changing wallpaper"
        )
        return 0
    return_code = set_wallpaper(wallpaper)
    if return_code == 0:
        write_last(STATE_FILE, period)
    else:
        sys.exit(return_code)


if __name__ == "__main__":
    main()
