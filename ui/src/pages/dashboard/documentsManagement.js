import '../../App.css';
import "milligram";
import {useState, useEffect} from "react";
import {Link} from "react-router-dom";

const DocumentsManagement = () => {

    const [folderName, setFolderName] = useState("");
    const [files, setFiles] = useState([]);
    const [documents, setDocuments] = useState([]);
    const [folders, setFolders] = useState([]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [mode, setMode] = useState(null);
    const API_URL = "http://localhost:8000";


    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!folderName.trim()) {
            setError("Folder name is required.");
            return;
        }

        if (files.length === 0) {
            setError("Please select at least one file.");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const formData = new FormData();

            formData.append("folder_name", folderName);

            for (const file of files) {
                formData.append("files", file);
            }

            const res = await fetch("/documents/upload", {
                method: "POST",
                body: formData,
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Upload failed");
            }

            setFolderName("");
            setFiles([]);

        } catch (err) {
            console.error("Upload error:", err);

            setError(
                err instanceof Error
                    ? err.message
                    : "Unknown upload error"
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {

        fetch("/documents")
            .then((res) => res.json())
            .then((data) => setFolders(data.folders))
            .catch((err) => {
                console.error("Folders error:", err);
            });

    }, []);


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


    const deleteDocument = async (filename) => {

        const confirmed = window.confirm(
            `Delete ${filename}?`
        );

        if (!confirmed) {
            return;
        }

        try {

            const res = await fetch(
                `/documents/${folderName}/${filename}`,
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
        }
    };

    const clearAll = () => {
        setFolderName("");
        setFiles([]);
        setDocuments([]);
        setError("");
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
                            setMode("upload");
                            clearAll();
                        }}
                    >
                        Upload
                    </button>
                </div>

                {mode === "manage" && (
                    <div className="inline-form">
                        <h4>Manage documents</h4>
                        <label htmlFor="folderField">
                            Please select folder name
                        </label>

                        <select
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

                {mode === "upload" && (
                    <div className="inline-form">
                        <h4>Upload documents</h4>
                        <label htmlFor="folderField">
                            Folder name
                        </label>

                        <input
                            type="text"
                            value={folderName}
                            onChange={(e) =>
                                setFolderName(e.target.value)
                            }
                            placeholder="Enter folder name (new or existing)"
                        />
                        <br />
                        <form onSubmit={handleSubmit}>
                            <fieldset>
                                <label htmlFor="fileField">
                                    Select documents
                                </label>

                                <input
                                    id="fileField"
                                    type="file"
                                    multiple
                                    onChange={(e) =>
                                        setFiles(
                                            Array.from(
                                                e.target.files || []
                                            )
                                        )
                                    }
                                />

                            </fieldset>

                            <button
                                type="submit"
                                className="button button-black"
                                disabled={
                                    loading ||
                                    !folderName.trim() ||
                                    files.length === 0
                                }
                            >
                                {
                                    loading
                                        ? "UPLOADING..."
                                        : "UPLOAD DOCUMENTS"
                                }
                            </button>

                        </form>

                        {files.length > 0 && (
                            <div style={{marginTop: "2rem"}}>
                                <h4>Selected files</h4>
                                <ul>
                                    {files.map((file, index) => (
                                        <li key={`${file.name}-${index}`}>
                                            {file.name}
                                        </li>
                                    ))}
                                </ul>
                            </div>
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
                    <div style={{marginTop: "2rem"}}>
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

                                <tr
                                    key={`${doc.filename}-${index}`}
                                >

                                    <td>{doc.filename}</td>
                                    <td>{doc.extension}</td>
                                    <td>
                                        {(
                                            doc.size_bytes / 1024
                                        ).toFixed(2)} KB
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