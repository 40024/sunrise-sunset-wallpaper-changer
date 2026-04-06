#!/usr/bin/env python3

from datetime import datetime, time
from zoneinfo import ZoneInfo
import subprocess
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


def now_period(periods, datetime_obj: datetime) -> str:
    """
    Returns one of the following depending on time
        "dawn" "day" "dusk" "night"
    """
    time = datetime_obj.time()

    for name, (start, end) in periods.items():
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


def get_current_wallpapers() -> list[str]:
    """
    Monitors may have their own wallpaper
    So we get a list of wallpapers for each monitor
    """
    stdout = subprocess.run(["awww", "query"], capture_output=True, text=True).stdout
    lines = stdout.splitlines()
    return [line.split(" ")[-1] for line in lines]


def set_wallpaper(path: str) -> int:
    cmd = ["/usr/bin/awww", "img", path]
    res = subprocess.run(cmd, check=False)
    return res.returncode


def get_wallpaper_filename(wallpaper_path: str) -> str:
    return wallpaper_path.split("/")[-1]


def main():
    # TODO cache api call, currently made every MINUTE
    # TODO and fall back to sensible defaults if offline
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

    # TODO should've just been an object
    # Define periods intervals
    PERIODS = {
        "dawn":  (gse(api_info, "first_light"), gse(api_info, "sunrise")),
        "day":   (gse(api_info, "sunrise"),     gse(api_info, "golden_hour")),
        "dusk":  (gse(api_info, "golden_hour"), gse(api_info, "sunset")),
        "night": (gse(api_info, "sunset"),      gse(api_info, "first_light")),
    }

    TZ = ZoneInfo("America/Los_Angeles")

    datetime_obj = datetime.now(TZ)
    period = now_period(PERIODS, datetime_obj)

    expected_wallpaper = WALLPAPERS.get(period, None)

    if not expected_wallpaper:
        logging.error(f"No wallpaper configured for period {period}")
        return 2

    current_wallpapers = get_current_wallpapers()

    for current_wallpaper in current_wallpapers:
        wallpaper_filename = get_wallpaper_filename(expected_wallpaper)

        if current_wallpaper != expected_wallpaper:
            print(f"Changing wallpaper to {wallpaper_filename} from {get_wallpaper_filename(current_wallpaper)}")
            return_code = set_wallpaper(expected_wallpaper)

            if return_code != 0:
                logging.error(f"Err with {return_code}")
        else:
            print(f"Wallpaper {wallpaper_filename} matches what it should be for period {period}")


if __name__ == "__main__":
    main()
