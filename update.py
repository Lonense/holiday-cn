#!/usr/bin/env python3
"""Update holiday-cn data and generate ICS files."""

import json
import os
import uuid
from datetime import date, datetime, timedelta, tzinfo
from itertools import chain
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import requests
import bs4
from icalendar import Calendar, Event, Timezone, TimezoneStandard

# Constants
SEARCH_URL = "http://sousuo.gov.cn/s.htm"
PAPER_EXCLUDE = [
    "http://www.gov.cn/zhengce/content/2014-09/29/content_9102.htm",
    "http://www.gov.cn/zhengce/content/2015-02/09/content_9466.htm",
]
PAPER_INCLUDE = {
    2015: ["http://www.gov.cn/zhengce/content/2015-05/13/content_9742.htm"]
}

PRE_PARSED_PAPERS = {
    "http://www.gov.cn/zhengce/content/2015-05/13/content_9742.htm": [
        {
            "name": "抗日战争暨世界反法西斯战争胜利70周年纪念日",
            "date": date(2015, 9, 3),
            "isOffDay": True,
        },
        {
            "name": "抗日战争暨世界反法西斯战争胜利70周年纪念日",
            "date": date(2015, 9, 4),
            "isOffDay": True,
        },
        {
            "name": "抗日战争暨世界反法西斯战争胜利70周年纪念日",
            "date": date(2015, 9, 5),
            "isOffDay": True,
        },
        {
            "name": "抗日战争暨世界反法西斯战争胜利70周年纪念日",
            "date": date(2015, 9, 6),
            "isOffDay": False,
        },
    ]
}

CALENDAR_NAME = "中国法定节假日"
CALENDAR_DESCRIPTION = "中国法定节假日数据，自动每日抓取国务院公告。"
MAIN_CALENDAR_NAME = "节日补充"
MAIN_CALENDAR_DESCRIPTION = "补充节日数据"

__dirname__ = os.path.abspath(os.path.dirname(__file__))


class ChinaTimezone(tzinfo):
    """Timezone of china."""

    def tzname(self, dt):
        return "UTC+8"

    def utcoffset(self, dt):
        return timedelta(hours=8)

    def dst(self, dt):
        return timedelta()


def _file_path(*other: str) -> str:
    return os.path.join(__dirname__, *other)


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


def _cast_int(value: Optional[str]) -> Optional[int]:
    return int(value) if value else None


def _raise_for_status_200(resp: requests.Response):
    resp.raise_for_status()
    if resp.status_code != 200:
        raise requests.HTTPError(
            "request failed: %d: %s" % (resp.status_code, resp.request.url),
            response=resp,
        )


def _create_event(
    event_name: str,
    start: Union[date, datetime],
    end: Union[date, datetime],
    description: Optional[str] = None,
    is_off_day: Optional[bool] = None,
) -> Event:
    """Create an iCalendar event."""
    event = Event()
    event.add("SUMMARY", event_name)
    event.add("DTSTART", start)
    event.add("DTEND", end)
    event.add("DTSTAMP", start)

    if description:
        event.add("DESCRIPTION", description)

    if is_off_day is not None:
        event.add(
            "X-APPLE-SPECIAL-DAY", "WORK-HOLIDAY" if not is_off_day else "HOLIDAY"
        )

    event["UID"] = str(uuid.uuid4())
    return event


def _create_calendar(name: str, description: str) -> Calendar:
    """Create a new iCalendar calendar."""
    cal = Calendar()
    cal.add("X-WR-CALNAME", name)
    cal.add("X-WR-CALDESC", description)
    cal.add("VERSION", "2.0")
    cal.add("METHOD", "PUBLISH")
    cal.add("CLASS", "PUBLIC")
    cal.add_component(_create_timezone())
    return cal


def _iter_date_ranges(days: Sequence[dict]) -> Iterable[Tuple[dict, dict]]:
    """Iterate through date ranges with same holiday status."""
    if len(days) == 0:
        return

    if len(days) == 1:
        yield days[0], days[0]
        return

    fr, to = days[0], days[0]
    for cur in days[1:]:
        if (_cast_date(cur["date"]) - _cast_date(to["date"])).days == 1 and cur[
            "isOffDay"
        ] == to["isOffDay"]:
            to = cur
        else:
            yield fr, to
            fr, to = cur, cur
    yield fr, to


