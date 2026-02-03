import { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

// Use Cloud URL or Localhost automatically
const API_BASE_URL = "http://127.0.0.1:8000";

function Login() {
  const [formData, setFormData] = useState({
    username: "", // This can be Email OR ABHA Number
    password: ""
  });
  
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      // 1. Format data for FastAPI (OAuth2 expects form-urlencoded, NOT JSON)
      const params = new URLSearchParams();
      params.append('username', formData.username);
      params.append('password', formData.password);

      // 2. Send Request
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, params, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      // 3. Extract Token and User Data
      const { access_token, role, full_name, hospital } = response.data;

      // 4. Save to Local Storage (The Browser's Safe)
      localStorage.setItem("token", access_token);
      localStorage.setItem("role", role);
      localStorage.setItem("user_name", full_name);
      if (hospital) localStorage.setItem("hospital", hospital);

      // 5. Success Feedback
      alert(`Welcome back, ${full_name}!`);
      
      // 6. Redirect to Dashboard (We will build this next!)
      navigate("/dashboard");

    } catch (err) {
      console.error("Login Error:", err);
      setError("Invalid Credentials. Please try again.");
    }
  };

  return (
    <div style={{ maxWidth: "400px", margin: "100px auto", textAlign: "center", fontFamily: "Arial, sans-serif" }}>
      <h2 style={{ color: "#0056b3" }}>🔐 Secure Login</h2>
      
      {error && <div style={{ 
          color: "#721c24", 
          backgroundColor: "#f8d7da", 
          padding: "10px", 
          marginBottom: "15px", 
          borderRadius: "5px" 
      }}>{error}</div>}

      <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
        
        <input 
            type="text" 
            name="username" 
            placeholder="Email Address OR ABHA Number" 
            value={formData.username} 
            onChange={handleChange} 
            required 
            style={inputStyle} 
        />
        
        <input 
            type="password" 
            name="password" 
            placeholder="Password" 
            value={formData.password} 
            onChange={handleChange} 
            required 
            style={inputStyle} 
        />

        <button type="submit" style={{ 
            padding: "12px", 
            cursor: "pointer", 
            backgroundColor: "#21a340", 
            color: "white", 
            border: "none", 
            borderRadius: "5px", 
            fontWeight: "bold", 
            fontSize: "1em" 
        }}>
          Login
        </button>
      </form>

      <p style={{ marginTop: "20px" }}>
        New here? <Link to="/register" style={{ color: "#0056b3" }}>Create an Account</Link>
      </p>
    </div>
  );
}

const inputStyle = { padding: "12px", borderRadius: "5px", border: "1px solid #ccc", fontSize: "1em" };

export default Login;