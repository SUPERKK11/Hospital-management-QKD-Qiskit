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
      
      // 1. Call Backend to Decrypt & Accept
      await axios.post(`${API_BASE_URL}/api/transfer/accept`, 
        { inbox_id: id }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // 2. Remove from UI immediately
      setIncomingRecords(prev => prev.filter(r => (r._id || r.id) !== id));
      
      alert("✅ Accepted! Record decrypted and moved to your History.");
      window.location.reload(); // Refresh to show in main list

    } catch (err) {
      alert("❌ Failed to accept. Check console.");
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-indigo-100 shadow-sm overflow-hidden flex flex-col h-full">
      <div className="bg-indigo-50 p-4 border-b border-indigo-100 flex justify-between items-center">
        <h3 className="text-indigo-900 font-bold flex items-center gap-2">
          <ArrowDownCircle size={20} className="text-indigo-600"/> 
          Incoming Transfers
          {incomingRecords.length > 0 && (
            <span className="text-[10px] bg-indigo-600 text-white px-2 py-0.5 rounded-full shadow-sm animate-pulse">
              {incomingRecords.length} New
            </span>
          )}
        </h3>
        <button onClick={fetchInbox} className="text-xs bg-white border border-indigo-200 text-indigo-700 px-3 py-1 rounded hover:bg-indigo-100 transition shadow-sm">
          Refresh
        </button>
      </div>

      <div className="divide-y divide-gray-50 overflow-y-auto max-h-[400px]">
        {incomingRecords.length === 0 ? (
          <div className="p-8 text-center flex flex-col items-center justify-center text-gray-400">
            <CheckCircle size={32} className="mb-2 opacity-20" />
            <p className="text-sm italic">Inbox is empty.</p>
          </div>
        ) : (
          incomingRecords.map((rec) => {
            const recId = rec._id || rec.id;
            return (
              <div key={recId} className="p-4 hover:bg-gray-50 transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200">
                      🔒 ENCRYPTED
                    </span>
                    <h4 className="font-bold text-gray-800 text-sm mt-1">HIDDEN CONTENT</h4>
                  </div>
                  
                  {/* THE ACCEPT BUTTON */}
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
          })
        )}
      </div>
    </div>
  );
};

export default Inbox;