def get_paper_urls(year: int) -> List[str]:
    """Find year related paper urls.

    Args:
        year (int): eg. 2018

    Returns:
        List[str]: Urls， newlest first.
    """
    resp = requests.get(
        SEARCH_URL,
        params={
            "t": "paper",
            "advance": "true",
            "title": year,
            "q": "假期",
            "pcodeJiguan": "国办发明电",
            "puborg": "国务院办公厅",
        },
    )
    _raise_for_status_200(resp)
    ret = re.findall(
        r'<li class="res-list".*?<a href="(.+?)".*?</li>', resp.text, flags=re.S
    )
    ret = [i for i in ret if i not in PAPER_EXCLUDE]
    ret += PAPER_INCLUDE.get(year, [])
    ret.sort()
    if not ret and date.today().year >= year:
        raise RuntimeError("could not found papers for %d" % year)
    return ret


def get_paper(url: str) -> str:
    """Extract paper text from url.

    Args:
        url (str): Paper url.

    Returns:
        str: Extracted paper text.
    """
    assert re.match(
        r"http://www.gov.cn/zhengce/content/\d{4}-\d{2}/\d{2}/content_\d+.htm", url
    ), "Site changed, need human verify"

    response = requests.get(url)
    _raise_for_status_200(response)
    response.encoding = "utf-8"
    soup = bs4.BeautifulSoup(response.text, features="html.parser")
    container = soup.find("td", class_="b12c")
    assert container, f"Can not get paper container from url: {url}"
    ret = container.get_text().replace("\u3000\u3000", "\n")
    assert ret, f"Can not get paper content from url: {url}"
    return ret


def get_rules(paper: str) -> Iterable[Tuple[str, str]]:
    """Extract rules from paper.

    Args:
        paper (str): Paper text

    Raises:
        NotImplementedError: When find no rules.

    Returns:
        Iterable[Tuple[str, str]]: (name, description)
    """
    lines: list = paper.splitlines()
    lines = sorted(set(lines), key=lines.index)
    count = 0
    for i in chain(get_normal_rules(lines), get_patch_rules(lines)):
        count += 1
        yield i
    if not count:
        raise NotImplementedError(lines)


def get_normal_rules(lines: Iterable[str]) -> Iterable[Tuple[str, str]]:
    """Get normal holiday rule for a year

    Args:
        lines (Iterable[str]): paper content

    Returns:
        Iterable[Tuple[str, str]]: (name, description)
    """
    for i in lines:
        match = re.match(r"[一二三四五六七八九十]、(.+?)：(.+)", i)
        if match:
            yield match.groups()


def get_patch_rules(lines: Iterable[str]) -> Iterable[Tuple[str, str]]:
    """Get holiday patch rule for existed holiday

    Args:
        lines (Iterable[str]): paper content

    Returns:
        Iterable[Tuple[str, str]]: (name, description)
    """
    name = None
    for i in lines:
        match = re.match(r".*\d+年([^和、]{2,})(?:假期|放假).*安排", i)
        if match:
            name = match.group(1)
        if not name:
            continue
        match = re.match(r"^[一二三四五六七八九十]、(.+)$", i)
        if not match:
            continue
        description = match.group(1)
        if re.match(r".*\d+月\d+日.*", description):
            yield name, description


class DescriptionParser:
    """Parser for holiday shift description."""

    def __init__(self, description: str, year: int):
        self.description = description
        self.year = year
        self.date_history = list()

    def parse(self) -> Iterable[dict]:
        """Generator for description parsing result.

        Args:
            year (int): Context year
        """
        del self.date_history[:]
        for i in re.split("[，。；]", self.description):
            for j in SentenceParser(self, i).parse():
                yield j

        if not self.date_history:
            raise NotImplementedError(self.description)

    def get_date(self, year: Optional[int], month: Optional[int], day: int) -> date:
        """Get date in context.

        Args:
            year (Optional[int]): year
            month (int): month
            day (int): day

        Returns:
            date: Date result
        """
        assert day, "No day specified"

        # Special case: month inherit
        if month is None:
            month = self.date_history[-1].month

        # Special case: 12 month may mean previous year
        if (
            year is None
            and month == 12
            and self.date_history
            and max(self.date_history) < date(year=self.year, month=2, day=1)
        ):
            year = self.year - 1

        year = year or self.year
        return date(year=year, month=month, day=day)


