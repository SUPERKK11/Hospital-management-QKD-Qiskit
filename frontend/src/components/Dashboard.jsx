import { useEffect, useState, useRef, useCallback } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

// Components
import TransferControl from '../components/TransferControl';
import GovernmentView from '../components/GovernmentView';
import BulkPatientList from '../components/BulkPatientList';
import Inbox from '../components/Inbox';

const API_BASE_URL = "http://127.0.0.1:8000";

// 🛡️ SAFETY WRAPPER: Prevents entire app from crashing if a child fails
const SafeComponent = ({ children, name }) => {
  try {
    return children;
  } catch (err) {
    console.error(`CRASH in ${name}:`, err);
    return <div className="p-4 bg-red-100 text-red-700 border border-red-300 rounded">⚠️ {name} Crashed</div>;
  }
};

function Dashboard() {
  const [userRole, setUserRole] = useState("");
  const [fullName, setFullName] = useState("");
  const [allRecords, setAllRecords] = useState([]); 
  const [displayedRecords, setDisplayedRecords] = useState([]); 
  
  // Doctor Form Inputs
  const [patientEmail, setPatientEmail] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [prescription, setPrescription] = useState(""); 

  // Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  // Resizable Sidebar Logic
  const [leftWidth, setLeftWidth] = useState(400); 
  const isResizing = useRef(false);
  
  const startResizing = useCallback(() => {
    isResizing.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  const stopResizing = useCallback(() => {
    isResizing.current = false;
    document.body.style.cursor = "default";
    document.body.style.userSelect = "auto";
  }, []);

  const resize = useCallback((e) => {
    if (isResizing.current) {
      const newWidth = Math.min(Math.max(e.clientX, 300), window.innerWidth - 400);
      setLeftWidth(newWidth);
    }
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", resize);
    window.addEventListener("mouseup", stopResizing);
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [resize, stopResizing]);

  const navigate = useNavigate();

  // AUTH & FETCH
  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role") || localStorage.getItem("user_type");
    const name = localStorage.getItem("full_name");

    if (!token) {
      navigate("/"); 
    } else {
      setUserRole(role); 
      setFullName(name);
      if (role !== "government") initialFetch(token, role);
    }
  }, [navigate]);

  const initialFetch = async (token, role) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/records/my-records`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      // 🛡️ SAFETY: Ensure data is an array
      const data = Array.isArray(response.data) ? response.data : [];
      setAllRecords(data);
      if (role === 'patient') setDisplayedRecords(data);
    } catch (err) {
      console.error("Error fetching records:", err);
    }
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return alert("Please enter a Patient Email.");
    setHasSearched(true);
    const results = allRecords.filter(r => 
      r.patient_email?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setDisplayedRecords(results);
  };

  const handleCreateRecord = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    try {
      await axios.post(`${API_BASE_URL}/api/records/create`, 
        { patient_email: patientEmail, diagnosis, prescription, notes: "Direct Entry" },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert("✅ Record created!");
      setPatientEmail(""); setDiagnosis(""); setPrescription("");
      initialFetch(token, userRole);
    } catch (err) { alert("Error creating record."); }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate("/");
  };

  if (userRole === "government") return <GovernmentView onLogout={handleLogout} />;

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden font-sans">
      {/* HEADER */}
      <header className="flex-none bg-white p-4 shadow-sm border-b border-gray-200 flex justify-between items-center z-30">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 text-white p-2 rounded-lg text-xl font-bold">QKD</div>
            <div>
                <h2 className="text-xl font-bold text-gray-800 leading-tight">Quantum Health Nexus</h2>
                <p className="text-xs text-gray-500">{fullName} | <span className="capitalize text-indigo-600 font-semibold">{userRole}</span></p>
            </div>
          </div>
          <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 text-sm font-medium transition shadow-sm">
            Logout
          </button>
      </header>

      <div className="flex-1 flex overflow-hidden w-full relative">
        {/* LEFT PANEL */}
        {userRole === "doctor" && (
          <div className="flex flex-col bg-white border-r border-gray-200 h-full shadow-lg z-10" style={{ width: leftWidth, minWidth: 300 }}>
            <div className="p-5 border-b bg-gray-50 font-bold text-gray-700">📝 New Diagnosis</div>
            <div className="p-5 overflow-y-auto flex-1">
              <form onSubmit={handleCreateRecord} className="space-y-4">
                <input className="w-full p-3 border rounded-lg text-sm" placeholder="Patient Email" value={patientEmail} onChange={e => setPatientEmail(e.target.value)} required />
                <input className="w-full p-3 border rounded-lg text-sm" placeholder="Diagnosis" value={diagnosis} onChange={e => setDiagnosis(e.target.value)} required />
                <textarea className="w-full p-3 border rounded-lg text-sm h-32" placeholder="Prescription" value={prescription} onChange={e => setPrescription(e.target.value)} required />
                <button className="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold hover:bg-indigo-700">Submit Record</button>
              </form>
            </div>
          </div>
        )}

        {userRole === "doctor" && (
          <div className="w-1.5 bg-gray-200 hover:bg-indigo-400 cursor-col-resize z-20 transition-all" onMouseDown={startResizing}></div>
        )}

        {/* RIGHT PANEL */}
        <div className="flex-1 flex flex-col bg-gray-50 h-full overflow-hidden">
          <div className="flex-none p-5 border-b border-gray-200 bg-white shadow-sm z-10">
            <h3 className="font-bold text-gray-800 text-lg mb-3">
              {userRole === "doctor" ? "🔍 Clinical Management" : "📂 Medical History"}
            </h3>
            {userRole === "doctor" && (
              <div className="flex gap-2 max-w-xl">
                <input className="flex-1 p-2 border rounded-lg text-sm" placeholder="Search Patient History..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                <button onClick={handleSearch} className="bg-gray-800 text-white px-5 py-2 rounded-lg text-sm font-bold hover:bg-black">Search</button>
              </div>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-8">
            {/* 1. MANAGEMENT AREA (Bulk & Inbox) - The Danger Zone */}
            {userRole === "doctor" && !hasSearched && (
              <div className="space-y-6">
                {/* COMMENT THESE OUT IF STILL WHITE SCREEN */}
                 <BulkPatientList /> 
                 <Inbox /> 
              </div>
            )}

            {/* 2. SEARCH RESULTS */}
            <div className="space-y-4">
              {displayedRecords.length === 0 && hasSearched && (
                <div className="text-center py-10 text-gray-400 italic">No records found.</div>
              )}

              {displayedRecords.map((rec) => (
                <div key={rec._id || rec.id} className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:border-indigo-300 transition-all group">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-bold text-gray-900">{rec.diagnosis}</h4>
                    <span className="text-[10px] font-bold bg-indigo-50 text-indigo-700 px-2 py-1 rounded uppercase">{rec.hospital}</span>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 border-l-4 border-indigo-400 mb-4">{rec.prescription}</div>
                  
                  {/* TRANSFER CONTROL - ONLY FOR DOCTORS */}
                  {userRole === "doctor" && (
                    <div className="mt-4 pt-4 border-t border-dashed">
                      <TransferControl recordId={rec._id || rec.id} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;