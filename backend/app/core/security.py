# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt
import hashlib
import numpy as np

# --- QISKIT IMPORTS (The Real Quantum Logic) ---
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# --- CONFIGURATION ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "super_secret_key_change_this_in_production"
ALGORITHM = "HS256"

# --- AUTHENTICATION ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- REAL QUANTUM KEY DISTRIBUTION ---
class QKDProtocol:
    """
    Implements the BB84 Protocol using IBM Qiskit.
    This constructs a quantum circuit to simulate photon polarization.
    """
    def __init__(self, num_bits: int = 128):
        # 128 qubits is a secure balance for server performance
        self.num_bits = num_bits 
        self.simulator = AerSimulator()

    def execute_bb84_protocol(self) -> Dict[str, Any]:
        n = self.num_bits

        # 1. ALICE GENERATES BITS & BASES
        alice_bits = np.random.randint(2, size=n)
        alice_bases = np.random.randint(2, size=n)

        # 2. BOB GENERATES BASES
        bob_bases = np.random.randint(2, size=n)

        # 3. QUANTUM CIRCUIT CONSTRUCTION
        qc = QuantumCircuit(n, n)
        for i in range(n):
            # Alice prepares: Apply X if bit is 1
            if alice_bits[i] == 1: qc.x(i)
            # Alice prepares: Apply Hadamard if basis is 1
            if alice_bases[i] == 1: qc.h(i)
            
            # Bob measures: Apply Hadamard if basis is 1
            if bob_bases[i] == 1: qc.h(i)
            qc.measure(i, i)

        # 4. EXECUTION
        job = self.simulator.run(qc, shots=1, memory=True)
        # Qiskit returns bits in reverse order (Little Endian), so we flip it
        measured_str = job.result().get_memory()[0] 
        bob_results = [int(bit) for bit in measured_str[::-1]]

        # 5. SIFTING
        sifted_key = []
        for i in range(n):
            if alice_bases[i] == bob_bases[i]:
                sifted_key.append(bob_results[i])

        # 6. FINAL KEY GENERATION
        key_string = "".join(map(str, sifted_key))
        final_key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        shared_key_bytes = hashlib.sha256(key_string.encode()).digest()

        return {
            "shared_key": shared_key_bytes,
            "final_key_hash": final_key_hash,
            "raw_bits_length": n,
            "sifted_bits_count": len(sifted_key),
            "protocol": "BB84 (IBM Qiskit Aer Simulation)"
        }

def simulate_qkd_exchange():
    qkd = QKDProtocol(num_bits=128)
    return qkd.execute_bb84_protocol()