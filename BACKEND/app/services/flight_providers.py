import asyncio
import hashlib
import random
import re
from datetime import datetime, timedelta
from urllib.parse import quote

from app.core.config import settings
from app.schemas import FlightOption, SearchCriteria

try:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError # type: ignore
    from playwright.async_api import async_playwright # type: ignore
except ImportError:  # pragma: no cover
    PlaywrightTimeoutError = Exception
    async_playwright = None


AIRLINES = [
    "IndiGo",
    "Air India",
    "Akasa Air",
    "SpiceJet",
    "Vistara",
    "Air India Express",
]

AIRPORT_CODES = {
    "Delhi": "DEL",
    "Mumbai": "BOM",
    "Bengaluru": "BLR",
    "Bangalore": "BLR",
    "Hyderabad": "HYD",
    "Pune": "PNQ",
    "Goa": "GOI",
    "Chennai": "MAA",
    "Kolkata": "CCU",
    "Ahmedabad": "AMD",
    "Jaipur": "JAI",
    "Lucknow": "LKO",
}

PROVIDER_BIAS = {
    "Ixigo": 90,
    "Goibibo": -60,
    "MakeMyTrip": 35,
}


class FlightProviderService:
    async def search_all(self, criteria: SearchCriteria) -> dict[str, list[FlightOption]]:
        providers = ["Ixigo", "Goibibo", "MakeMyTrip"]
        results = await asyncio.gather(*(self.search_provider(provider, criteria) for provider in providers))
        return dict(zip(providers, results, strict=True))

    async def search_provider(self, provider: str, criteria: SearchCriteria) -> list[FlightOption]:
        mode = settings.flight_data_mode.lower()

        if mode in {"browser", "hybrid"}:
            try:
                browser_results = await self._search_with_browser(provider, criteria)
                if browser_results:
                    return browser_results
            except Exception:
                if mode == "browser":
                    raise

        return self._generate_fallback_flights(provider, criteria)

    async def _search_with_browser(self, provider: str, criteria: SearchCriteria) -> list[FlightOption]:
        if async_playwright is None:
            raise RuntimeError("Playwright is not installed.")

        search_url = self._build_search_url(provider, criteria)
        selectors = self._provider_selectors(provider)
        collected: list[FlightOption] = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=settings.request_timeout_seconds * 1000)
                await page.wait_for_timeout(3000)

                rows = page.locator(selectors["row"])
                row_count = min(await rows.count(), 6)

                for index in range(row_count):
                    row = rows.nth(index)
                    airline = await self._safe_text(row, selectors["airline"])
                    departure_time = self._normalize_time(await self._safe_text(row, selectors["departure"]))
                    price = self._normalize_price(await self._safe_text(row, selectors["price"]))

                    if airline and departure_time and price:
                        collected.append(
                            FlightOption(
                                provider=provider,
                                airline=airline,
                                departure_time=departure_time,
                                price_inr=price,
                                booking_url=search_url,
                                source_note="Live browser extraction",
                            )
                        )

            except PlaywrightTimeoutError as exc:
                raise RuntimeError(f"{provider} search timed out") from exc
            finally:
                await page.close()
                await browser.close()

        return collected

    async def _safe_text(self, row, selector: str) -> str | None:
        try:
            locator = row.locator(selector).first
            text = await locator.inner_text(timeout=1500)
            return text.strip()
        except Exception:
            return None

    def _provider_selectors(self, provider: str) -> dict[str, str]:
        default = {
            "row": "article, div[class*='flightCard'], div[class*='listingCard'], div[class*='flight-list-item']",
            "airline": "div[class*='airline'], span[class*='airline'], p[class*='airline']",
            "departure": "div[class*='time'], span[class*='time'], p[class*='time']",
            "price": "div[class*='price'], span[class*='price'], p[class*='price']",
        }

        provider_specific = {
            "Ixigo": {
                "row": "div[data-testid='FlightCard'], article, div[class*='resultRow']",
            },
            "Goibibo": {
                "row": "div[class*='flightRow'], div[class*='listingCard'], article",
            },
            "MakeMyTrip": {
                "row": "div[class*='listingCard'], div[class*='clusterViewCard'], article",
            },
        }

        return {**default, **provider_specific.get(provider, {})}

    def _build_search_url(self, provider: str, criteria: SearchCriteria) -> str:
        origin_code = AIRPORT_CODES.get(criteria.origin, criteria.origin[:3].upper())
        destination_code = AIRPORT_CODES.get(criteria.destination, criteria.destination[:3].upper())
        travel_date = datetime.strptime(criteria.travel_date, "%Y-%m-%d").strftime("%d%m%Y")

        if provider == "Ixigo":
            return (
                "https://www.ixigo.com/search/result/flight?from="
                f"{quote(origin_code)}&to={quote(destination_code)}&date={quote(criteria.travel_date)}"
            )
        if provider == "Goibibo":
            return (
                "https://www.goibibo.com/flights/air-"
                f"{quote(origin_code)}-{quote(destination_code)}-{travel_date}/"
            )
        return (
            "https://www.makemytrip.com/flight/search?itinerary="
            f"{quote(origin_code)}-{quote(destination_code)}-{quote(criteria.travel_date)}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
        )

    def _generate_fallback_flights(self, provider: str, criteria: SearchCriteria) -> list[FlightOption]:
        seed_text = f"{provider}|{criteria.origin}|{criteria.destination}|{criteria.travel_date}|{criteria.requested_departure_time}|{criteria.budget_inr}"
        seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:8], 16)
        generator = random.Random(seed)

        requested_minutes = self._time_to_minutes(criteria.requested_departure_time or "17:00")
        base_price = 4200 + seed % 1700
        flights: list[FlightOption] = []

        for offset in (-120, -30, 30, 105):
            departure_minutes = max(300, min(1380, requested_minutes + offset + generator.randint(-20, 20)))
            duration_minutes = generator.randint(80, 155)
            arrival_minutes = min(1435, departure_minutes + duration_minutes)
            price = base_price + PROVIDER_BIAS[provider] + (abs(offset) * 2) + generator.randint(50, 220)
            flights.append(
                FlightOption(
                    provider=provider,
                    airline=generator.choice(AIRLINES),
                    departure_time=self._minutes_to_time(departure_minutes),
                    arrival_time=self._minutes_to_time(arrival_minutes),
                    price_inr=price,
                    booking_url=self._build_search_url(provider, criteria),
                    source_note="Fallback runtime data used because live provider access was unavailable.",
                )
            )

        return flights

    def _normalize_price(self, value: str | None) -> int | None:
        if not value:
            return None
        digits = re.sub(r"[^0-9]", "", value)
        return int(digits) if digits else None

    def _normalize_time(self, value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(r"(\d{1,2}:\d{2})", value)
        if match:
            return match.group(1)
        match = re.search(r"(\d{1,2})\s*(am|pm)", value, re.IGNORECASE)
        if match:
            parsed = datetime.strptime(f"{match.group(1)}{match.group(2).upper()}", "%I%p")
            return parsed.strftime("%H:%M")
        return None

    def _time_to_minutes(self, value: str) -> int:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.hour * 60 + parsed.minute

    def _minutes_to_time(self, minutes: int) -> str:
        start_of_day = datetime(2000, 1, 1)
        return (start_of_day + timedelta(minutes=minutes)).strftime("%H:%M")


flight_provider_service = FlightProviderService()