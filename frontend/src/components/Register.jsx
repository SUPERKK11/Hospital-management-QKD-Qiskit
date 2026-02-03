import { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

// Uses the Cloud URL if available, otherwise localhost
const API_BASE_URL = "http://127.0.0.1:8000";

function Register() {
  const [formData, setFormData] = useState({
    email: "", 
    password: "",
    full_name: "",
    user_type: "patient", // Options: patient, doctor, government
    
    // Patient Fields
    abha_id: "",         // Will map to backend 'abha_number'
    
    // Doctor Fields
    hospital_name: "hospitalA" // Default value for dropdown
  });
  
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");

    try {
      // 1. Prepare Payload according to new Backend Rules
      const payload = {
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        role: formData.user_type,
        
        // ✅ FIX: Send NULL if not a doctor. (Do not force 'hospitalA')
        hospital: formData.user_type === "doctor" ? formData.hospital_name : null, 
        
        // Send ABHA only if patient
        abha_number: formData.user_type === "patient" ? formData.abha_id : null
      };

      console.log("Sending Unified Payload:", payload); 

      // 2. Single Endpoint for ALL roles
      await axios.post(`${API_BASE_URL}/api/auth/register`, payload);
      
      alert(`Registration Successful as ${formData.user_type.toUpperCase()}! Please Login.`);
      navigate("/"); 

    } catch (err) {
      console.error("Full Error:", err);
      // Smart error handling to show backend validation messages
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Registration failed. Please check backend connection.");
      }
    }
  };

  return (
    <div style={{ maxWidth: "400px", margin: "50px auto", textAlign: "center", fontFamily: "Arial, sans-serif" }}>
      <h2 style={{ color: "#0056b3" }}>📝 Secure Registration</h2>
      
      {/* Error Box */}
      {error && <div style={{ 
          color: "#721c24", 
          backgroundColor: "#f8d7da", 
          borderColor: "#f5c6cb",
          padding: "10px",
          marginBottom: "15px",
          borderRadius: "5px",
          fontSize: "0.9em"
      }}>{error}</div>}

      <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        
        {/* --- COMMON FIELDS --- */}
        <input type="text" name="full_name" placeholder="Full Name" value={formData.full_name} onChange={handleChange} required style={inputStyle} />
        <input type="email" name="email" placeholder="Email Address" value={formData.email} onChange={handleChange} required style={inputStyle} />
        <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required style={inputStyle} />

        {/* --- ROLE SELECTION --- */}
        <label style={{textAlign: "left", fontSize: "0.85em", color: "#666", marginBottom: "-5px"}}>Select Role:</label>
        <select name="user_type" value={formData.user_type} onChange={handleChange} style={inputStyle}>
            <option value="patient">Patient (ABHA User)</option>
            <option value="doctor">Doctor (Hospital Staff)</option>
            <option value="government">Government Official</option>
        </select>

        {/* --- PATIENT SPECIFIC FIELDS --- */}
        {formData.user_type === "patient" && (
            <div style={{animation: "fadeIn 0.5s"}}>
                <label style={{textAlign: "left", display:"block", fontSize: "0.85em", color: "#666"}}>ABHA Number (14 Digits):</label>
                <input 
                  type="text" 
                  name="abha_id" 
                  placeholder="e.g. 1234-5678-9012-14" 
                  value={formData.abha_id} 
                  onChange={handleChange} 
                  required 
                  maxLength="16" // Allow for dashes
                  style={{...inputStyle, borderColor: "#28a745"}} 
                />
                <small style={{color: "#888", fontSize: "0.7em"}}>We verify this locally.</small>
            </div>
        )}

        {/* --- DOCTOR SPECIFIC FIELDS (STRICT DROPDOWN) --- */}
        {formData.user_type === "doctor" && (
            <div style={{animation: "fadeIn 0.5s"}}>
                <label style={{textAlign: "left", display:"block", fontSize: "0.85em", color: "#666"}}>Select Your Workplace:</label>
                <select name="hospital_name" value={formData.hospital_name} onChange={handleChange} style={inputStyle} required>
                    <option value="hospitalA">Hospital A </option>
                    <option value="hospitalB">Hospital B </option>
                    <option value="hospitalC">Hospital C </option>
                </select>
            </div>
        )}
        <button type="submit" style={{ padding: "12px", cursor: "pointer", backgroundColor: "#21a340", color: "white", border: "none", borderRadius: "5px", fontWeight: "bold", marginTop: "10px" }}>
          Register Now
        </button>
      </form>

      <p style={{ marginTop: "20px" }}>
        Already have an ID? <Link to="/" style={{ color: "#0056b3" }}>Login here</Link>
      </p>
    </div>
  );
}

const inputStyle = { padding: "10px", borderRadius: "5px", border: "1px solid #ccc", fontSize: "1em" };

export default Register;