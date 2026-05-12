import '../App.css';
import "milligram";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
    const navigate = useNavigate();

    return (
        <div className="container_main">
            <div className="dashboard">
                <div className="tile" onClick={() => navigate("/agentsOverview")}>
                    <h5>Agents</h5>
                    <h5>Overview</h5>
                </div>

                <div className="tile" onClick={() => navigate("/agentsConfiguration")}>
                    <h5>Agents</h5>
                    <h5>Configuration</h5>
                </div>

                <div className="tile" onClick={() => navigate("/documentsManagement")}>
                    <h5>Documents</h5>
                    <h5>Management</h5>
                </div>

                <div className="tile">
                    <h5>Live status</h5>
                    <h5 style={{ color: '#e63946' }}>Not implemented</h5>
                </div>

                <div className="tile">
                    <h5>Performance</h5>
                    <h5 style={{ color: '#e63946' }}>Not implemented</h5>
                </div>

                <div className="tile">
                    <h5>Permissions</h5>
                    <h5 style={{ color: '#e63946' }}>Not implemented</h5>
                </div>

                <div className="tile">
                    <h5>FunctionB</h5>
                    <h5 style={{ color: '#e63946' }}>Not implemented</h5>
                </div>

                <div className="tile">
                    <h5>FunctionC</h5>
                    <h5 style={{ color: '#e63946' }}>Not implemented</h5>
                </div>

                <div className="tile">
                    <h5>FunctionD</h5>
                    <h5 style={{ color: '#e63946' }}>Not implemented</h5>
                </div>

            </div>
        </div>
    );
};

export default Dashboard;