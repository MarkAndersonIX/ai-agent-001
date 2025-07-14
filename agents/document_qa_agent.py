from typing import Dict, Any
from core.base_agent import BaseAgent
from core.base_config_provider import ConfigProvider


class DocumentQAAgent(BaseAgent):
    """Document Q&A agent specialized for analyzing and answering questions about documents."""

    def __init__(self, config: ConfigProvider):
        """Initialize the document Q&A agent."""
        super().__init__("document_qa", config)

    def _build_system_prompt(
        self, relevant_context: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Build the system prompt for the document Q&A agent."""

        # Get base system prompt from configuration
        base_prompt = self.agent_config.get(
            "system_prompt",
            "You are a document analysis assistant that answers questions "
            "based on provided documents with accurate citations.",
        )

        # Add context information if available
        context_parts = [base_prompt]

        if relevant_context.get("context"):
            context_parts.append(
                "\nRelevant document content:\n" + relevant_context["context"]
            )
        else:
            context_parts.append(
                "\nNo relevant documents found in the knowledge base for this query."
            )

        # Add specialized document analysis instructions
        context_parts.append(
            "\nDocument Analysis Guidelines:\n"
            "- Base your answers strictly on the provided document content\n"
            "- Quote directly from documents when making specific claims\n"
            "- Provide page numbers, section headings, or other location references when available\n"
            "- Clearly distinguish between what is explicitly stated vs. inferred\n"
            "- If information is not in the documents, clearly state this\n"
            "- Summarize multiple relevant sections when they relate to the question"
        )

        # Add citation and referencing instructions
        context_parts.append(
            "\nCitation Requirements:\n"
            "- Always cite the specific document and location for each claim\n"
            "- Use quotation marks for direct quotes\n"
            "- Provide context around quoted material\n"
            "- Reference multiple documents if they contain relevant information\n"
            "- Note any contradictions between different documents"
        )

        # Add response formatting guidelines
        context_parts.append(
            "\nResponse Format:\n"
            "- Provide a direct answer to the question first\n"
            "- Support the answer with relevant quotes and citations\n"
            "- Use clear paragraph breaks for different points\n"
            "- Include a summary if the answer is complex\n"
            "- List all referenced documents at the end"
        )

        # Add limitations and uncertainty handling
        context_parts.append(
            "\nHandling Uncertainty:\n"
            "- If the question cannot be answered from the documents, say so clearly\n"
            "- Distinguish between 'not mentioned' and 'explicitly contradicted'\n"
            "- Suggest what additional documents might be needed\n"
            "- Note if documents are incomplete or unclear on the topic\n"
            "- Indicate confidence level when interpreting ambiguous content"
        )

        # Add source information from context
        if relevant_context.get("sources"):
            source_info = []
            for i, source in enumerate(relevant_context["sources"], 1):
                metadata = source.get("metadata", {})
                if "file_path" in metadata:
                    source_info.append(f"Document {i}: {metadata['file_path']}")
                elif "source_url" in metadata:
                    source_info.append(f"Document {i}: {metadata['source_url']}")
                else:
                    source_info.append(
                        f"Document {i}: {metadata.get('title', 'Unknown source')}"
                    )

            if source_info:
                context_parts.append(
                    "\nAvailable Documents:\n" + "\n".join(source_info)
                )

        # Add document-specific analysis features
        context_parts.append(
            "\nDocument Analysis Features:\n"
            "- Identify key themes and topics\n"
            "- Extract definitions and explanations\n"
            "- Note relationships between concepts\n"
            "- Highlight important dates, numbers, and facts\n"
            "- Recognize document structure and organization\n"
            "- Compare information across multiple documents"
        )

        # Add quality assurance reminders
        context_parts.append(
            "\nQuality Assurance:\n"
            "- Double-check all citations for accuracy\n"
            "- Ensure quotes are exact and properly attributed\n"
            "- Verify that interpretations are well-supported\n"
            "- Maintain objectivity and avoid adding personal opinions\n"
            "- Focus on what the documents actually say, not external knowledge"
        )

        return "\n".join(context_parts)
