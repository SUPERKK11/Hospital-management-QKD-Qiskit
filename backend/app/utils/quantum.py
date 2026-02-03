# backend/app/utils/quantum.py
import numpy as np
import hashlib
from typing import Dict, Any

# --- QISKIT IMPORTS (The Real Physics) ---
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

class QKDProtocol:
    def __init__(self, num_bits: int = 128):
        self.num_bits = num_bits 
        self.simulator = AerSimulator()

    def execute_bb84_protocol(self) -> Dict[str, Any]:
        n = self.num_bits
        
        # 1. Alice's Random Bits & Bases (0=Rectilinear, 1=Diagonal)
        alice_bits = np.random.randint(2, size=n)
        alice_bases = np.random.randint(2, size=n)
        
        # 2. Bob's Random Bases
        bob_bases = np.random.randint(2, size=n)

        # 3. Build Quantum Circuit
        qc = QuantumCircuit(n, n)
        for i in range(n):
            # Encode bit
            if alice_bits[i] == 1: 
                qc.x(i) 
            # Apply Basis (Hadamard Gate)
            if alice_bases[i] == 1: 
                qc.h(i)
            
            # Bob Measures (Apply Hadamard if his basis is Diagonal)
            if bob_bases[i] == 1: 
                qc.h(i)
            
            qc.measure(i, i)

        # 4. Run Simulation (Shot noise included!)
        job = self.simulator.run(qc, shots=1, memory=True)
        measured_str = job.result().get_memory()[0] 
        # Reverse because Qiskit is Little Endian
        bob_results = [int(bit) for bit in measured_str[::-1]]

        # 5. Sifting (The "Handshake")
        sifted_key = []
        for i in range(n):
            if alice_bases[i] == bob_bases[i]:
                sifted_key.append(bob_results[i])

        # 6. Final Key Generation
        key_string = "".join(map(str, sifted_key))
        
        # Hash it for AES-256 compatibility
        final_key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        shared_key_bytes = hashlib.sha256(key_string.encode()).digest()

        return {
            "shared_key": shared_key_bytes,
            "final_key_hash": final_key_hash,
            "raw_bits_length": n,
            "sifted_bits_count": len(sifted_key)
        }

# This is the function your API calls
def simulate_qkd_exchange():
    qkd = QKDProtocol(num_bits=128)
    return qkd.execute_bb84_protocol()