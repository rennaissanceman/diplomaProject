import '../../App.css';
import "milligram";
import {Link} from "react-router-dom";
import {useState, useEffect} from "react";
import {Modal} from 'antd';

const AgentsConfiguration = () => {
    const [mode, setMode] = useState(null);
    const [agents, setAgents] = useState([]);
    const [selectedAgentId, setSelectedAgentId] = useState(null);
    const selectedAgent = agents.find(a => a.id === selectedAgentId);
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        docs_path: "",
        prompt: "",
        agent_type: "specialist",
        active: true,
        connected_agent_ids: []
    });

    const resetForm = () => ({
        name: "",
        description: "",
        docs_path: "",
        prompt: "",
        agent_type: "specialist",
        active: true,
        connected_agent_ids: []
    });

    const loadAgentToForm = (agent) => {
        setFormData({
            name: agent.name || "",
            description: agent.description || "",
            docs_path: agent.docs_path || "",
            prompt: agent.prompt || "",
            agent_type: agent.agent_type || "specialist",
            active: agent.active ?? true,
            connected_agent_ids: agent.connected_agent_ids || []
        });
    };


    useEffect(() => {
        fetch("/agents")
            .then(res => res.json())
            .then(data => setAgents(data));
    }, []);

    const clearAll = () => {
        setFormData(resetForm());
        setSelectedAgentId(null);
    };

    const createAgent = async () => {
        try {
            const res = await fetch("/agents", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(
                    data.detail || "Failed to create agent"
                );
            }

            setFormData({
                name: "",
                description: "",
                docs_path: "",
                prompt: "",
                agent_type: "specialist",
                active: true,
                connected_agent_ids: []
            });

            Modal.success({
                title: "Agent created",
                content: `Agent "${data.name || formData.name}" has been created successfully.`,

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
            console.error(err);

            Modal.error({
                title: "Error",
                content:
                    err instanceof Error
                        ? err.message
                        : "Error creating agent",

                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },

                okButtonProps: {
                    className: "button button-outline"
                }
            });
        }
    };

    const toggleAgentActive = async () => {
        if (!selectedAgentId) return;

        const agent = agents.find(a => a.id === selectedAgentId);
        if (!agent) return;

        const endpoint = agent.active
            ? `/agents/${selectedAgentId}/deactivate`
            : `/agents/${selectedAgentId}/activate`;

        try {
            const res = await fetch(endpoint, {
                method: "PATCH",
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(
                    data.detail || "Error updating agent status"
                );
            }

            setAgents(prev =>
                prev.map(a =>
                    a.id === selectedAgentId
                        ? {...a, active: !a.active}
                        : a
                )
            );

            Modal.success({
                title: "Agent status updated",
                content: `Agent "${agent.name}" has been ${
                    agent.active ? "deactivated" : "activated"
                } successfully.`,

                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },

                okButtonProps: {
                    className: "button button-outline"
                }
            });

            setSelectedAgentId(null);
            setMode(null);

        } catch (err) {
            console.error(err);

            Modal.error({
                title: "Error",
                content:
                    err instanceof Error
                        ? err.message
                        : "Error updating agent status",

                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },

                okButtonProps: {
                    className: "button button-outline"
                }
            });
        }
    };

    const updateAgent = async () => {
        if (!selectedAgentId) return;

        try {
            const res = await fetch(`/agents/${selectedAgentId}`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name: formData.name,
                    description: formData.description,
                    prompt: formData.prompt
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(
                    data.detail || "Failed to update agent"
                );
            }

            setAgents(prev =>
                prev.map(a =>
                    a.id === selectedAgentId
                        ? {...a, ...formData}
                        : a
                )
            );

            Modal.success({
                title: "Agent updated",
                content: `Agent "${formData.name}" has been updated successfully.`,

                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },

                okButtonProps: {
                    className: "button button-outline"
                }
            });

            setMode(null);
            setSelectedAgentId(null);

        } catch (err) {
            console.error(err);

            Modal.error({
                title: "Error",
                content:
                    err instanceof Error
                        ? err.message
                        : "Error updating agent",

                className: "milligram-confirm",
                style: {
                    border: "2px solid #9b4dca",
                    borderRadius: "6px"
                },

                okButtonProps: {
                    className: "button button-outline"
                }
            });
        }
    };


    return (
        <div className="container_main">
            <div className="dashboard_view_2">
                <div className="back-container">
                    <Link to="/dashboard" className="back-button">
                        ← Back to Dashboard
                    </Link>
                </div>

                <div className="button-group">
                    <button
                        className="button button-black button-outline"
                        onClick={() => {
                            clearAll();
                            setSelectedAgentId(null);
                            setMode("create");
                        }}

                    >
                        Add
                    </button>
                    <button
                        className="button button-black button-outline"
                        onClick={() => {
                            clearAll();
                            setMode("edit")
                        }}
                    >
                        Edit
                    </button>
                    <button
                        className="button button-black button-outline"
                        onClick={() => {
                            clearAll();
                            setMode("deactivate")
                        }}
                    >
                        Toggle Status
                    </button>
                </div>

                {mode === "edit" && (
                    <div className="inline-form">
                        <h4>Edit Agent</h4>

                        <select
                            value={selectedAgentId || ""}
                            onChange={(e) => {
                                const id = Number(e.target.value);
                                setSelectedAgentId(id);

                                const agent = agents.find(a => a.id === id);
                                if (agent) loadAgentToForm(agent);
                            }}
                        >
                            <option value="">Select agent</option>
                            {agents.map(agent => (
                                <option key={agent.id} value={agent.id}>
                                    {agent.name}
                                </option>
                            ))}
                        </select>


                        {selectedAgentId && (
                            <>
                                <input
                                    placeholder="Name"
                                    value={formData.name}
                                    onChange={(e) =>
                                        setFormData({...formData, name: e.target.value})
                                    }
                                />
                                <input
                                    placeholder="Description"
                                    value={formData.description}
                                    onChange={(e) =>
                                        setFormData({...formData, description: e.target.value})
                                    }
                                />
                                <textarea
                                    placeholder="Prompt"
                                    value={formData.prompt}
                                    onChange={(e) =>
                                        setFormData({...formData, prompt: e.target.value})
                                    }
                                />

                                <div className="form-actions">
                                    <button
                                        className="button button-black"
                                        onClick={updateAgent}
                                    >
                                        Save Changes
                                    </button>

                                    <button
                                        className="button button-outline"
                                        onClick={() => {
                                            clearAll();
                                            setMode(null);
                                            setSelectedAgentId(null);
                                        }}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {mode === "create" && (
                    <div className="inline-form">
                        <h4>Create Agent</h4>

                        <input
                            placeholder="Name"
                            value={formData.name}
                            onChange={(e) =>
                                setFormData({...formData, name: e.target.value})
                            }
                        />
                        <input
                            placeholder="Description"
                            value={formData.description}
                            onChange={(e) =>
                                setFormData({...formData, description: e.target.value})
                            }
                        />
                        <input
                            placeholder="Docs path"
                            value={formData.docs_path}
                            onChange={(e) =>
                                setFormData({...formData, docs_path: e.target.value})
                            }
                        />
                        <textarea
                            placeholder="Prompt"
                            value={formData.prompt}
                            onChange={(e) =>
                                setFormData({...formData, prompt: e.target.value})
                            }
                        />

                        <select
                            value={formData.agent_type}
                            onChange={(e) =>
                                setFormData({...formData, agent_type: e.target.value})
                            }
                        >
                            <option value="specialist">specialist</option>
                            <option value="supervisor">supervisor</option>
                        </select>
                        {formData.agent_type === "supervisor" && (
                            <select
                                multiple
                                value={formData.connected_agent_ids}
                                onChange={(e) => {
                                    const values = Array.from(
                                        e.target.selectedOptions,
                                        (option) => Number(option.value)
                                    );

                                    setFormData({
                                        ...formData,
                                        connected_agent_ids: values
                                    });
                                }}
                            >
                                {agents
                                    .filter(a => a.agent_type === "specialist")
                                    .map(agent => (
                                        <option key={agent.id} value={agent.id}>
                                            {agent.name}
                                        </option>
                                    ))}
                            </select>
                        )}
                        <label>
                            Status Active:
                            <input
                                type="checkbox"
                                checked={formData.active}
                                onChange={(e) =>
                                    setFormData({...formData, active: e.target.checked})
                                }
                            />
                        </label>

                        <div className="form-actions">
                            <button type="button" className="button button-black" onClick={createAgent}>
                                Save
                            </button>

                            <button
                                type="button"
                                className="button button-outline"
                                onClick={() => setMode(null)}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}

                {mode === "deactivate" && (
                    <div className="inline-form">
                        <h4>Change agent status</h4>

                        <select
                            value={selectedAgentId || ""}
                            onChange={(e) => setSelectedAgentId(Number(e.target.value))}
                        >
                            <option value="">Select agent</option>
                            {agents.map(agent => (
                                <option key={agent.id} value={agent.id}>
                                    {agent.name} ({agent.active ? "Active" : "Inactive"})
                                </option>
                            ))}
                        </select>

                        {selectedAgent && (
                            <p>
                                Current status:{" "}
                                <b>{selectedAgent.active ? "Active" : "Inactive"}</b>
                                <br/>
                                Action:{" "}
                                <b>{selectedAgent.active ? "Deactivate" : "Activate"}</b>
                            </p>
                        )}

                        <div className="form-actions">
                            <button
                                className="button button-black"
                                onClick={toggleAgentActive}
                                disabled={!selectedAgentId}
                            >
                                Change Status
                            </button>

                            <button
                                className="button button-outline"
                                onClick={() => {
                                    setMode(null);
                                    setSelectedAgentId(null);
                                }}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
};

export default AgentsConfiguration;