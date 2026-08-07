import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_or_create_assistant_config,
    get_owned_conversation,
    get_owned_folder,
    get_owned_tone,
)
from app.db.session import get_db
from app.models.chat import Conversation, Message
from app.models.user import User
from app.schemas.chat import (
    ChatTurnOut,
    CitationOut,
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageCreate,
    MessageOut,
)
from app.services.llm.base import ChatMessage, LLMProviderError
from app.services.llm.defaults import default_model_for
from app.services.llm.factory import get_provider
from app.services.prompting import FALLBACK_NOTICE_TEMPLATE, build_system_prompt
from app.services.retrieval import retrieve

router = APIRouter(tags=["chat"])


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assistant_config = get_or_create_assistant_config(db, user)

    tone_id = payload.tone_id
    if tone_id is not None:
        get_owned_tone(db, user, tone_id)
    elif assistant_config.default_tone_id is not None:
        tone_id = assistant_config.default_tone_id

    provider = payload.provider or assistant_config.default_provider
    model = payload.model or default_model_for(db, user, provider, assistant_config)

    conversation = Conversation(
        owner_id=user.id,
        tone_id=tone_id,
        provider=provider,
        model=model,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Conversation)
        .filter(Conversation.owner_id == user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def rename_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = get_owned_conversation(db, user, conversation_id)
    conversation.title = payload.title.strip() or None
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conversation = get_owned_conversation(db, user, conversation_id)
    db.query(Message).filter(Message.conversation_id == conversation.id).delete()
    db.delete(conversation)
    db.commit()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conversation = get_owned_conversation(db, user, conversation_id)
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )


@router.post("/conversations/{conversation_id}/messages", response_model=ChatTurnOut)
def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = get_owned_conversation(db, user, conversation_id)
    assistant_config = get_or_create_assistant_config(db, user)
    tone = get_owned_tone(db, user, conversation.tone_id) if conversation.tone_id else None

    folder_ids = None
    if payload.retrieval_scope.type == "folders":
        folder_ids = payload.retrieval_scope.folder_ids
        for folder_id in folder_ids:
            get_owned_folder(db, user, folder_id)

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.content,
        retrieval_scope=payload.retrieval_scope.model_dump(mode="json"),
    )
    db.add(user_message)
    db.flush()

    if conversation.title is None and not history:
        # Auto-title from the opening message, same idea as ChatGPT/Claude's chat list — a
        # provider/model string isn't informational once you have more than a couple of chats.
        # Still renameable via PATCH /conversations/{id}.
        conversation.title = payload.content.strip()[:60]

    chunks, fallback_used = retrieve(
        db, user.id, payload.content, folder_ids, top_k=assistant_config.max_context_chunks
    )
    system_prompt = build_system_prompt(tone, assistant_config, chunks)

    llm_history = [ChatMessage(role=m.role, content=m.content) for m in history]
    llm_history.append(ChatMessage(role="user", content=payload.content))

    try:
        provider = get_provider(db, user, conversation.provider, conversation.model)
        reply_text = provider.generate(
            messages=llm_history,
            system_prompt=system_prompt,
            params={"temperature": assistant_config.temperature},
        )
    except LLMProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if fallback_used:
        reply_text = FALLBACK_NOTICE_TEMPLATE + reply_text

    # Stored as a JSON snapshot on the message itself (not re-resolved from document_chunks on
    # read) so a conversation's history stays meaningful even if the source document is later
    # edited, moved, or deleted — and so the frontend doesn't need special-case logic to show
    # citations for a message just sent vs. one loaded from history.
    citation_dicts = [
        CitationOut(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            page_ref=c.page_ref,
            chunk_text=c.chunk_text,
            distance=c.distance,
        ).model_dump(mode="json")
        for c in chunks
    ]

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        retrieval_scope=payload.retrieval_scope.model_dump(mode="json"),
        scope_fallback_used=fallback_used,
        source_chunk_ids=[str(c.chunk_id) for c in chunks],
        citations=citation_dicts,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return ChatTurnOut(user_message=user_message, assistant_message=assistant_message)
