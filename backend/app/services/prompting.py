from app.models.assistant_config import AssistantConfig
from app.models.tone import Tone
from app.services.retrieval import RetrievedChunk

NO_TONE_PROMPT = "You are a helpful assistant."
FALLBACK_NOTICE_TEMPLATE = (
    "_Nothing relevant found in the selected folder — searched all your documents instead._\n\n"
)


def build_system_prompt(tone: Tone | None, assistant_config: AssistantConfig, chunks: list[RetrievedChunk]) -> str:
    parts = [tone.system_prompt_template if tone else NO_TONE_PROMPT]

    if assistant_config.name or assistant_config.persona_description:
        parts.append(
            f"Your name is {assistant_config.name}. {assistant_config.persona_description}".strip()
        )

    if chunks:
        excerpts = "\n\n".join(
            f"[Source {i + 1}: {c.filename}"
            + (f", page {c.page_ref}" if c.page_ref else "")
            + f"]\n{c.chunk_text}"
            for i, c in enumerate(chunks)
        )
        parts.append(
            "Use the following document excerpts to answer the user's question. "
            "Cite sources by their bracketed number when you use them. "
            "If the excerpts don't contain relevant information, say so rather than guessing.\n\n"
            + excerpts
        )
    else:
        parts.append(
            "No relevant documents were found for this question. Answer from general knowledge "
            "and let the user know no matching documents were available."
        )

    return "\n\n".join(parts)
