import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layers, CheckCircle, AlertTriangle, XCircle, ArrowRight } from 'lucide-react';

const API_BASE_URL = "http://127.0.0.1:8000";

const BulkPatientList = () => {
  const [patients, setPatients] = useState([]);
  const [hospitals, setHospitals] = useState([]); 
  
  // Selection State
  const [selectedIds, setSelectedIds] = useState([]); 
  const [target, setTarget] = useState("");
  
  // Transfer State
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // 1. Fetch Patients (Safe Check)
      // Note: Adjust endpoint if your route is different (e.g., /api/records/my-records)
      const patRes = await axios.get(`${API_BASE_URL}/api/records/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (Array.isArray(patRes.data)) {
        setPatients(patRes.data);
      } else {
        setPatients([]); 
      }

      // 2. Fetch Hospitals
      const hospRes = await axios.get(`${API_BASE_URL}/api/doctors/target-hospitals`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (Array.isArray(hospRes.data)) {
        setHospitals(hospRes.data);
        if (hospRes.data.length > 0) setTarget(hospRes.data[0]);
      }

    } catch (err) {
      console.error("Bulk Fetch Error:", err);
    }
  };

  // Toggle single row selection
  const handleSelectOne = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(sid => sid !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  // Toggle "Select All"
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      // Map safe ID (handle _id or id)
      setSelectedIds(patients.map(p => p._id || p.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleBulkTransfer = async () => {
    if (!target || selectedIds.length === 0) return;
    setLoading(true);
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      
      // 🚀 SENDING BATCH TO SAME ENDPOINT
      const payload = { 
          record_ids: selectedIds, 
          target_hospital_name: target 
      };

      const res = await axios.post(`${API_BASE_URL}/api/transfer/execute-batch`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setResult(res.data);
      setSelectedIds([]); // Clear selection to prevent double send
      
    } catch (err) {
      alert("Bulk Transfer Failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
      {/* Header Bar */}
      <div className="p-4 bg-gray-50 border-b border-gray-200 flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-2">
          <Layers className="text-indigo-600" size={20} />
          <h3 className="font-bold text-gray-800">
            Bulk Patient Action
            <span className="ml-2 text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded-full">{patients.length} records</span>
          </h3>
        </div>
        
        {/* Bulk Controls */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 hidden sm:inline">Transfer selected to:</span>
          <select 
            className="text-sm border-gray-300 rounded shadow-sm py-1.5 px-2 bg-white"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            {hospitals.map(h => <option key={h} value={h}>{h}</option>)}
          </select>
          
          <button 
            onClick={handleBulkTransfer}
            disabled={loading || selectedIds.length === 0}
            className={`flex items-center gap-2 text-sm px-4 py-1.5 rounded font-medium text-white transition-all
              ${selectedIds.length === 0 ? "bg-gray-300 cursor-not-allowed" : "bg-indigo-600 hover:bg-indigo-700 shadow-md hover:shadow-lg"}`}
          >
            {loading ? "Processing..." : <>Transfer <span className="bg-indigo-500 px-1.5 rounded text-xs">{selectedIds.length}</span> <ArrowRight size={14}/></>}
          </button>
        </div>
      </div>

      {/* Result Report (Only shows after transfer) */}
      {result && (
        <div className="bg-blue-50 p-4 border-b border-blue-100 flex gap-6 text-sm animate-fade-in">
          <div className="font-bold text-blue-900 flex items-center gap-2">
            <Layers size={16}/> Batch Report:
          </div>
          <div className="text-green-700 flex items-center gap-1">
            <CheckCircle size={14}/> {result.success?.length || 0} Sent
          </div>
          <div className="text-amber-700 flex items-center gap-1" title="Patient data hasn't changed since last transfer">
            <AlertTriangle size={14}/> {result.skipped?.length || 0} Skipped (Duplicate)
          </div>
          {result.failed?.length > 0 && (
            <div className="text-red-700 flex items-center gap-1">
              <XCircle size={14}/> {result.failed?.length} Failed
            </div>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto max-h-80 overflow-y-auto">
        <table className="w-full text-left text-sm text-gray-500">
          <thead className="bg-gray-50 text-xs uppercase text-gray-700 sticky top-0 z-10 shadow-sm">
            <tr>
              <th className="p-3 w-10">
                <input 
                  type="checkbox" 
                  onChange={handleSelectAll}
                  checked={patients.length > 0 && selectedIds.length === patients.length}
                />
              </th>
              <th className="p-3">Patient ID</th>
              <th className="p-3">Diagnosis</th>
              <th className="p-3">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {patients.length === 0 ? (
               <tr><td colSpan="4" className="p-8 text-center italic text-gray-400">No patient records found.</td></tr>
            ) : (
               patients.map((p) => (
                <tr 
                  key={p._id || p.id} 
                  className={`hover:bg-gray-50 transition-colors ${selectedIds.includes(p._id || p.id) ? "bg-indigo-50/60" : ""}`}
                >
                  <td className="p-3">
                    <input 
                      type="checkbox" 
                      checked={selectedIds.includes(p._id || p.id)}
                      onChange={() => handleSelectOne(p._id || p.id)}
                    />
                  </td>
                  <td className="p-3 font-medium text-gray-900">{p.patient_email || p.patient_id || "Unknown"}</td>
                  <td className="p-3 text-gray-700">{p.diagnosis}</td>
                  <td className="p-3 text-xs">{new Date(p.created_at).toLocaleDateString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BulkPatientList;