class SentenceParser:
    """Parser for holiday shift description sentence."""

    special_cases = {
        "延长2020年春节假期至2月2日（农历正月初九": [
            {"date": date(2020, 1, 31), "isOffDay": True},
            {"date": date(2020, 2, 1), "isOffDay": True},
            {"date": date(2020, 2, 2), "isOffDay": True},
        ],
    }

    def __init__(self, parent: DescriptionParser, sentence):
        self.parent = parent
        self.sentence = sentence

    def extract_dates(self, text: str) -> Iterable[date]:
        """Extract date from text.

        Args:
            text (str): Text to extract

        Returns:
            Iterable[date]: Extracted dates.
        """
        count = 0
        text = text.replace("(", "（").replace(")", "）")
        for i in chain(
            *(method(self, text) for method in self.date_extraction_methods)
        ):
            count += 1
            is_seen = i in self.parent.date_history
            self.parent.date_history.append(i)
            if is_seen:
                continue
            yield i

        if not count:
            raise NotImplementedError(text)

    def _extract_dates_1(self, value: str) -> Iterable[date]:
        match = re.findall(r"(?:(\d+)年)?(?:(\d+)月)?(\d+)日", value)
        for groups in match:
            groups = [_cast_int(i) for i in groups]
            assert len(groups) == 3, groups
            yield self.parent.get_date(year=groups[0], month=groups[1], day=groups[2])

    def _extract_dates_2(self, value: str) -> Iterable[date]:
        match = re.findall(
            r"(?:(\d+)年)?(?:(\d+)月)?(\d+)日(?:至|-|—)(?:(\d+)年)?(?:(\d+)月)?(\d+)日",
            value,
        )
        for groups in match:
            groups = [_cast_int(i) for i in groups]
            assert len(groups) == 6, groups
            start = self.parent.get_date(year=groups[0], month=groups[1], day=groups[2])
            end = self.parent.get_date(year=groups[3], month=groups[4], day=groups[5])
            for i in range((end - start).days + 1):
                yield start + timedelta(days=i)

    def _extract_dates_3(self, value: str) -> Iterable[date]:
        match = re.findall(
            r"(?:(\d+)年)?(?:(\d+)月)?(\d+)日(?:（[^）]+）)?"
            r"(?:、(?:(\d+)年)?(?:(\d+)月)?(\d+)日(?:（[^）]+）)?)+",
            value,
        )
        for groups in match:
            groups = [_cast_int(i) for i in groups]
            assert not (len(groups) % 3), groups
            for i in range(0, len(groups), 3):
                yield self.parent.get_date(
                    year=groups[i], month=groups[i + 1], day=groups[i + 2]
                )

    date_extraction_methods = [_extract_dates_1, _extract_dates_2, _extract_dates_3]

    def parse(self) -> Iterable[dict]:
        """Parse days with memory

        Returns:
            Iterable[dict]: Days without name field.
        """
        for method in self.parsing_methods:
            for i in method(self):
                yield i

    def _parse_rest_1(self):
        match = re.match(r"(.+)(放假|补休|调休|公休)+(?:\d+天)?$", self.sentence)
        if match:
            for i in self.extract_dates(match.group(1)):
                yield {"date": i, "isOffDay": True}

    def _parse_work_1(self):
        match = re.match("(.+)上班$", self.sentence)
        if match:
            for i in self.extract_dates(match.group(1)):
                yield {"date": i, "isOffDay": False}

    def _parse_shift_1(self):
        match = re.match("(.+)调至(.+)", self.sentence)
        if match:
            for i in self.extract_dates(match.group(1)):
                yield {"date": i, "isOffDay": False}
            for i in self.extract_dates(match.group(2)):
                yield {"date": i, "isOffDay": True}

    def _parse_special(self):
        for i in self.special_cases.get(self.sentence, []):
            yield i

    parsing_methods = [
        _parse_rest_1,
        _parse_work_1,
        _parse_shift_1,
        _parse_special,
    ]


