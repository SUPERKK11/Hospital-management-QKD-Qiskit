# 🏥 Quantum-Secured Hospital Management System

> A Full-Stack Medical Portal featuring Post-Quantum Cryptography Simulation (BB84 Protocol).

## 🚀 Overview
This project is a **Hospital Management System** designed to demonstrate the future of cybersecurity in healthcare. Unlike standard web apps that rely solely on classical encryption (which can be broken by future quantum computers), this system integrates a **Quantum Key Distribution (QKD)** simulation.

It simulates the **BB84 Protocol** to generate unhackable encryption keys, ensuring that patient diagnosis and prescription data remain mathematically secure against interception.

## 🛠️ Tech Stack
* **Frontend:** React.js (Vite), Axios, CSS Modules
* **Backend:** Python (FastAPI), Uvicorn
* **Database:** MongoDB Atlas (Cloud NoSQL)
* **Security:** JWT Authentication, AES-256 Encryption, BB84 Quantum Simulation

## ✨ Key Features
* **🔐 Role-Based Access Control:** Distinct portals for **Doctors** (Write Access) and **Patients** (Read Access).
* **⚛️ Quantum Key Distribution (QKD):** Simulates the exchange of qubits (photons) between sender and receiver to generate a shared secret key.
* **🛡️ Hybrid Encryption:** Uses the generated Quantum Key to encrypt sensitive medical data (Diagnosis/Prescription) before saving to MongoDB.
* **📂 Modern Dashboard:** A clean, responsive UI for patients to view their medical history securely.

## ⚛️ How the Quantum Security Works
The system implements a simulation of the **BB84 Protocol**:
1.  **Alice (Server)** prepares random bits encoded in random quantum bases (Rectilinear `+` or Diagonal `x`).
2.  **Bob (Client Logic)** measures these bits using random bases.
3.  **Sifting:** They compare bases publicly. If the bases match, the bit is kept. If not, it is discarded.
4.  **Key Generation:** The remaining bits form a **Shared Secret Key**.
5.  **Encryption:** This key is used to lock the patient's record using AES encryption. Even if the database is hacked, the attacker sees only gibberish.

## 📸 Screenshots
*(Add screenshots of your Login Page and Dashboard here)*

## ⚡ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/SUPERKK11/Hospital-management-QKD-Qiskit.git.](https://github.com/SUPERKK11/Hospital-management-QKD-Qiskit.git)
cd hospital-management-qkd
```
### 2. Backend Setup (Using Conda)
```bash
Prerequisite: Install Anaconda or Miniconda.
cd backend
# Create the environment
conda create --name hospital-sys python=3.9
# Activate it
conda activate hospital-sys
# Install dependencies
pip install fastapi uvicorn pymongo python-dotenv pydantic bcrypt pyjwt cryptography
# Run the Server
python -m uvicorn app.main:app --reload
```
### 3. Frontend Setup (React)
```bash
cd frontend
# Install dependencies
npm install
# Run the UI
npm run dev
```

## 🐳 Docker Quick Start (Recommended)
You don't need to install Python or Node.js to run this app. You can pull the pre-built images directly from Docker Hub.

1.  **Create a file named `docker-compose.yml`** and paste this content:
    ```yaml
    version: '3.8'
    services:
      backend:
        image: superkk11/hospital-backend:v1
        ports:
          - "8000:8000"
        environment:
          # Replace with your actual MongoDB URL
          - MONGODB_URL=mongodb+srv://your_user:your_pass@cluster.mongodb.net/hospital_db
      frontend:
        image: superkk11/hospital-frontend:v1
        ports:
          - "5173:80"
        depends_on:
          - backend
    ```

2.  **Run the application:**
    ```bash
    docker-compose up
    ```

3.  **Open the App:** [http://localhost:5173](http://localhost:5173)