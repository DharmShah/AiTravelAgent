from pydantic import BaseModel, Field


class SearchCriteria(BaseModel):
    origin: str
    destination: str
    travel_date: str
    requested_departure_time: str | None = None
    requested_time_slot: str | None = None
    budget_inr: int | None = None
    flexible_timing: bool = False
    flexibility_hours: int = 2


class FlightOption(BaseModel):
    provider: str
    airline: str
    departure_time: str
    arrival_time: str | None = None
    price_inr: int
    booking_url: str | None = None
    within_flex_window: bool = False
    time_delta_minutes: int | None = None
    source_note: str | None = None


class FlightComparison(BaseModel):
    criteria: SearchCriteria
    platform_comparison: list[FlightOption] = Field(default_factory=list)
    best_option: FlightOption
    reasoning: str
    raw_results: list[FlightOption] = Field(default_factory=list)


class TravelChatRequest(BaseModel):
    query: str = Field(min_length=3)


class TravelChatResponse(BaseModel):
    answer: str
    comparison: FlightComparison