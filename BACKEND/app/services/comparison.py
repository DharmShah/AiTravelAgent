from datetime import datetime

from app.schemas import FlightComparison, FlightOption, SearchCriteria


class FlightComparisonService:
    def compare(
        self,
        criteria: SearchCriteria,
        provider_results: dict[str, list[FlightOption]],
    ) -> FlightComparison:
        provider_best: list[FlightOption] = []
        raw_results = [flight for flights in provider_results.values() for flight in flights]

        for provider, flights in provider_results.items():
            best = self._pick_best_for_provider(criteria, flights)
            if best is not None:
                provider_best.append(best)

        if not provider_best:
            raise ValueError("No flights could be collected from the configured providers.")

        best_option = self._pick_overall_best(criteria, provider_best)
        reasoning = self._build_reasoning(criteria, provider_best, best_option)

        return FlightComparison(
            criteria=criteria,
            platform_comparison=provider_best,
            best_option=best_option,
            reasoning=reasoning,
            raw_results=raw_results,
        )

    def compose_answer(self, comparison: FlightComparison) -> str:
        best = comparison.best_option
        budget_text = (
            f" under INR {comparison.criteria.budget_inr}" if comparison.criteria.budget_inr is not None else ""
        )
        return (
            f"I compared Ixigo, Goibibo, and MakeMyTrip for {comparison.criteria.origin} to "
            f"{comparison.criteria.destination} on {comparison.criteria.travel_date}{budget_text}. "
            f"The best option is {best.airline} on {best.provider} at {best.departure_time} for INR {best.price_inr}. "
            f"{comparison.reasoning}"
        )

    def _pick_best_for_provider(self, criteria: SearchCriteria, flights: list[FlightOption]) -> FlightOption | None:
        if not flights:
            return None

        requested_minutes = self._to_minutes(criteria.requested_departure_time)
        time_window_minutes = criteria.flexibility_hours * 60

        enriched: list[FlightOption] = []
        for flight in flights:
            flight_copy = flight.model_copy(deep=True)
            delta_minutes = None
            within_window = False

            if requested_minutes is not None:
                delta_minutes = abs(self._to_minutes(flight_copy.departure_time) - requested_minutes) # type: ignore
                within_window = delta_minutes <= time_window_minutes

            flight_copy.time_delta_minutes = delta_minutes
            flight_copy.within_flex_window = within_window
            enriched.append(flight_copy)

        budget_filtered = [
            flight for flight in enriched if criteria.budget_inr is None or flight.price_inr <= criteria.budget_inr
        ]
        candidate_pool = budget_filtered or enriched

        if criteria.flexible_timing and requested_minutes is not None:
            within_window = [flight for flight in candidate_pool if flight.within_flex_window]
            if within_window:
                candidate_pool = within_window

        return min(candidate_pool, key=lambda flight: self._provider_sort_key(criteria, flight))

    def _pick_overall_best(self, criteria: SearchCriteria, flights: list[FlightOption]) -> FlightOption:
        if criteria.flexible_timing and criteria.requested_departure_time is not None:
            within_window = [flight for flight in flights if flight.within_flex_window]
            if within_window:
                flights = within_window
        return min(flights, key=lambda flight: self._global_sort_key(criteria, flight))

    def _provider_sort_key(self, criteria: SearchCriteria, flight: FlightOption) -> tuple[int, int, int, int]:
        budget_penalty = 0 if criteria.budget_inr is None or flight.price_inr <= criteria.budget_inr else 1
        time_penalty = 0 if flight.within_flex_window else 1
        delta = flight.time_delta_minutes or 0

        if criteria.flexible_timing:
            return budget_penalty, time_penalty, flight.price_inr, delta
        if criteria.requested_departure_time is not None:
            return budget_penalty, delta, flight.price_inr, time_penalty
        return budget_penalty, flight.price_inr, delta, time_penalty

    def _global_sort_key(self, criteria: SearchCriteria, flight: FlightOption) -> tuple[int, int, int, int]:
        budget_penalty = 0 if criteria.budget_inr is None or flight.price_inr <= criteria.budget_inr else 1
        delta = flight.time_delta_minutes or 0
        within_window_penalty = 0 if flight.within_flex_window else 1
        return budget_penalty, within_window_penalty, flight.price_inr, delta

    def _build_reasoning(
        self,
        criteria: SearchCriteria,
        provider_best: list[FlightOption],
        best_option: FlightOption,
    ) -> str:
        platforms = ", ".join(
            f"{flight.provider} INR {flight.price_inr}" for flight in sorted(provider_best, key=lambda item: item.price_inr)
        )
        if criteria.requested_departure_time:
            return (
                f"Requested departure was around {criteria.requested_departure_time}. I prioritized options within "
                f"+/- {criteria.flexibility_hours} hours and then compared price. Platform snapshot: {platforms}."
            )
        return f"I ranked the lowest valid fare across the providers. Platform snapshot: {platforms}."

    def _to_minutes(self, value: str | None) -> int | None:
        if value is None:
            return None
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.hour * 60 + parsed.minute


flight_comparison_service = FlightComparisonService()