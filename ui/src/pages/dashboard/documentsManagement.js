import '../../App.css';
import "milligram";
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Modal } from 'antd';

const DocumentsManagement = () => {
    const [folderName, setFolderName] = useState("");
    const [files, setFiles] = useState([]);
    const [documents, setDocuments] = useState([]);
    const [folders, setFolders] = useState([]);

    const [agents, setAgents] = useState([]);
    const [selectedAgent, setSelectedAgent] = useState("");

    const [loading, setLoading] = useState(false);
    const [adminLoading, setAdminLoading] = useState(false);

    const [error, setError] = useState("");
    const [adminMessage, setAdminMessage] = useState("");
    const [adminResult, setAdminResult] = useState(null);

    const [mode, setMode] = useState(null);

    const API_URL = "http://localhost:8000";

    useEffect(() => {
        fetch("/documents")
            .then((res) => res.json())
            .then((data) => setFolders(data.folders || []))
            .catch((err) => {
                console.error("Folders error:", err);
            });
    }, []);

    useEffect(() => {
        fetch("/agents")
            .then((res) => res.json())
            .then((data) => {
                const specialistAgents = data.filter(
                    (agent) => agent.agent_type === "specialist"
                );

                setAgents(specialistAgents);

                if (specialistAgents.length > 0) {
                    setSelectedAgent(specialistAgents[0].name);
                }
            })
            .catch((err) => {
                console.error("Agents loading error:", err);
                setError("Cannot load agents.");
            });
    }, []);

    const refreshFolders = async () => {
        try {
            const res = await fetch("/documents");
            const data = await res.json();

            if (res.ok) {
                setFolders(data.folders || []);
            }
        } catch (err) {
            console.error("Folders refresh error:", err);
        }
    };

    const uploadDocumentAndRebuild = async (e) => {
        e.preventDefault();

        if (!selectedAgent) {
            setAdminMessage("Please select specialist agent.");
            return;
        }

        if (files.length === 0) {
            setAdminMessage("Please select document.");
            return;
        }

        setAdminLoading(true);
        setAdminMessage("");
        setAdminResult(null);
        setError("");

        try {
            const formData = new FormData();
            formData.append("file", files[0]);

            const response = await fetch(
                `/admin/documents/upload/${encodeURIComponent(selectedAgent)}`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Upload failed");
            }

            setAdminResult(data);
            setAdminMessage(
                "Document uploaded and agent index rebuilt successfully."
            );

            setFiles([]);
            await refreshFolders();

            const input = document.getElementById("ragUploadField");

            if (input) {
                input.value = "";
            }

            Modal.success({
                title: "UPLOAD completed",
                content: "Document uploaded and selected agent index rebuilt successfully.",
                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },
                okButtonProps: {
                    className: "button button-outline"
                }
            });
        } catch (err) {
            console.error("RAG upload error:", err);

            const message =
                err instanceof Error
                    ? err.message
                    : "Unknown upload error";

            setAdminMessage(message);

            Modal.error({
                title: "RAG upload failed",
                content: message,
                className: "milligram-confirm",
                okButtonProps: {
                    className: "button"
                }
            });
        } finally {
            setAdminLoading(false);
        }
    };

    const ingestAll = async () => {
        setAdminLoading(true);
        setAdminMessage("");
        setAdminResult(null);
        setError("");

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

            Modal.success({
                title: "Ingest completed",
                content: "All indexes rebuilt successfully.",
                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },
                okButtonProps: {
                    className: "button button-outline"
                }
            });
        } catch (err) {
            console.error("Ingest all error:", err);

            const message =
                err instanceof Error
                    ? err.message
                    : "Unknown ingest error";

            setAdminMessage(message);

            Modal.error({
                title: "Ingest failed",
                content: message,
                className: "milligram-confirm",
                okButtonProps: {
                    className: "button"
                }
            });
        } finally {
            setAdminLoading(false);
        }
    };

    const ingestAgent = async () => {
        if (!selectedAgent) {
            setAdminMessage("Please select specialist agent.");
            return;
        }

        setAdminLoading(true);
        setAdminMessage("");
        setAdminResult(null);
        setError("");

        try {
            const response = await fetch(
                `/admin/ingest/agent/${encodeURIComponent(selectedAgent)}`,
                {
                    method: "POST",
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Agent ingest failed");
            }

            setAdminResult(data);
            setAdminMessage(
                `Index rebuilt successfully for ${selectedAgent}.`
            );

            Modal.success({
                title: "Agent ingest completed",
                content: `Index rebuilt successfully for ${selectedAgent}.`,
                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },
                okButtonProps: {
                    className: "button button-outline"
                }
            });
        } catch (err) {
            console.error("Agent ingest error:", err);

            const message =
                err instanceof Error
                    ? err.message
                    : "Unknown ingest error";

            setAdminMessage(message);

            Modal.error({
                title: "Agent ingest failed",
                content: message,
                className: "milligram-confirm",
                okButtonProps: {
                    className: "button"
                }
            });
        } finally {
            setAdminLoading(false);
        }
    };

    const loadDocuments = async () => {
        if (!folderName.trim()) {
            setError("Folder name is required.");
            return;
        }

        setLoading(true);
        setError("");
        setDocuments([]);

        try {
            const res = await fetch(
                `/documents/${folderName}`
            );

            const data = await res.json();

            if (!res.ok) {
                throw new Error(
                    data.detail || "Cannot load documents"
                );
            }

            setDocuments(data.documents);
        } catch (err) {
            console.error("Documents loading error:", err);

            setError(
                err instanceof Error
                    ? err.message
                    : "Unknown error"
            );
        } finally {
            setLoading(false);
        }
    };

    const downloadDocument = (filename) => {
        window.open(
            `${API_URL}/documents/${folderName}/${encodeURIComponent(filename)}?download=true`,
            "_blank"
        );
    };

    const openDocument = (filename) => {
        window.open(
            `${API_URL}/documents/${folderName}/${encodeURIComponent(filename)}`,
            "_blank"
        );
    };

    const deleteDocument = (filename) => {
        Modal.confirm({
            title: "Are you sure you want to remove this document?",
            className: "milligram-confirm",
            okText: "Yes",
            cancelText: "No",
            okType: "danger",
            style: {
                border: "2px solid #9b4dca",
                borderRadius: "6px"
            },
            okButtonProps: {
                className: "button button-outline"
            },
            cancelButtonProps: {
                className: "button"
            },
            async onOk() {
                try {
                    const res = await fetch(
                        `/documents/${folderName}/${encodeURIComponent(filename)}`,
                        {
                            method: "DELETE",
                        }
                    );

                    const data = await res.json();

                    if (!res.ok) {
                        throw new Error(
                            data.detail || "Delete failed"
                        );
                    }

                    setDocuments((prev) =>
                        prev.filter(
                            (doc) => doc.filename !== filename
                        )
                    );
                } catch (err) {
                    console.error("Delete error:", err);

                    setError(
                        err instanceof Error
                            ? err.message
                            : "Unknown error"
                    );

                    throw err;
                }
            },
        });
    };

    const clearAll = () => {
        setFolderName("");
        setFiles([]);
        setDocuments([]);
        setError("");
        setAdminMessage("");
        setAdminResult(null);
    };

    return (
        <div className="container_main">
            <div className="dashboard_view_2">
                <div className="back-container">
                    <Link
                        to="/dashboard"
                        className="back-button"
                    >
                        ← Back to Dashboard
                    </Link>
                </div>

                <div className="button-group">
                    <button
                        className="button button-black button-outline"
                        onClick={() => {
                            setMode("manage");
                            clearAll();
                        }}
                    >
                        Manage
                    </button>

                    <button
                        className="button button-black button-outline"
                        onClick={() => {
                            setMode("rag");
                            clearAll();
                        }}
                    >
                        UPLOAD
                    </button>
                </div>

                {mode === "manage" && (
                    <div className="inline-form">
                        <h4>Manage documents</h4>

                        <label htmlFor="folderField">
                            Please select folder name
                        </label>

                        <select
                            id="folderField"
                            value={folderName}
                            onChange={(e) =>
                                setFolderName(e.target.value)
                            }
                        >
                            <option value="">
                                -- Select folder --
                            </option>

                            {folders.map((f) => (
                                <option key={f.name} value={f.name}>
                                    {f.name}
                                </option>
                            ))}
                        </select>

                        <button
                            className="button button-black"
                            onClick={loadDocuments}
                            disabled={loading || !folderName.trim()}
                        >
                            {loading ? "LOADING..." : "LOAD DOCUMENTS"}
                        </button>
                    </div>
                )}

                {mode === "rag" && (
                    <div className="inline-form">
                        <h4>RAG Admin Panel</h4>

                        <p>
                            Use this section to rebuild FAISS indexes or upload
                            a new document and rebuild the selected specialist agent.
                        </p>

                        <button
                            className="button button-black"
                            type="button"
                            onClick={ingestAll}
                            disabled={adminLoading}
                        >
                            {
                                adminLoading
                                    ? "PROCESSING..."
                                    : "REBUILD ALL INDEXES"
                            }
                        </button>

                        <hr />

                        <label htmlFor="agentField">
                            Choose specialist agent
                        </label>

                        <select
                            id="agentField"
                            value={selectedAgent}
                            onChange={(e) =>
                                setSelectedAgent(e.target.value)
                            }
                            disabled={adminLoading}
                        >
                            <option value="">
                                -- Select specialist agent --
                            </option>

                            {agents.map((agent) => (
                                <option
                                    key={agent.id}
                                    value={agent.name}
                                >
                                    {agent.name}
                                </option>
                            ))}
                        </select>

                        <button
                            className="button button-black"
                            type="button"
                            onClick={ingestAgent}
                            disabled={adminLoading || !selectedAgent}
                        >
                            {
                                adminLoading
                                    ? "PROCESSING..."
                                    : "REBUILD SELECTED AGENT"
                            }
                        </button>

                        <hr />

                        <form onSubmit={uploadDocumentAndRebuild}>
                            <fieldset>
                                <label htmlFor="ragUploadField">
                                    Upload document to selected agent
                                </label>

                                <input
                                    id="ragUploadField"
                                    type="file"
                                    accept=".txt,.md,.pdf"
                                    onChange={(e) =>
                                        setFiles(
                                            Array.from(
                                                e.target.files || []
                                            )
                                        )
                                    }
                                    disabled={adminLoading}
                                />
                            </fieldset>

                            <button
                                className="button button-black"
                                type="submit"
                                disabled={
                                    adminLoading ||
                                    !selectedAgent ||
                                    files.length === 0
                                }
                            >
                                {
                                    adminLoading
                                        ? "PROCESSING..."
                                        : "UPLOAD DOCUMENT + REBUILD AGENT"
                                }
                            </button>
                        </form>

                        {files.length > 0 && (
                            <div style={{ marginTop: "2rem" }}>
                                <h4>Selected file</h4>
                                <ul>
                                    {files.map((file, index) => (
                                        <li key={`${file.name}-${index}`}>
                                            {file.name}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {adminMessage && (
                            <div
                                style={{
                                    border: "1px solid #ddd",
                                    padding: "1rem",
                                    marginTop: "1rem",
                                }}
                            >
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
                )}

                {error && (
                    <div
                        style={{
                            border: "1px solid #c00",
                            padding: "1rem",
                            marginTop: "1rem",
                        }}
                    >
                        <strong>Error:</strong> {error}
                    </div>
                )}

                {documents.length > 0 && (
                    <div style={{ marginTop: "2rem" }}>
                        <h3>Documents</h3>

                        <table>
                            <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Extension</th>
                                <th>Size</th>
                                <th>Actions</th>
                            </tr>
                            </thead>

                            <tbody>
                            {documents.map((doc, index) => (
                                <tr key={`${doc.filename}-${index}`}>
                                    <td>{doc.filename}</td>

                                    <td>{doc.extension}</td>

                                    <td>
                                        {(doc.size_bytes / 1024).toFixed(2)} KB
                                    </td>

                                    <td
                                        style={{
                                            display: "flex",
                                            gap: "1rem",
                                        }}
                                    >
                                        <button
                                            className="button button-outline"
                                            onClick={() =>
                                                openDocument(doc.filename)
                                            }
                                        >
                                            Open
                                        </button>

                                        <button
                                            className="button button-outline"
                                            onClick={() =>
                                                downloadDocument(doc.filename)
                                            }
                                        >
                                            Download
                                        </button>

                                        <button
                                            className="button button-outline"
                                            onClick={() =>
                                                deleteDocument(doc.filename)
                                            }
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DocumentsManagement;