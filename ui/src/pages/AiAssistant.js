import '../App.css';
import "milligram";
import { useEffect, useState } from "react";

const AiAssistant = () => {
    const [agents, setAgents] = useState([]);
    const [selectedAgent, setSelectedAgent] = useState("");

    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState("");

    const [question, setQuestion] = useState("");
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        fetch("/agents")
            .then((res) => res.json())
            .then((data) => setAgents(data))
            .catch((err) => {
                console.error("Error fetching agents:", err);
                setError("Cannot load agents.");
            });
    }, []);

    useEffect(() => {
        fetch("/llm-models")
            .then((res) => res.json())
            .then((data) => {
                setModels(data);

                const defaultModel = data.find((model) => model.default);

                if (defaultModel) {
                    setSelectedModel(defaultModel.id);
                } else if (data.length > 0) {
                    setSelectedModel(data[0].id);
                }
            })
            .catch((err) => {
                console.error("Error fetching LLM models:", err);
                setError("Cannot load LLM models.");
            });
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setResponse(null);

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    question: question,
                    selected_agent: selectedAgent || null,
                    language_model: selectedModel || null,
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Request failed");
            }

            setResponse(data);
        } catch (err) {
            console.error("Error asking question:", err);
            setError(err.message || "Unknown error");
        } finally {
            setLoading(false);
        }
    };

    const debug = response?.debug;
    const chunks = debug?.chunks || [];

    return (
        <div className="container_main">
            <form onSubmit={handleSubmit}>
                <fieldset>
                    <label htmlFor="agentField">Choose your AI agent</label>
                    <select
                        id="agentField"
                        value={selectedAgent}
                        onChange={(e) => setSelectedAgent(e.target.value)}
                    >
                        <option value="">-- Select AI agent --</option>
                        {agents.map((agent) => (
                            <option key={agent.id} value={agent.name}>
                                {agent.name} ({agent.agent_type})
                            </option>
                        ))}
                    </select>

                    <label htmlFor="modelField">Choose language model</label>
                    <select
                        id="modelField"
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                    >
                        <option value="">-- Select language model --</option>
                        {models.map((model) => (
                            <option key={model.id} value={model.id}>
                                {model.label} ({model.id})
                            </option>
                        ))}
                    </select>

                    <label htmlFor="commentField">Question</label>
                    <textarea
                        id="commentField"
                        placeholder="Ask question here"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                    />

                    <input
                        className="button-primary"
                        type="submit"
                        value={loading ? "ASKING..." : "ASK"}
                        disabled={loading || !question.trim()}
                    />
                </fieldset>
            </form>

            {error && (
                <div style={{ border: "1px solid #c00", padding: "1rem", marginTop: "1rem" }}>
                    <strong>Error:</strong> {error}
                </div>
            )}

            {response && (
                <div style={{ marginTop: "2rem" }}>
                    <h3>Answer</h3>

                    <div style={{ border: "1px solid #ddd", padding: "1rem", marginBottom: "1rem" }}>
                        <p><strong>Agent:</strong> {response.agent}</p>
                        <p><strong>Agent type:</strong> {debug?.agent_type || "unknown"}</p>
                        <p><strong>Language model:</strong> {debug?.language_model || selectedModel || "unknown"}</p>
                        <p>{response.answer}</p>
                    </div>

                    <h4>RAG debug metrics</h4>
                    <table>
                        <tbody>
                            <tr>
                                <td><strong>Confidence</strong></td>
                                <td>{debug?.confidence ?? "n/a"}</td>
                            </tr>
                            <tr>
                                <td><strong>Retrieval time</strong></td>
                                <td>{debug?.retrieval_time_ms ?? "n/a"} ms</td>
                            </tr>
                            <tr>
                                <td><strong>Generation time</strong></td>
                                <td>{debug?.generation_time_ms ?? "n/a"} ms</td>
                            </tr>
                            <tr>
                                <td><strong>Total time</strong></td>
                                <td>{debug?.total_time_ms ?? "n/a"} ms</td>
                            </tr>
                        </tbody>
                    </table>

                    <h4>Sources</h4>
                    {response.sources?.length > 0 ? (
                        <ul>
                            {response.sources.map((source, index) => (
                                <li key={`${source}-${index}`}>{source}</li>
                            ))}
                        </ul>
                    ) : (
                        <p>No sources returned.</p>
                    )}

                    <h4>Retrieved chunks</h4>
                    {chunks.length > 0 ? (
                        chunks.map((chunk, index) => (
                            <details
                                key={`${chunk.source_file}-${chunk.chunk_id}-${index}`}
                                style={{ border: "1px solid #ddd", padding: "1rem", marginBottom: "1rem" }}
                            >
                                <summary>
                                    #{index + 1} | {chunk.source_file} | chunk: {chunk.chunk_id} | score: {chunk.score}
                                </summary>

                                <p><strong>Agent:</strong> {chunk.agent || "n/a"}</p>
                                <p><strong>Characters:</strong> {chunk.start_char}–{chunk.end_char}</p>
                                <pre style={{ whiteSpace: "pre-wrap" }}>{chunk.content}</pre>
                            </details>
                        ))
                    ) : (
                        <p>No chunks returned.</p>
                    )}

                    <h4>Raw JSON</h4>
                    <pre style={{ whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(response, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};

export default AiAssistant;