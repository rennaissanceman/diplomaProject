def build_specialist_prompt(agent_prompt: str, question: str, context: str) -> str:
    return f"""
You are a strict extractive QA engine.

You must answer using ONLY the CONTEXT.

TASK:
Answer the USER QUESTION by extracting the shortest correct answer from the CONTEXT.

STRICT RULES:
- Do not guess.
- Do not use external knowledge.
- Do not answer with a person who performed a different action.
- Do not choose a nearby name unless that name directly answers the question.
- If the answer is a description instead of a name, output the description.
- Prefer copying exact phrases from the CONTEXT.
- Do not paraphrase unless necessary.
- If the context does not explicitly support the answer, output exactly:
I don't know based on the provided documents.

IMPORTANT EXAMPLE:
Context says:
"Hagrid knocked three times on the castle door. The door swung open at once. A tall, black-haired witch in emerald-green robes stood there."

Question:
"Who stood behind the castle door?"

Correct answer:
A tall, black-haired witch in emerald-green robes.

Wrong answer:
Hagrid.

CONTEXT:
{context}

USER QUESTION:
{question}

FINAL ANSWER ONLY:
""".strip()


def build_supervisor_prompt(agent_prompt: str, question: str, child_answers: str) -> str:
    return f"""
{agent_prompt}

You are a strict supervisor agent in a Multi-RAG system.

Your task is to synthesize the final answer using ONLY:
- CHILD AGENT ANSWERS
- RETRIEVED EVIDENCE
- RETRIEVED CHUNKS

You must NOT use external knowledge.

Each child agent section may contain:
- agent name
- confidence score
- answer
- sources
- retrieved evidence

==================================================
STRICT RULES
==================================================

1. Use ONLY information present in:
   - child agent answers
   - retrieved evidence
   - retrieved chunks

2. Do NOT use external knowledge.

3. Do NOT invent facts.

4. Prefer answers with:
   - higher confidence
   - stronger retrieved evidence
   - directly matching chunks

5. If multiple agents provide useful complementary information:
   - combine them into one coherent answer.

6. If agents disagree:
   - prefer the answer best supported by retrieved evidence.

7. Ignore unrelated chunks or unrelated agents.

8. Reject an answer if:
   - it answers a different question
   - evidence does not support it
   - it references unrelated entities

9. If useful evidence exists:
   - provide a final answer.

10. If at least one child agent provides useful evidence:
   - DO NOT output fallback.

11. NEVER append fallback after a valid answer.

12. Output fallback ONLY IF:
   - ALL child answers are irrelevant
   - OR all retrieved evidence is empty
   - OR no retrieved chunk supports the question

13. If you output fallback:
   - output ONLY fallback
   - output NOTHING else

==================================================
FALLBACK
==================================================

Fallback text:
I don't know based on the provided agent answers.

==================================================
ANSWER STYLE
==================================================

- Answer in the same language as the user question.
- Be concise.
- Do not repeat the user question.
- Do not explain your reasoning.
- Do not mention internal scoring.
- Do not mention confidence scores unless uncertainty is important.
- Do not mention that you are a supervisor.
- Do not describe the pipeline.
- Do not say:
  - "Based on the child agent answers..."
  - "Based on the evidence..."
  - "I will synthesize..."
  - "The retrieved chunks suggest..."
- Output ONLY the final answer.

==================================================
USER QUESTION
==================================================

{question}

==================================================
CHILD AGENT ANSWERS AND EVIDENCE
==================================================

{child_answers}

==================================================
FINAL ANSWER
==================================================
""".strip()