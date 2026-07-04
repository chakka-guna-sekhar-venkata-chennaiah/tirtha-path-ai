"""
TirthaPathAI — LangGraph ReAct agent.
Uses DeepSeek LLM (OpenAI-compatible) with three Neo4j GDS tools.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.prompts import SYSTEM_PROMPT
from agent.tools import gds_analysis_tool, gds_community_tool, gds_path_tool

load_dotenv()


def _build_llm() -> ChatOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "DEEPSEEK_API_KEY not set.\n"
            "Copy .env.example → .env and add your key from platform.deepseek.com"
        )
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        temperature=0,
        streaming=True,
    )


@lru_cache(maxsize=1)
def get_agent():
    """Build and cache the TirthaPathAI ReAct agent."""
    llm   = _build_llm()
    tools = [gds_path_tool, gds_analysis_tool, gds_community_tool]
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )
