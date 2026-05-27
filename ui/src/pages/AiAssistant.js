import '../App.css';
import "milligram";
import { useEffect, useState } from "react";

const AiAssistant = () => {
    const [agents, setAgents] = useState([]);
    const [selectedAgent, setSelectedAgent] = useState("");

    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState("");

    const [useReranker, setUseReranker] = useState(false);

    const [question, setQuestion] = useState("");
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const [adminAgent, setAdminAgent] = useState("");
    const [selectedFile, setSelectedFile] = useState(null);
    const [adminLoading, setAdminLoading] = useState(false);
    const [adminMessage, setAdminMessage] = useState("");
    const [adminResult, setAdminResult] = useState(null);

    useEffect(() => {
        fetch("/agents")
            .then((res) => res.json())
            .then((data) => {
                setAgents(data);

                const firstSpecialist = data.find(
                    (agent) => agent.agent_type === "specialist"
                );

                if (firstSpecialist) {
                    setAdminAgent(firstSpecialist.name);
                } else if (data.length > 0) {
                    setAdminAgent(data[0].name);
                }
            })
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
                    use_reranker: useReranker,
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

    const ingestAll = async () => {
        setAdminLoading(true);
        setAdminMessage("");
        setAdminResult(null);

        try {
            const response = await fetch("/admin/ingest/all", {
                method: "POST",
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Ingest all failed");
            }

            setAdminResult(data);
            setAdminMessage("All indexes rebuilt successfully.");
        } catch (err) {
            console.error("Error rebuilding all indexes:", err);
            setAdminMessage(err.message || "Unknown ingest error");
        } finally {
            setAdminLoading(false);
        }
    };

    const ingestAgent = async (agentName) => {
        if (!agentName) {
            setAdminMessage("Select agent first.");
            return;
        }

        setAdminLoading(true);
        setAdminMessage("");
        setAdminResult(null);

        try {
            const response = await fetch(
                `/admin/ingest/agent/${encodeURIComponent(agentName)}`,
                {
                    method: "POST",
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `Ingest failed for ${agentName}`);
            }

            setAdminResult(data);
            setAdminMessage(`Index rebuilt successfully for ${agentName}.`);
        } catch (err) {
            console.error("Error rebuilding agent index:", err);
            setAdminMessage(err.message || "Unknown ingest error");
        } finally {
            setAdminLoading(false);
        }
    };

    const uploadDocument = async (agentName, file) => {
        if (!agentName) {
            setAdminMessage("Select agent first.");
            return;
        }

        if (!file) {
            setAdminMessage("Select document first.");
            return;
        }

        setAdminLoading(true);
        setAdminMessage("");
        setAdminResult(null);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch(
                `/admin/documents/upload/${encodeURIComponent(agentName)}`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Document upload failed");
            }

            setAdminResult(data);
            setAdminMessage("Document uploaded and agent index rebuilt successfully.");
            setSelectedFile(null);

            const fileInput = document.getElementById("adminDocumentField");
            if (fileInput) {
                fileInput.value = "";
            }
        } catch (err) {
            console.error("Error uploading document:", err);
            setAdminMessage(err.message || "Unknown upload error");
        } finally {
            setAdminLoading(false);
        }
    };

    const debug = response?.debug;
    const chunks = debug?.chunks || [];

    const specialistAgents = agents.filter(
        (agent) => agent.agent_type === "specialist"
    );

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

                    <label htmlFor="rerankerField">
                        <input
                            id="rerankerField"
                            type="checkbox"
                            checked={useReranker}
                            onChange={(e) => setUseReranker(e.target.checked)}
                        />
                        Use Qwen Reranker
                    </label>

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

            <div style={{ border: "1px solid #ddd", padding: "1rem", marginTop: "2rem" }}>
                <h3>RAG Admin Panel</h3>

                <p>
                    Use this section to rebuild FAISS indexes or upload a new document
                    and rebuild the selected specialist agent.
                </p>

                <button
                    className="button"
                    type="button"
                    onClick={ingestAll}
                    disabled={adminLoading}
                >
                    {adminLoading ? "PROCESSING..." : "Rebuild All Indexes"}
                </button>

                <hr />

                <label htmlFor="adminAgentField">Choose specialist agent</label>
                <select
                    id="adminAgentField"
                    value={adminAgent}
                    onChange={(e) => setAdminAgent(e.target.value)}
                    disabled={adminLoading}
                >
                    <option value="">-- Select specialist agent --</option>
                    {specialistAgents.map((agent) => (
                        <option key={agent.id} value={agent.name}>
                            {agent.name}
                        </option>
                    ))}
                </select>

                <button
                    className="button"
                    type="button"
                    onClick={() => ingestAgent(adminAgent)}
                    disabled={adminLoading || !adminAgent}
                >
                    {adminLoading ? "PROCESSING..." : "Rebuild Selected Agent"}
                </button>

                <hr />

                <label htmlFor="adminDocumentField">Upload document to selected agent</label>
                <input
                    id="adminDocumentField"
                    type="file"
                    accept=".txt,.md,.pdf"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    disabled={adminLoading}
                />

                <button
                    className="button-primary"
                    type="button"
                    onClick={() => uploadDocument(adminAgent, selectedFile)}
                    disabled={adminLoading || !adminAgent || !selectedFile}
                >
                    {adminLoading ? "PROCESSING..." : "Upload Document + Rebuild Agent"}
                </button>

                {adminMessage && (
                    <div style={{ border: "1px solid #ddd", padding: "1rem", marginTop: "1rem" }}>
                        <strong>Status:</strong> {adminMessage}
                    </div>
                )}

                {adminResult && (
                    <details style={{ marginTop: "1rem" }}>
                        <summary>Admin operation result JSON</summary>
                        <pre style={{ whiteSpace: "pre-wrap" }}>
                            {JSON.stringify(adminResult, null, 2)}
                        </pre>
                    </details>
                )}
            </div>

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
                        <p><strong>Qwen Reranker:</strong> {debug?.use_reranker ? "enabled" : "disabled"}</p>
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
                                <td><strong>Reranker</strong></td>
                                <td>{debug?.use_reranker ? "enabled" : "disabled"}</td>
                            </tr>
                            <tr>
                                <td><strong>Retrieval time</strong></td>
                                <td>{debug?.retrieval_time_ms ?? "n/a"} ms</td>
                            </tr>
                            <tr>
                                <td><strong>Reranking time</strong></td>
                                <td>{debug?.reranking_time_ms ?? "n/a"} ms</td>
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