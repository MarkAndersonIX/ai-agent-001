from typing import Dict, Any
from core.base_agent import BaseAgent
from core.base_config_provider import ConfigProvider


class ResearchAgent(BaseAgent):
    """Research agent specialized for information gathering and analysis."""

    def __init__(self, config: ConfigProvider):
        """Initialize the research agent."""
        super().__init__("research_agent", config)

    def _build_system_prompt(
        self, relevant_context: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Build the system prompt for the research agent."""

        # Get base system prompt from configuration
        base_prompt = self.agent_config.get(
            "system_prompt",
            "You are a research assistant that finds credible sources, "
            "summarizes complex topics, and provides citations.",
        )

        # Add context information if available
        context_parts = [base_prompt]

        if relevant_context.get("context"):
            context_parts.append(
                "\nRelevant research and information from knowledge base:\n"
                + relevant_context["context"]
            )

        # Add specialized research instructions
        context_parts.append(
            "\nResearch Guidelines:\n"
            "- Prioritize credible, authoritative sources\n"
            "- Provide balanced perspectives on controversial topics\n"
            "- Distinguish between facts, opinions, and speculation\n"
            "- Note the date and relevance of information\n"
            "- Acknowledge limitations in available data\n"
            "- Suggest additional research directions when appropriate"
        )

        # Add tool usage instructions
        available_tools = self.list_tools()
        if available_tools:
            if "web_search" in available_tools:
                context_parts.append(
                    "\nWeb Search Usage:\n"
                    "- Use web search to find current, credible information\n"
                    "- Look for academic papers, government sources, and reputable organizations\n"
                    "- Cross-reference information from multiple sources\n"
                    "- Note the publication date and source credibility"
                )

        # Add information evaluation criteria
        context_parts.append(
            "\nSource Evaluation Criteria:\n"
            "- Authority: Who is the author/organization?\n"
            "- Accuracy: Is the information verifiable?\n"
            "- Objectivity: Is there potential bias?\n"
            "- Currency: How recent is the information?\n"
            "- Coverage: Is the topic treated comprehensively?"
        )

        # Add citation requirements
        context_parts.append(
            "\nCitation Requirements:\n"
            "- Always provide sources for factual claims\n"
            "- Include publication dates when available\n"
            "- Use a consistent citation format\n"
            "- Distinguish between primary and secondary sources\n"
            "- Note when information is preliminary or disputed"
        )

        # Add response structure guidance
        context_parts.append(
            "\nResponse Structure:\n"
            "- Begin with a clear summary of key findings\n"
            "- Organize information logically by topic or theme\n"
            "- Use headings and bullet points for clarity\n"
            "- Include a 'Sources' section at the end\n"
            "- Note any gaps in available information"
        )

        # Add source attribution from context
        if relevant_context.get("sources"):
            context_parts.append(
                "\nAvailable Sources from Knowledge Base:\n"
                "Use and cite the provided sources appropriately. "
                "Supplement with additional research as needed."
            )

        return "\n".join(context_parts)
