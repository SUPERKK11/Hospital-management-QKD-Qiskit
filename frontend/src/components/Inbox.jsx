import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Download, CheckCircle, ArrowDownCircle, Loader, AlertCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const Inbox = () => {
  const [incomingRecords, setIncomingRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    fetchInbox();
    const interval = setInterval(fetchInbox, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, []);

  const fetchInbox = async () => {
    if (incomingRecords.length === 0) setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_BASE_URL}/api/transfer/my-inbox`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIncomingRecords(res.data);
    } catch (err) {
      console.error("Error fetching inbox:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (id) => {
    setProcessingId(id);
    try {
      const token = localStorage.getItem('token');
      
      const res = await axios.post(`${API_BASE_URL}/api/transfer/accept`, 
        { inbox_id: id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // ✅ NEW: Show the Decrypted Data Popup
      if (res.data.decrypted_data) {
        alert(
          `🔓 QUANTUM DECRYPTION SUCCESSFUL!\n\n` +
          `Diagnosis: ${res.data.decrypted_data.diagnosis}\n` +
          `Prescription: ${res.data.decrypted_data.prescription}`
        );
      } else {
        alert("Record Accepted! Check your main dashboard.");
      }

      // Refresh Inbox
      fetchInbox();

    } catch (err) {
      console.error("Accept Error:", err);
      alert("Failed to accept transfer.");
    } finally {
      setProcessingId(null);
    }
  };

  if (loading && incomingRecords.length === 0) {
    return <div className="p-4 text-center text-gray-500 animate-pulse">Scanning Quantum Channel...</div>;
  }

  if (incomingRecords.length === 0) {
    return (
      <div className="bg-white p-6 rounded-xl border border-dashed border-gray-300 text-center">
        <ArrowDownCircle className="mx-auto text-gray-300 mb-2" size={32} />
        <p className="text-gray-500 text-sm">No incoming transfers.</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-indigo-100">
      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
        <ArrowDownCircle className="text-indigo-600" size={20} />
        Incoming Transfers
        <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full animate-pulse">
          {incomingRecords.length}
        </span>
      </h3>

      <div className="space-y-3">
        {incomingRecords.map((rec) => {
          const recId = rec._id || rec.id;
          return (
            <div key={recId} className="border border-indigo-100 rounded-lg p-4 hover:shadow-md transition-all bg-indigo-50/30">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200">
                    🔒 ENCRYPTED
                  </span>
                  <h4 className="font-bold text-gray-800 text-sm mt-1">HIDDEN CONTENT</h4>
                </div>
                
                <button 
                  onClick={() => handleAccept(recId)}
                  disabled={processingId === recId}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3 py-1.5 rounded shadow-sm flex items-center gap-2 transition-all disabled:opacity-70"
                >
                  {processingId === recId ? <Loader size={12} className="animate-spin"/> : <Download size={14} />}
                  Accept
                </button>
              </div>
              
              <div className="bg-gray-50 p-2 rounded border border-gray-100 mb-2">
                 <p className="text-xs text-gray-500 line-clamp-2 break-all font-mono">
                   {rec.prescription || "QKD Encrypted Data..."}
                 </p>
              </div>
              
              <div className="text-[11px] text-gray-500">
                From: <span className="font-bold text-indigo-600">{rec.sender || rec.hospital || "Unknown"}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Inbox;