from langgraph.graph import StateGraph, END
from src.core.base import GoalState
from src.utils.logging_utils import get_logger
from src.core.agent_library import (
    fetch_goal_data_node,
    task_relevance_gate_node,
    task_suggestions_node,
    analytics_node,
    critical_strategy_node,
    optimization_strategy_node,
    balanced_strategy_node,
    route_strategy_node,
    insight_node,
    observation_tool_node,
    answer_formatter_node
)

logger = get_logger(__name__, __file__, logging_level="DEBUG")


def goal_orchestrator():

    workflow = StateGraph(GoalState)

    # Nodes
    workflow.add_node("fetch_data", fetch_goal_data_node)
    workflow.add_node("relevance_gate", task_relevance_gate_node)
    workflow.add_node("task_suggestions", task_suggestions_node)

    workflow.add_node("analytics", analytics_node)
    workflow.add_node("route_strategy", route_strategy_node)
    workflow.add_node("critical_strategy", critical_strategy_node)
    workflow.add_node("optimization_strategy", optimization_strategy_node)
    workflow.add_node("balanced_strategy", balanced_strategy_node)

    workflow.add_node("insight", insight_node)
    workflow.add_node("observation_tool", observation_tool_node)
    workflow.add_node("answer_formatter", answer_formatter_node)

    # Entry Point
    workflow.set_entry_point("fetch_data")

    # Edges
    workflow.add_edge("fetch_data", "relevance_gate")

    workflow.add_conditional_edges(
        "relevance_gate",
        lambda state: state["next_node"],
        {
            "task_suggestions": "task_suggestions",
            "analytics": "analytics"
        }
    )

    workflow.add_edge("task_suggestions", "observation_tool")
    workflow.add_edge("analytics", "route_strategy")

    workflow.add_conditional_edges(
        "route_strategy",
        lambda state: state["next_node"],
        {
            "critical_strategy": "critical_strategy",
            "optimization_strategy": "optimization_strategy",
            "balanced_strategy": "balanced_strategy"
        }
    )

    workflow.add_edge("critical_strategy", "insight")
    workflow.add_edge("optimization_strategy", "insight")
    workflow.add_edge("balanced_strategy", "insight")

    workflow.add_edge("insight", "observation_tool")
    workflow.add_edge("observation_tool", "answer_formatter")

    workflow.add_edge("answer_formatter", END)

    try:
        app = workflow.compile()
        graph_plot = app.get_graph().draw_mermaid_png()
        graph_path = f"orchestrator.png"
        with open(graph_path, "wb") as f:
            f.write(graph_plot)
        logger.info("Graph visualization saved successfully!")
        return app
    except Exception as e:
        logger.error(f"Warning: Could not generate graph visualization: {e}")
        return None