import json

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.schemas import FlightComparison, FlightOption, SearchCriteria
from app.services.comparison import flight_comparison_service
from app.services.flight_providers import flight_provider_service

class OpenRouterTravelAgent:
    async def run(self, query: str, criteria: SearchCriteria) -> tuple[str, FlightComparison]:
        provider_cache: dict[str, list[FlightOption]] = {}

        @tool
        async def search_ixigo(criteria_json: str) -> str:
            """Search Ixigo for available flights using the provided criteria JSON."""
            return await self._tool_search("Ixigo", criteria_json, provider_cache)

        @tool
        async def search_goibibo(criteria_json: str) -> str:
            """Search Goibibo for available flights using the provided criteria JSON."""
            return await self._tool_search("Goibibo", criteria_json, provider_cache)

        @tool
        async def search_makemytrip(criteria_json: str) -> str:
            """Search MakeMyTrip for available flights using the provided criteria JSON."""
            return await self._tool_search("MakeMyTrip", criteria_json, provider_cache)

        tools = [search_ixigo, search_goibibo, search_makemytrip]
        llm = ChatOpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
    model=settings.openrouter_model,
    temperature=0,
    max_tokens=500
)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an AI travel agent. Always call all three flight provider tools exactly once using the criteria JSON provided by the user. "
                    "After seeing the tool results, reply with a concise natural-language recommendation that mentions the cheapest strong fit and why it matches the requested timing and budget.",
                ),
                ("human", "Query: {input}\nCriteria JSON: {criteria_json}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

        result = await executor.ainvoke(
            {
                "input": query,
                "criteria_json": criteria.model_dump_json(),
            }
        )

        for provider in ("Ixigo", "Goibibo", "MakeMyTrip"):
            if provider not in provider_cache:
                provider_cache[provider] = await flight_provider_service.search_provider(provider, criteria)

        comparison = flight_comparison_service.compare(criteria, provider_cache)
        answer = str(result.get("output", "")).strip() or flight_comparison_service.compose_answer(comparison)
        return answer, comparison

    async def _tool_search(
        self,
        provider: str,
        criteria_json: str,
        provider_cache: dict[str, list[FlightOption]],
    ) -> str:
        criteria = SearchCriteria.model_validate_json(criteria_json)
        if provider not in provider_cache:
            provider_cache[provider] = await flight_provider_service.search_provider(provider, criteria)
        payload = [flight.model_dump() for flight in provider_cache[provider]]
        return json.dumps(payload, ensure_ascii=False)


openrouter_travel_agent = OpenRouterTravelAgent()