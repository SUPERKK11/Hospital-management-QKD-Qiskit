import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, Lock, RefreshCw } from 'lucide-react';

const ReceiverDashboard = () => {
  // Use the EXACT names from your previous dropdown
  const hospitalOptions = [
    "Hospital A",
    "Hospital B",
    "Hospital C"
  ];

  const [selectedHospital, setSelectedHospital] = useState(hospitalOptions[0]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchInbox = async () => {
    setLoading(true);
    try {
      // Clean the name for the URL to match backend logic
      const safeName = selectedHospital.toLowerCase().trim().replace(/ /g, "_");
      
      // Make the request
      const response = await axios.get(`http://localhost:8000/api/transfer/inbox/${safeName}`);
      setMessages(response.data);
    } catch (error) {
      console.error("Error fetching inbox", error);
      setMessages([]); // Clear if empty or error
    }
    setLoading(false);
  };

  // Auto-fetch when hospital changes
  useEffect(() => {
    fetchInbox();
  }, [selectedHospital]);

  return (
    <div className="mt-12 p-6 bg-gray-900 rounded-xl border border-gray-700">
      
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-blue-400 flex items-center gap-2">
            <ShieldCheck className="w-6 h-6" />
            Receiver Dashboard (Hospital B)
          </h2>
          <p className="text-gray-400 text-sm">View incoming QKD-Secured Packets</p>
        </div>

        {/* Controls */}
        <div className="flex gap-2">
          <select 
            value={selectedHospital}
            onChange={(e) => setSelectedHospital(e.target.value)}
            className="bg-gray-800 text-white border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          >
            {hospitalOptions.map(h => (
              <option key={h} value={h}>{h}</option>
            ))}
          </select>

          <button 
            onClick={fetchInbox}
            className="p-2 bg-gray-800 text-gray-300 rounded hover:bg-gray-700 border border-gray-600"
            title="Refresh Inbox"
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Inbox List */}
      <div className="space-y-3">
        {loading ? (
           <div className="text-center py-8 text-gray-500 animate-pulse">Scanning Quantum Channels...</div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8 bg-gray-800/50 rounded-lg border border-dashed border-gray-700">
            <p className="text-gray-500">No encrypted packets found for {selectedHospital}.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700 hover:border-blue-500/50 transition-all">
              <div className="flex justify-between items-start mb-2">
                
                {/* Left: Info */}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="bg-green-900/30 text-green-400 text-xs px-2 py-0.5 rounded border border-green-900">INCOMING</span>
                    <span className="text-sm text-gray-200 font-medium">Patient ID: {msg.patient_id}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    From: {msg.from} • {new Date(msg.time).toLocaleString()}
                  </div>
                </div>

                {/* Right: Status */}
                <div className="flex items-center gap-1 text-red-400 bg-red-900/10 px-2 py-1 rounded text-xs border border-red-900/30">
                  <Lock size={12} />
                  {msg.status}
                </div>
              </div>

              {/* The "Data" Preview */}
              <div className="bg-black/40 p-2 rounded border border-gray-700/50 font-mono text-xs text-gray-400 break-all">
                <span className="text-blue-500/70 mr-2 select-none">$ payload:</span>
                {msg.encrypted_preview}
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
};

export default ReceiverDashboard;