import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, Lock, AlertTriangle } from 'lucide-react'; // Optional icons

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const TransferControl = ({ recordId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [hospitals, setHospitals] = useState([]); 
  const [target, setTarget] = useState(""); 
  const [error, setError] = useState("");

  // 1. Load Target Hospitals
  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_BASE_URL}/api/doctors/target-hospitals`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setHospitals(res.data || []);
        if (res.data?.length > 0) setTarget(res.data[0]);
      } catch (err) {
        console.error("Hospital load error", err);
        setHospitals([]);
      }
    };
    fetchHospitals();
  }, []);

  // 2. Handle Transfer Action
  const handleTransfer = async () => {
    if (!target) return;
    
    setLoading(true);
    setResult(null);
    setError("");

    try {
      const token = localStorage.getItem('token');
      
      // Payload matches 'BatchTransferRequest' in transfer.py
      const payload = {
          record_ids: [recordId], // Sending as a list of 1
          target_hospital_name: target
      };

      const res = await axios.post(`${API_BASE_URL}/api/transfer/execute-batch`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // 3. Save the result (success/skipped/failed)
      setResult(res.data);
      
    } catch (err) {
      console.error("Transfer error:", err);
      setError("Network or Server Error");
    } finally {
      setLoading(false);
    }
  };

  // 4. Render Interface
  return (
    <div className="bg-gray-50 p-3 rounded-lg border border-gray-200 mt-2">
      <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
        <ShieldCheck size={12} /> Quantum Secure Transfer
      </h4>
      
      {!result ? (
        // STATE A: SELECTION MODE
        <div className="flex gap-2">
          <select 
            value={target} 
            onChange={(e) => setTarget(e.target.value)}
            className="flex-1 p-1.5 border border-gray-300 rounded text-sm bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
          >
            {hospitals.length === 0 && <option>No hospitals found</option>}
            {hospitals.map((h, i) => <option key={i} value={h}>{h}</option>)}
          </select>
          
          <button 
            onClick={handleTransfer} 
            disabled={loading || !target}
            className={`px-3 py-1.5 rounded text-sm font-medium text-white transition-all 
              ${loading ? "bg-gray-400 cursor-not-allowed" : "bg-indigo-600 hover:bg-indigo-700 shadow-sm"}`}
          >
            {loading ? "Encrypting..." : "Send"}
          </button>
        </div>
      ) : (
        // STATE B: RESULT FEEDBACK
        <div className="space-y-2 text-sm animate-fade-in">
          {/* Check Success List */}
          {result?.success?.includes(recordId) && (
            <div className="p-2 bg-green-100 text-green-800 rounded flex items-center gap-2 border border-green-200">
              <Lock size={14} /> 
              <span>Securely Transferred via QKD</span>
            </div>
          )}
          
          {/* Check Skipped List (Duplicate) */}
          {result?.skipped?.includes(recordId) && (
            <div className="p-2 bg-amber-50 text-amber-800 rounded flex items-center gap-2 border border-amber-200">
               <AlertTriangle size={14} />
               <span>Record already exists at target.</span>
            </div>
          )}

          {/* Check Failed List */}
          {result?.failed?.some(f => f.id === recordId) && (
            <div className="p-2 bg-red-50 text-red-800 rounded border border-red-200">
              ❌ Transfer Failed.
            </div>
          )}
          
          <button 
            onClick={() => setResult(null)}
            className="text-xs text-indigo-600 underline mt-1 hover:text-indigo-800"
          >
            Send to another hospital
          </button>
        </div>
      )}
      
      {error && <div className="text-xs text-red-600 mt-2">{error}</div>}
    </div>
  );
};

export default TransferControl;