import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models import Agent, AgentLink
from ollama_client import generate_answer, validate_model_name
from prompts.builders import build_specialist_prompt
from retrieval.reranker import DEFAULT_RERANKER_CANDIDATES
from retrieval.retriever import retrieve_chunks_for_folder
from retrieval.types import AgentRagAnswer, AgentRetrievalResult, RetrievedChunk


SPECIALIST_TOP_K = 3


@dataclass(frozen=True)
class RuntimeDebugInfo:
    agent_type: str
    language_model: str
    use_reranker: bool
    retrieval_time_ms: float
    reranking_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    confidence: float
    chunks: list[RetrievedChunk]


@dataclass(frozen=True)
class SupervisorRunResult:
    answer: str
    sources: list[str]
    chunks: list[RetrievedChunk]
    confidence: float


def is_unknown_answer(answer: str) -> bool:
    normalized = answer.strip().lower()

    return (
        "i don't know based on the provided documents" in normalized
        or "i don't know based on the provided agent answers" in normalized
        or "i do not know based on the provided documents" in normalized
        or "i do not know based on the provided agent answers" in normalized
        or "i don't know based on the provided child agent answers" in normalized
        or "i do not know based on the provided child agent answers" in normalized
    )


def _unique_sources_from_chunks(sources: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_sources: list[str] = []

    for source in sources:
        if source not in seen:
            seen.add(source)
            unique_sources.append(source)

    return unique_sources


def _calculate_confidence(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0

    best_score = max(item.score for item in chunks)
    average_score = sum(item.score for item in chunks) / len(chunks)

    return round((best_score * 0.7) + (average_score * 0.3), 4)


def _calculate_supervisor_confidence(results: list[AgentRagAnswer]) -> float:
    known_results = [
        result
        for result in results
        if result.chunks and not is_unknown_answer(result.answer)
    ]

    if not known_results:
        return 0.0

    return round(
        sum(result.confidence for result in known_results) / len(known_results),
        4,
    )


def _format_retrieved_chunks(chunks: list[RetrievedChunk]) -> str:
    return "\n\n---\n\n".join(
        (
            f"[source: {item.chunk.source_file} | "
            f"chunk: {item.chunk.chunk_id} | "
            f"chars: {item.chunk.start_char}-{item.chunk.end_char} | "
            f"score: {item.score:.4f}]\n"
            f"{item.chunk.content}"
        )
        for item in chunks
    )


def _build_child_question(question: str, child: Agent) -> str:
    """
    Very simple first version of query decomposition.

    Purpose:
    - reduce cross-agent confusion,
    - avoid sending the full multi-domain question to every child,
    - improve retrieval quality for supervisor agents.

    This can later be replaced by LLM-based decomposition.
    """
    normalized_question = question.lower()
    child_name = child.name.lower()
    child_docs_path = (child.docs_path or "").lower()

    if child_name == "harrypotter" or "hogwart" in child_docs_path:
        if "harry potter" in normalized_question:
            return question.replace(
                "and Lord of the Rings",
                "",
            ).replace(
                "and lord of the rings",
                "",
            ).strip()

    if child_name == "frodo" or "lotr" in child_docs_path:
        if "lord of the rings" in normalized_question:
            return question.replace(
                "Harry Potter and",
                "",
            ).replace(
                "harry potter and",
                "",
            ).strip()

    return question


def run_specialist_retrieval_only(
    question: str,
    agent: Agent,
    top_k: int = SPECIALIST_TOP_K,
    use_reranker: bool = False,
) -> AgentRetrievalResult:
    relevant_chunks = retrieve_chunks_for_folder(
        question=question,
        folder=agent.docs_path,
        top_k=top_k,
        agent_name=agent.name,
        use_reranker=use_reranker,
        reranker_candidates=DEFAULT_RERANKER_CANDIDATES,
    )

    sources = _unique_sources_from_chunks(
        [item.chunk.source_file for item in relevant_chunks]
    )

    confidence = _calculate_confidence(relevant_chunks)

    return AgentRetrievalResult(
        agent_name=agent.name,
        chunks=relevant_chunks,
        sources=sources,
        confidence=confidence,
    )


def run_specialist_rag_answer(
    question: str,
    agent: Agent,
    top_k: int = SPECIALIST_TOP_K,
    language_model: str | None = None,
    use_reranker: bool = False,
) -> AgentRagAnswer:
    selected_language_model = validate_model_name(language_model)

    retrieval_result = run_specialist_retrieval_only(
        question=question,
        agent=agent,
        top_k=top_k,
        use_reranker=use_reranker,
    )

    if not retrieval_result.has_context:
        return AgentRagAnswer(
            agent_name=agent.name,
            answer="I don't know based on the provided documents.",
            chunks=[],
            sources=[],
            confidence=0.0,
        )

    context = _format_retrieved_chunks(retrieval_result.chunks)

    prompt = build_specialist_prompt(
        agent_prompt=agent.prompt,
        question=question,
        context=context,
    )

    print("\n========== SPECIALIST PROMPT ==========")
    print("AGENT:", agent.name)
    print("QUESTION:", question)
    print(prompt)
    print("========== END SPECIALIST PROMPT ==========\n")

    answer = generate_answer(
        prompt,
        model_name=selected_language_model,
    )

    print("\n========== SPECIALIST ANSWER ==========")
    print("AGENT:", agent.name)
    print(answer)
    print("========== END SPECIALIST ANSWER ==========\n")

    return AgentRagAnswer(
        agent_name=agent.name,
        answer=answer,
        chunks=retrieval_result.chunks,
        sources=retrieval_result.sources,
        confidence=retrieval_result.confidence,
    )


def run_specialist_agent(
    question: str,
    agent: Agent,
    language_model: str | None = None,
    use_reranker: bool = False,
) -> tuple[str, list[str]]:
    result = run_specialist_rag_answer(
        question=question,
        agent=agent,
        language_model=language_model,
        use_reranker=use_reranker,
    )

    return result.answer, result.sources


def run_supervisor_agent_with_details(
    question: str,
    agent: Agent,
    db: Session,
    language_model: str | None = None,
    use_reranker: bool = False,
) -> SupervisorRunResult:
    selected_language_model = validate_model_name(language_model)

    links = (
        db.query(AgentLink)
        .filter(
            AgentLink.supervisor_agent_id == agent.id,
            AgentLink.active.is_(True),
        )
        .order_by(AgentLink.sort_order.asc(), AgentLink.id.asc())
        .all()
    )

    print("\n========== SUPERVISOR DEBUG ==========")
    print("SUPERVISOR:", agent.name)
    print("SUPERVISOR ID:", agent.id)
    print("QUESTION:", question)
    print("LINKS:", [(link.child_agent_id, link.active) for link in links])

    if not links:
        print("NO LINKS CONFIGURED")
        print("========== END SUPERVISOR DEBUG ==========\n")

        return SupervisorRunResult(
            answer="No connected agents are configured for this supervisor.",
            sources=[],
            chunks=[],
            confidence=0.0,
        )

    child_ids = [link.child_agent_id for link in links]

    child_agents = (
        db.query(Agent)
        .filter(
            Agent.id.in_(child_ids),
            Agent.active.is_(True),
        )
        .all()
    )

    child_map = {child.id: child for child in child_agents}

    print("CHILD IDS:", child_ids)
    print("CHILD AGENTS:", [child.name for child in child_agents])

    useful_child_results: list[AgentRagAnswer] = []
    collected_sources: list[str] = []
    collected_chunks: list[RetrievedChunk] = []

    for link in links:
        child = child_map.get(link.child_agent_id)

        if not child:
            print("MISSING OR INACTIVE CHILD AGENT:", link.child_agent_id)
            continue

        child_question = _build_child_question(
            question=question,
            child=child,
        )

        print("\n--- CALLING CHILD AGENT ---")
        print("CHILD ID:", child.id)
        print("CHILD NAME:", child.name)
        print("CHILD TYPE:", child.agent_type)
        print("CHILD DOCS PATH:", child.docs_path)
        print("CHILD QUESTION:", child_question)

        child_result = run_specialist_rag_answer(
            question=child_question,
            agent=child,
            language_model=selected_language_model,
            use_reranker=use_reranker,
        )

        print("CHILD RESULT AGENT:", child_result.agent_name)
        print("CHILD RESULT ANSWER:", child_result.answer)
        print("CHILD RESULT CONFIDENCE:", child_result.confidence)
        print("CHILD RESULT SOURCES:", child_result.sources)
        print("CHILD RESULT CHUNKS:", len(child_result.chunks))

        if child_result.chunks and not is_unknown_answer(child_result.answer):
            useful_child_results.append(child_result)
            collected_chunks.extend(child_result.chunks)
            collected_sources.extend(
                [
                    f"{child_result.agent_name}:{source}"
                    for source in child_result.sources
                ]
            )
            print("CHILD ACCEPTED BY SUPERVISOR")
        else:
            print("CHILD REJECTED BY SUPERVISOR")

    print("USEFUL CHILD RESULTS:", len(useful_child_results))
    print("========== END SUPERVISOR DEBUG ==========\n")

    if not useful_child_results:
        return SupervisorRunResult(
            answer="I don't know based on the provided agent answers.",
            sources=[],
            chunks=collected_chunks,
            confidence=0.0,
        )

    useful_child_results.sort(
        key=lambda item: item.confidence,
        reverse=True,
    )

    known_child_answers = [
        f"{result.agent_name}: {result.answer.strip()}"
        for result in useful_child_results
        if not is_unknown_answer(result.answer)
    ]

    if known_child_answers:
        final_answer = "\n\n".join(known_child_answers)
    else:
        final_answer = "I don't know based on the provided agent answers."

    print("\n========== SUPERVISOR ANSWER ==========")
    print(final_answer)
    print("========== END SUPERVISOR ANSWER ==========\n")

    unique_sources = _unique_sources_from_chunks(collected_sources)
    supervisor_confidence = _calculate_supervisor_confidence(useful_child_results)

    return SupervisorRunResult(
        answer=final_answer,
        sources=unique_sources,
        chunks=collected_chunks,
        confidence=supervisor_confidence,
    )


def run_supervisor_agent(
    question: str,
    agent: Agent,
    db: Session,
    language_model: str | None = None,
    use_reranker: bool = False,
) -> tuple[str, list[str]]:
    result = run_supervisor_agent_with_details(
        question=question,
        agent=agent,
        db=db,
        language_model=language_model,
        use_reranker=use_reranker,
    )

    return result.answer, result.sources


def _run_agent(
    question: str,
    agent: Agent,
    db: Session,
    language_model: str | None = None,
    use_reranker: bool = False,
) -> tuple[str, list[str]]:
    selected_language_model = validate_model_name(language_model)

    if agent.agent_type == "supervisor":
        return run_supervisor_agent(
            question=question,
            agent=agent,
            db=db,
            language_model=selected_language_model,
            use_reranker=use_reranker,
        )

    return run_specialist_agent(
        question=question,
        agent=agent,
        language_model=selected_language_model,
        use_reranker=use_reranker,
    )


def run_agent(
    question: str,
    agent: Agent,
    db: Session,
    language_model: str | None = None,
    use_reranker: bool = False,
) -> tuple[str, list[str]]:
    return _run_agent(
        question=question,
        agent=agent,
        db=db,
        language_model=language_model,
        use_reranker=use_reranker,
    )


def run_agent_with_debug(
    question: str,
    agent: Agent,
    db: Session,
    language_model: str | None = None,
    use_reranker: bool = False,
) -> tuple[str, list[str], RuntimeDebugInfo]:
    selected_language_model = validate_model_name(language_model)
    total_start = time.perf_counter()

    if agent.agent_type == "supervisor":
        generation_start = time.perf_counter()

        supervisor_result = run_supervisor_agent_with_details(
            question=question,
            agent=agent,
            db=db,
            language_model=selected_language_model,
            use_reranker=use_reranker,
        )

        generation_time_ms = round((time.perf_counter() - generation_start) * 1000, 2)
        total_time_ms = round((time.perf_counter() - total_start) * 1000, 2)

        debug = RuntimeDebugInfo(
            agent_type="supervisor",
            language_model=selected_language_model,
            use_reranker=use_reranker,
            retrieval_time_ms=0.0,
            reranking_time_ms=0.0,
            generation_time_ms=generation_time_ms,
            total_time_ms=total_time_ms,
            confidence=supervisor_result.confidence,
            chunks=supervisor_result.chunks,
        )

        return supervisor_result.answer, supervisor_result.sources, debug

    retrieval_start = time.perf_counter()

    retrieval_result = run_specialist_retrieval_only(
        question=question,
        agent=agent,
        use_reranker=use_reranker,
    )

    retrieval_time_ms = round((time.perf_counter() - retrieval_start) * 1000, 2)
    reranking_time_ms = retrieval_time_ms if use_reranker else 0.0

    if not retrieval_result.has_context:
        total_time_ms = round((time.perf_counter() - total_start) * 1000, 2)

        debug = RuntimeDebugInfo(
            agent_type="specialist",
            language_model=selected_language_model,
            use_reranker=use_reranker,
            retrieval_time_ms=retrieval_time_ms,
            reranking_time_ms=reranking_time_ms,
            generation_time_ms=0.0,
            total_time_ms=total_time_ms,
            confidence=0.0,
            chunks=[],
        )

        return "I don't know based on the provided documents.", [], debug

    context = _format_retrieved_chunks(retrieval_result.chunks)

    prompt = build_specialist_prompt(
        agent_prompt=agent.prompt,
        question=question,
        context=context,
    )

    print("\n========== SPECIALIST PROMPT ==========")
    print("AGENT:", agent.name)
    print("QUESTION:", question)
    print(prompt)
    print("========== END SPECIALIST PROMPT ==========\n")

    generation_start = time.perf_counter()

    answer = generate_answer(
        prompt,
        model_name=selected_language_model,
    )

    print("\n========== SPECIALIST ANSWER ==========")
    print("AGENT:", agent.name)
    print(answer)
    print("========== END SPECIALIST ANSWER ==========\n")

    generation_time_ms = round((time.perf_counter() - generation_start) * 1000, 2)
    total_time_ms = round((time.perf_counter() - total_start) * 1000, 2)

    debug = RuntimeDebugInfo(
        agent_type="specialist",
        language_model=selected_language_model,
        use_reranker=use_reranker,
        retrieval_time_ms=retrieval_time_ms,
        reranking_time_ms=reranking_time_ms,
        generation_time_ms=generation_time_ms,
        total_time_ms=total_time_ms,
        confidence=retrieval_result.confidence,
        chunks=retrieval_result.chunks,
    )

    return answer, retrieval_result.sources, debug