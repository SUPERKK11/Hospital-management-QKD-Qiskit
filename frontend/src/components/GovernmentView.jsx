import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const GovernmentView = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await axios.get(`${API_BASE_URL}/api/transfer/audit-logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLogs(res.data);
    } catch (err) {
      console.error("Audit Fetch Error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-5 bg-white shadow rounded-lg">
      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        🏛️ National Health Oversight Log
        <button onClick={fetchLogs} className="text-sm bg-gray-200 px-2 py-1 rounded hover:bg-gray-300 ml-auto">Refresh</button>
      </h3>

      {loading ? (
        <p>Loading classified data...</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3">Sender</th>
                <th className="px-6 py-3">Receiver</th>
                <th className="px-6 py-3">QKD Key ID</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="bg-white border-b hover:bg-gray-50">
                  <td className="px-6 py-4">{new Date(log.timestamp).toLocaleString()}</td>
                  <td className="px-6 py-4 font-medium text-gray-900">{log.sender_hospital}</td>
                  <td className="px-6 py-4">{log.receiver_hospital}</td>
                  <td className="px-6 py-4 font-mono text-xs">{log.qkd_key_id}</td>
                  <td className="px-6 py-4 text-green-600 font-bold">{log.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && <p className="p-4 text-center">No transfers recorded yet.</p>}
        </div>
      )}
    </div>
  );
};

export default GovernmentView;