def parse_paper(year: int, url: str) -> Iterable[dict]:
    """Parse one paper

    Args:
        year (int): Year
        url (str): Paper url

    Returns:
        Iterable[dict]: Days
    """
    if url in PRE_PARSED_PAPERS:
        yield from PRE_PARSED_PAPERS[url]
        return
    paper = get_paper(url)
    rules = get_rules(paper)
    ret = (
        {"name": name, **i}
        for name, description in rules
        for i in DescriptionParser(description, year).parse()
    )
    try:
        for i in ret:
            yield i
    except NotImplementedError as ex:
        raise RuntimeError("Can not parse paper", url) from ex


def fetch_holiday(year: int) -> dict:
    """Fetch holiday data for a specific year."""
    papers = get_paper_urls(year)

    days = dict()

    for k in (j for i in papers for j in parse_paper(year, i)):
        days[k["date"]] = k

    return {
        "year": year,
        "papers": papers,
        "days": sorted(days.values(), key=lambda x: x["date"]),
    }


def generate_ics(days: Sequence[dict], filename: str) -> None:
    """Generate ics from days."""
    cal = _create_calendar(CALENDAR_NAME, CALENDAR_DESCRIPTION)
    days = sorted(days, key=lambda x: x["date"])

    for fr, to in _iter_date_ranges(days):
        start = _cast_date(fr["date"])
        end = _cast_date(to["date"]) + timedelta(days=1)

        name = fr["name"] + "(休)"
        if not fr["isOffDay"]:
            name = fr["name"] + "(班)"
        cal.add_component(_create_event(name, start, end, is_off_day=fr["isOffDay"]))

    with open(filename, "wb") as f:
        f.write(cal.to_ical())


def generate_main_ics(days: Sequence[dict], filename: str, nowyear: int) -> None:
    """Generate main ics with additional holidays."""
    cal = _create_calendar(MAIN_CALENDAR_NAME, MAIN_CALENDAR_DESCRIPTION)

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


def update_data(year: int) -> Iterable[str]:
    """Update and store data for a year."""
    json_filename = _file_path(f"{year}.json")
    ics_filename = _file_path(f"{year}.ics")

    with open(json_filename, "w", encoding="utf-8", newline="\n") as f:
        data = fetch_holiday(year)
        json.dump(
            dict(
                (
                    (
                        "$schema",
                        "https://raw.githubusercontent.com/Lonense/holiday-cn/master/schema.json",
                    ),
                    (
                        "$id",
                        f"https://raw.githubusercontent.com/Lonense/holiday-cn/master/{year}.json",
                    ),
                    *data.items(),
                )
            ),
            f,
            indent=4,
            ensure_ascii=False,
            cls=CustomJSONEncoder,
        )

    yield json_filename
    generate_ics(data["days"], ics_filename)
    yield ics_filename


def update_main_ics(fr_year: int, to_year: int, nowyear: int) -> str:
    """Update main ICS file with holidays from all years."""
    all_days = []
    for year in range(fr_year, to_year + 1):
        filename = _file_path(f"{year}.json")
        if not os.path.isfile(filename):
            continue
        try:
            with open(filename, "r", encoding="utf8") as inf:
                data = json.loads(inf.read())
                all_days.extend(data.get("days", []))
        except (json.JSONDecodeError, IOError):
            continue

    filename = _file_path("holiday-cn.ics")
    generate_main_ics(all_days, filename, nowyear)
    return filename


class CustomJSONEncoder(json.JSONEncoder):
    """Custom json encoder."""

    def default(self, o):
        # pylint:disable=method-hidden
        if isinstance(o, date):
            return o.isoformat()

        return super().default(o)


def main():
    """Main function to update holiday data."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all years since 2007, default is this year and next year",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="create new release if repository data is not up to date",
    )
    args = parser.parse_args()

    now = datetime.now(ChinaTimezone())
    is_release = args.release

    filenames = []

    if args.all:
        for year in range(2007, now.year + 2):
            try:
                filenames += list(update_data(year))
            except Exception as e:
                print(f"Error updating {year}: {e}")
    else:
        for year in range(now.year, now.year + 2):
            try:
                filenames += list(update_data(year))
            except Exception as e:
                print(f"Error updating {year}: {e}")

    # Update main ICS
    filenames.append(update_main_ics(now.year - 3, now.year + 1, now.year))


if __name__ == "__main__":
    main()
