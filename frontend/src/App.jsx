import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard"; 
import Register from "./components/Register"; 
// 👇 1. Import the new Receiver Dashboard
import ReceiverDashboard from "./components/ReceiverDashboard"; 

function App() {
  return (
    <Router>
      <Routes>
        {/* Home Page is Login */}
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* 👇 2. Update this route to show BOTH the Sender and Receiver */}
        <Route path="/dashboard" element={
          <div className="bg-gray-900 min-h-screen pb-20">
            <Dashboard />          {/* The Sender (Top) */}
            
            {/* A divider to separate them */}
            <div className="container mx-auto px-6">
                <div className="border-t border-gray-700 my-8"></div>
            </div>

            {/* <ReceiverDashboard />  The Receiver (Bottom) */}
          </div>
        } />
      </Routes>
    </Router>
  );
}

export default App;
