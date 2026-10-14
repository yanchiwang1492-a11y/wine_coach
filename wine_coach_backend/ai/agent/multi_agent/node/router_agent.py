"""
路由分类智能体：将用户输入分为 practice / answer / chat 三类。
由 manager 节点内部调用，非图节点，故命名 router_agent 而非 router_node。
"""
import asyncio

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from ai.agent.multi_agent.schema.intent_schema import RouterSchema
from ai.model.my_model import MyModel, LLM_TIMEOUT
from ai.prompt.builder_prompt import BuilderPromptYaml

# 预加载提示词
prompt = BuilderPromptYaml.get_prompt("router_agent.yaml")


async def router_agent(question: str) -> str:
    """
    对用户输入做路由分类

    Returns:
        "practice" | "answer" | "chat"
    """
    model = MyModel.get_online_model()
    agent = create_agent(model=model, system_prompt=prompt, response_format=RouterSchema)
    rs = await asyncio.wait_for(
        agent.ainvoke({"messages": [HumanMessage(content=question)]}),
        timeout=LLM_TIMEOUT,
    )
    route = rs["structured_response"].route
    return route if route in ("practice", "answer", "chat") else "chat"
