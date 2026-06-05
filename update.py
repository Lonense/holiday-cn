#!/usr/bin/env python3
"""Generate supplementary holiday calendar for China."""

import uuid
from datetime import date, datetime, timedelta, tzinfo
from typing import Optional, Union

from icalendar import Calendar, Event, Timezone, TimezoneStandard

CALENDAR_NAME = "节日补充"
CALENDAR_DESCRIPTION = "补充苹果日历未包含的节日数据"


class ChinaTimezone(tzinfo):
    """Timezone of china."""

    def tzname(self, dt):
        return "UTC+8"

    def utcoffset(self, dt):
        return timedelta(hours=8)

    def dst(self, dt):
        return timedelta()


def _create_timezone():
    tz = Timezone()
    tz.add("TZID", "Asia/Shanghai")

    tz_standard = TimezoneStandard()
    tz_standard.add("DTSTART", datetime(1970, 1, 1))
    tz_standard.add("TZOFFSETFROM", timedelta(hours=8))
    tz_standard.add("TZOFFSETTO", timedelta(hours=8))

    tz.add_component(tz_standard)
    return tz


def _cast_date(v: Union[str, date]) -> date:
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return date.fromisoformat(v)
    raise NotImplementedError("can not convert to date: %s" % v)


def _create_event(
    event_name: str,
    start: Union[date, datetime],
    end: Union[date, datetime],
    description: Optional[str] = None,
) -> Event:
    """Create an iCalendar event."""
    event = Event()
    event.add("SUMMARY", event_name)
    event.add("DTSTART", start)
    event.add("DTEND", end)
    event.add("DTSTAMP", start)

    if description:
        event.add("DESCRIPTION", description)

    event["UID"] = str(uuid.uuid4())
    return event


def generate_ics(filename: str, nowyear: int) -> None:
    """Generate supplementary holiday ICS file."""
    cal = Calendar()
    cal.add("X-WR-CALNAME", CALENDAR_NAME)
    cal.add("X-WR-CALDESC", CALENDAR_DESCRIPTION)
    cal.add("VERSION", "2.0")
    cal.add("METHOD", "PUBLISH")
    cal.add("CLASS", "PUBLIC")
    cal.add_component(_create_timezone())

    # Collect all events first, then sort by date
    all_events = []

    for year in range(nowyear - 3, nowyear + 2):
        # Fixed date holidays
        holidays = [
            ("情人节", "%d-02-14"),
            ("植树节", "%d-03-12"),
            ("愚人节", "%d-04-01"),
            ("世界地球日", "%d-04-22"),
            ("抗日战争胜利纪念日", "%d-09-03", "抗日战争胜利%d周年" % (year - 1945)),
            ("教师节", "%d-09-10"),
            ("国耻日", "%d-09-18", "九·一八事变 1931年9月18日"),
            ("辛亥革命纪念日", "%d-10-10", "辛亥革命%d周年" % (year - 1911)),
            ("一二·九运动纪念日", "%d-12-09", "一二·九运动%d周年" % (year - 1935)),
            ("南京大屠杀纪念日", "%d-12-13", "南京大屠杀%d周年" % (year - 1937)),
            ("平安夜", "%d-12-24"),
            ("圣诞节", "%d-12-25"),
        ]

        for item in holidays:
            name = item[0]
            date_pattern = item[1]
            description = item[2] if len(item) > 2 else None
            start = _cast_date(date_pattern % year)
            all_events.append((start, name, start, start, description))

        # Mother's Day (second Sunday in May)
        may_first = _cast_date("%d-05-01" % year)
        mother_day = may_first + timedelta(days=(6 - may_first.weekday()) % 7 + 7)
        all_events.append((mother_day, "母亲节", mother_day, mother_day, None))

        # Father's Day (third Sunday in June)
        june_first = _cast_date("%d-06-01" % year)
        father_day = june_first + timedelta(days=(6 - june_first.weekday()) % 7 + 14)
        all_events.append((father_day, "父亲节", father_day, father_day, None))

        # Lunar holidays
        try:
            from zhdate import ZhDate

            lunar_holidays = [
                ("龙抬头", 2, 2),
                ("上巳节", 3, 3),
                ("中元节", 7, 15),
                ("下元节", 10, 15),
                ("腊八节", 12, 8),
            ]

            for name, month, day in lunar_holidays:
                start = _cast_date(ZhDate(year, month, day).to_datetime().date())
                all_events.append((start, name, start, start, None))
        except ImportError:
            # zhdate not available, skip lunar holidays
            pass

    # Sort all events by date
    all_events.sort(key=lambda x: x[0])

    # Add sorted events to calendar
    for _, name, start, end, description in all_events:
        cal.add_component(_create_event(name, start, end, description))

    with open(filename, "wb") as f:
        f.write(cal.to_ical())


def main():
    """Main function to generate holiday calendar."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Generate supplementary holiday calendar"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="holiday-cn.ics",
        help="Output ICS file path (default: holiday-cn.ics)",
    )
    args = parser.parse_args()

    now = datetime.now(ChinaTimezone())
    generate_ics(args.output, now.year)


if __name__ == "__main__":
    main()
