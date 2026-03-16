from app.agents.travel_agent import openrouter_travel_agent
from app.core.config import settings
from app.schemas import TravelChatResponse
from app.services.comparison import flight_comparison_service
from app.services.flight_providers import flight_provider_service
from app.services.query_parser import query_parser_service


class TravelChatService:
    async def handle_query(self, query: str) -> TravelChatResponse:
        criteria = query_parser_service.parse(query)

        if settings.openrouter_api_key:
            answer, comparison = await openrouter_travel_agent.run(query, criteria)
        else:
            provider_results = await flight_provider_service.search_all(criteria)
            comparison = flight_comparison_service.compare(criteria, provider_results)
            answer = flight_comparison_service.compose_answer(comparison)

        return TravelChatResponse(answer=answer, comparison=comparison)


travel_chat_service = TravelChatService()