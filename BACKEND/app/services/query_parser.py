import re
from datetime import datetime

from dateparser import parse as parse_date # type: ignore
from dateparser.search import search_dates # type: ignore

from app.schemas import SearchCriteria


TIME_SLOT_MAP = {
    "morning": "09:00",
    "afternoon": "14:00",
    "evening": "18:00",
    "night": "21:00",
    "noon": "12:00",
}


class QueryParserService:
    def parse(self, query: str) -> SearchCriteria:
        normalized_query = " ".join(query.strip().split())
        route = self._extract_route(normalized_query)
        if route is None:
            raise ValueError("Please specify the route in the format 'from CITY to CITY'.")

        travel_date = self._extract_date(normalized_query)
        if travel_date is None:
            raise ValueError("Please include a travel date so I can compare flights accurately.")

        requested_time_slot, requested_time = self._extract_time(normalized_query)
        budget = self._extract_budget(normalized_query)
        flexible_timing = self._is_flexible(normalized_query, requested_time_slot, requested_time)

        return SearchCriteria(
            origin=route[0],
            destination=route[1],
            travel_date=travel_date,
            requested_departure_time=requested_time,
            requested_time_slot=requested_time_slot,
            budget_inr=budget,
            flexible_timing=flexible_timing,
        )

    def _extract_route(self, query: str) -> tuple[str, str] | None:
        match = re.search(
            r"from\s+(?P<origin>[a-zA-Z ]+?)\s+to\s+(?P<destination>[a-zA-Z ]+?)(?:\s+on|\s+for|\s+around|\s+under|\s+budget|\s+this|\s+tomorrow|\s+today|\s*$)",
            query,
            re.IGNORECASE,
        )
        if not match:
            return None

        origin = re.sub(r"\s+", " ", match.group("origin")).strip().title()
        destination = re.sub(r"\s+", " ", match.group("destination")).strip().title()
        return origin, destination

    def _extract_date(self, query: str) -> str | None:
        exact_match = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", query)
        base_settings = {
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
            "TIMEZONE": "Asia/Kolkata",
            "RETURN_AS_TIMEZONE_AWARE": False,
        }

        if exact_match:
            parsed = parse_date(exact_match.group(0), settings=base_settings) # type: ignore
            if parsed:
                return parsed.strftime("%Y-%m-%d")

        results = search_dates(query, settings=base_settings, languages=["en"])
        if results:
            for matched_text, parsed_date in results:
                lowered = matched_text.lower().strip()
                if lowered in {"am", "pm"}:
                    continue
                return parsed_date.strftime("%Y-%m-%d")

        return None

    def _extract_time(self, query: str) -> tuple[str | None, str | None]:
        time_match = re.search(r"(?:around|at)?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", query, re.IGNORECASE)
        if time_match:
            raw_value = time_match.group(1).upper().replace(" ", "")
            parsed = datetime.strptime(raw_value, "%I:%M%p") if ":" in raw_value else datetime.strptime(raw_value, "%I%p")
            return None, parsed.strftime("%H:%M")

        for slot, time_value in TIME_SLOT_MAP.items():
            if re.search(rf"\b{slot}\b", query, re.IGNORECASE):
                return slot, time_value

        return None, None

    def _extract_budget(self, query: str) -> int | None:
        patterns = [
            r"(?:under|below|less than|upto|up to|max|budget)\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)",
            r"(?:₹|rs\.?|inr)\s*([0-9,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(",", ""))

        return None

    def _is_flexible(self, query: str, requested_time_slot: str | None, requested_time: str | None) -> bool:
        flexible_keywords = ["flexible", "around", "near", "plus minus", "+/-", "within"]
        if any(keyword in query.lower() for keyword in flexible_keywords):
            return True
        return requested_time_slot is not None or requested_time is not None


query_parser_service = QueryParserService()