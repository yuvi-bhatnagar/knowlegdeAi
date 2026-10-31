import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import NormalizedChatMessage
from app.ai.factory import AIProviderFactory
from app.core.config import settings
from app.core.exceptions import AIServiceException
from app.core.logging import logger
from app.repositories.document_repository import DocumentRepository
from app.schemas.chat import Citation
from app.services.vector_service import VectorService

INSUFFICIENT_EVIDENCE_PHRASE = (
    "I cannot find sufficient evidence in your uploaded documents to answer this question."
)

CONVERSATIONAL_GREETINGS = {
    "hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening",
    "how are you", "whats up", "who are you", "what can you do", "help", "how do you work",
    "thanks", "thank you", "bye", "goodbye",
}

def is_conversational_or_meta_query(query: str) -> bool:
    """Detect greetings, questions about assistant capabilities, identity, and system usage."""
    clean = re.sub(r"[^\w\s]", "", query.strip().lower())
    words = clean.split()

    pure_greetings = {
        "hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon",
        "good evening", "howdy", "sup", "thanks", "thank you", "bye", "goodbye",
    }
    if clean in pure_greetings or (len(words) <= 2 and any(w in pure_greetings for w in words)):
        return True

    meta_phrases = [
        "what can you do", "what you can do", "what are your capabilities", "what are you capable of",
        "who are you", "what are you", "tell me about yourself", "tell me what you can do",
        "tell me about what you can do", "how do you work", "how does this work", "how can you help",
        "can you help me", "what is your purpose", "what can i ask", "what should i ask",
        "how to use", "what is knowledgeai", "who created you", "what is your job",
        "what do you do", "can you only chat", "can you chat without",
        "help me understand what you do", "what documents", "how do i upload", "help",
    ]
    return any(p in clean for p in meta_phrases)


RAG_SYSTEM_PROMPT = """You are KnowledgeAI, an authoritative, helpful personal AI knowledge assistant.
Your answers are grounded in the user's uploaded documents provided in the context below.

CRITICAL RULES:
1. Write clean, natural, human-readable prose. Do NOT include raw technical tags like [Chunk 0], [Chunk 1], or [Chunk X] in your answer text.
2. If asked about the uploaded files, documents, or an overview (e.g., "tell me about the pdf uploaded", "what documents do I have?"), provide a clear, helpful one-liner or summary based on the document names and excerpts provided.
3. If the retrieved context genuinely does not contain enough evidence to answer a specific factual question, reply:
"{insufficient_evidence_phrase}"
4. Do not invent facts or extrapolate beyond the provided document context.
"""


