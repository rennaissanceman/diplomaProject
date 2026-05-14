import '../../App.css';
import "milligram";
import {Link} from "react-router-dom";

const LiveStatus = () => {


    return (
        <div className="container_main">
            <div className="dashboard_view_2">
                <div className="back-container">
                    <Link to="/dashboard" className="back-button">
                        ← Back to Dashboard
                    </Link>
                </div>


            </div>
        </div>
    );
};

export default LiveStatus;