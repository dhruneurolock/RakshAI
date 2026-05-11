import asyncio
import json

from app.agents.coordinator import CoordinatorAgent
from app.services.llm_service import LLMService

TARGET = "http://demo.testfire.net/"


async def main() -> None:
    agent = CoordinatorAgent("phase1_runner_real")
    agent.llm_service = LLMService()
    await agent.llm_service.initialize()

    strategy = await agent.create_attack_strategy(TARGET, {})

    print(f"PHASE1_TARGET={TARGET}")
    print(f"PHASE1_NON_MOCK={agent.llm_service.llm_strategic is not None}")
    print("PHASE1_STRATEGY_JSON_START")
    print(json.dumps(strategy, indent=2, default=str))
    print("PHASE1_STRATEGY_JSON_END")


if __name__ == "__main__":
    asyncio.run(main())