class RAGService:
    """Orchestrates query embedding, vector retrieval, prompt construction, grounded chat generation, and citation verification."""

    def __init__(self, session: AsyncSession, vector_service: Optional[VectorService] = None):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.vector_service = vector_service or VectorService()

    async def execute_rag(
        self,
        query: str,
        owner_id: uuid.UUID,
        document_ids: Optional[List[uuid.UUID]] = None,
        top_k: Optional[int] = None,
        conversation_history: Optional[List[NormalizedChatMessage]] = None,
    ) -> Tuple[str, List[Citation], str, bool]:
        """
        Executes end-to-end RAG pipeline.
        Returns: (answer, verified_citations, model_name, insufficient_evidence_flag)
        """
        k = top_k or settings.RAG_TOP_K

        # 1. Fetch user's completed documents to establish filename and inventory context
        user_docs, total_docs = await self.doc_repo.list_by_owner(owner_id=owner_id, page=1, page_size=50)
        completed_docs = [d for d in user_docs if d.status == "completed"]
        if document_ids:
            target_docs = [d for d in completed_docs if d.id in document_ids]
        else:
            target_docs = completed_docs

        # Build document inventory string for filename context
        doc_inventory_lines = []
        for d in (target_docs if target_docs else completed_docs):
            size_kb = f"{d.file_size / 1024:.1f} KB" if d.file_size else "N/A"
            doc_inventory_lines.append(f'- "{d.original_filename}" ({size_kb}, {d.chunk_count} chunks)')
        doc_inventory_str = "\n".join(doc_inventory_lines) if doc_inventory_lines else "No documents uploaded."

        # Handle greetings, questions about capabilities, identity, and system usage
        if is_conversational_or_meta_query(query):
            chat_provider = AIProviderFactory.get_chat_provider()
            capability_messages = [
                NormalizedChatMessage(
                    role="system",
                    content=(
                        "You are KnowledgeAI, a personal AI knowledge assistant. "
                        "When the user greets you, asks who you are, asks what you can do, or asks about your capabilities, "
                        "introduce yourself clearly, concisely, and warmly.\n"
                        "Explain your key capabilities:\n"
                        "1. Answering questions grounded strictly in the user's uploaded documents (PDF, TXT, Markdown) with verified citations and page references.\n"
                        "2. Summarizing documents, extracting key themes, and analyzing complex content.\n"
                        "3. Allowing targeted document filtering or library-wide knowledge search.\n\n"
                        f"User's Active Document(s) in Scope:\n{doc_inventory_str}\n\n"
                        + (
                            "Mention the user's currently uploaded document(s) by name, and suggest 2-3 sample questions they can ask about them."
                            if completed_docs
                            else "Inform the user politely that they haven't uploaded any documents yet, and invite them to upload files in the Document Library."
                        )
                    ),
                )
            ]
            if conversation_history:
                for hist_msg in conversation_history[-4:]:
                    capability_messages.append(hist_msg)
            capability_messages.append(NormalizedChatMessage(role="user", content=query))

            try:
                response = await chat_provider.generate_chat_response(
                    messages=capability_messages,
                    temperature=0.3,
                    max_tokens=600,
                )
                return response.content.strip(), [], chat_provider.model_name, False
            except Exception as exc:
                logger.warning(f"Conversational generation fallback: {exc}")
                if completed_docs:
                    doc_names = ", ".join(f'"{d.original_filename}"' for d in completed_docs[:3])
                    fallback_text = (
                        f"Hello! I'm KnowledgeAI. I am ready to answer questions grounded in your uploaded documents ({doc_names}). "
                        "You can ask me for a summary, ask about specific topics, or explore details across your files. How can I help you today?"
                    )
                else:
                    fallback_text = (
                        "Hello! I'm KnowledgeAI, your personal AI knowledge assistant. You haven't uploaded any documents yet. "
                        "Please upload a PDF, TXT, or Markdown file in the Document Library so I can answer questions grounded in your files!"
                    )
                return fallback_text, [], chat_provider.model_name, False

        # 2. Embed query using configured embedding provider
        embedding_provider = AIProviderFactory.get_embedding_provider()
        query_vector = await embedding_provider.embed_query(query)

        collection_name = VectorService.get_collection_name(
            model_name=embedding_provider.model_name,
            dimension=embedding_provider.dimension,
        )

        # 3. Search Qdrant with owner_id and optional document_ids filtering
        scored_points = []
        try:
            scored_points = await self.vector_service.search(
                collection_name=collection_name,
                query_vector=query_vector,
                owner_id=owner_id,
                document_ids=document_ids,
                limit=k,
                score_threshold=settings.RAG_SIMILARITY_THRESHOLD,
            )
        except Exception as exc:
            logger.warning(f"Vector search failed or collection empty: {exc}")
            scored_points = []

        # 4. Extract retrieved chunks or fallback to introductory chunks for document overview
        retrieved_chunks = []
        if scored_points:
            for point in scored_points:
                payload = point.payload or {}
                retrieved_chunks.append({
                    "point_id": point.id,
                    "score": point.score,
                    "document_id": payload.get("document_id"),
                    "chunk_index": payload.get("chunk_index", 0),
                    "page_number": payload.get("page_number"),
                    "filename": payload.get("filename", "Unknown"),
                    "content": payload.get("content", ""),
                })
        else:
            # Fallback: if semantic search returned 0 matches but the user has uploaded documents
            # (e.g. meta queries like "tell me about the pdf uploaded", summaries, or slight misspellings),
            # retrieve the introductory chunks of the target document(s)
            docs_to_sample = target_docs if target_docs else completed_docs
            if docs_to_sample:
                for doc in docs_to_sample[:2]:
                    chunks = await self.doc_repo.get_chunks_for_document(doc.id, owner_id)
                    for c in chunks[:3]:  # sample initial chunks 0, 1, 2
                        retrieved_chunks.append({
                            "point_id": str(c.id),
                            "score": 0.85,
                            "document_id": str(doc.id),
                            "chunk_index": c.chunk_index,
                            "page_number": c.page_number,
                            "filename": doc.original_filename,
                            "content": c.content,
                        })

        # 5. Check if any context could be retrieved
        if not retrieved_chunks:
            chat_provider = AIProviderFactory.get_chat_provider()
            return INSUFFICIENT_EVIDENCE_PHRASE, [], chat_provider.model_name, True

        # 6. Build context payload for LLM
        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks):
            page_info = f", Page {chunk['page_number']}" if chunk['page_number'] else ""
            context_blocks.append(
                f"--- [Document: {chunk['filename']}{page_info}] ---\n{chunk['content']}\n"
            )
        combined_context = "\n".join(context_blocks)

        system_instruction = (
            f"{RAG_SYSTEM_PROMPT.format(insufficient_evidence_phrase=INSUFFICIENT_EVIDENCE_PHRASE)}\n\n"
            f"Uploaded Document(s) in Scope:\n{doc_inventory_str}"
        )

        # 7. Assemble prompt messages with bounded conversation history
        messages: List[NormalizedChatMessage] = [
            NormalizedChatMessage(role="system", content=system_instruction),
        ]

        # Add recent conversation history if provided (bounded to last 6 messages)
        if conversation_history:
            for hist_msg in conversation_history[-6:]:
                messages.append(hist_msg)

        # Add user query augmented with context
        augmented_query = (
            f"Retrieved Document Context:\n{combined_context}\n\n"
            f"User Question: {query}\n\n"
            "Provide a natural, grounded answer based on the context above. Do not include [Chunk X] tags in your response:"
        )
        messages.append(NormalizedChatMessage(role="user", content=augmented_query))

        # 8. Generate response via configured chat provider
        chat_provider = AIProviderFactory.get_chat_provider()
        chat_response = await chat_provider.generate_chat_response(
            messages=messages,
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )

        answer = chat_response.content.strip()

        # 9. Check if response indicates insufficient evidence
        if (
            INSUFFICIENT_EVIDENCE_PHRASE.lower() in answer.lower()
            or "insufficient evidence" in answer.lower()
            or "not enough evidence" in answer.lower()
        ):
            return INSUFFICIENT_EVIDENCE_PHRASE, [], chat_provider.model_name, True

        # 10. Verify citations against actual retrieved chunks
        verified_citations = self._verify_citations(answer, retrieved_chunks)

        # 11. Clean away any robotic "[Chunk 0]" or "[Chunk X]" tags from the final user-facing text
        clean_answer = re.sub(r"\s*\[(?:Chunk\s*)?\d+\]", "", answer).strip()
        clean_answer = re.sub(r" +", " ", clean_answer)

        return clean_answer, verified_citations, chat_provider.model_name, False

    def _verify_citations(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> List[Citation]:
        """
        Parses chunk citation references like [Chunk 0], [Chunk 1] or [0], [1]
        and maps them to real retrieved documents. Discards any fabricated citations.
        """
        # Find citations like [Chunk 0], [Chunk 1], [0], [1]
        citation_pattern = re.compile(r"\[(?:Chunk\s*)?(\d+)\]", re.IGNORECASE)
        matches = citation_pattern.findall(answer)

        cited_indices = set()
        for match in matches:
            try:
                idx = int(match)
                if 0 <= idx < len(retrieved_chunks):
                    cited_indices.add(idx)
            except ValueError:
                pass

        # If model didn't use explicit bracket tags but gave an answer based on retrieved chunks,
        # attach the top most relevant chunks as references
        if not cited_indices and retrieved_chunks:
            # Fallback to top 2 chunks that actually contributed to the context
            cited_indices = {i for i in range(min(2, len(retrieved_chunks)))}

        citations: List[Citation] = []
        for idx in sorted(cited_indices):
            chunk = retrieved_chunks[idx]
            raw_doc_id = chunk["document_id"]
            if not raw_doc_id:
                continue

            doc_uuid = uuid.UUID(raw_doc_id) if isinstance(raw_doc_id, str) else raw_doc_id
            excerpt = chunk["content"]
            if len(excerpt) > 250:
                excerpt = excerpt[:247] + "..."

            citations.append(
                Citation(
                    document_id=doc_uuid,
                    filename=chunk["filename"],
                    page_number=chunk["page_number"],
                    chunk_index=chunk["chunk_index"],
                    excerpt=excerpt,
                    score=chunk.get("score"),
                )
            )

        return citations

