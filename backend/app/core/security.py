# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt
import secrets
import hashlib

# --- 1. CONFIGURATION ---
# Setup Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Setup Token Configuration
SECRET_KEY = "super_secret_key_change_this_in_production"
ALGORITHM = "HS256"

# --- 2. AUTHENTICATION FUNCTIONS (Login) ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- 3. QUANTUM KEY DISTRIBUTION (The Missing Part!) ---

class QKDProtocol:
    """
    Simulates the BB84 Quantum Key Distribution protocol.
    """
    def __init__(self, num_bits: int = 256):
        self.num_bits = num_bits  # Length of the raw bit stream

    def _generate_quantum_bits(self):
        """Generates random bits (0 or 1) and random bases (+ or x)."""
        bits = [secrets.randbelow(2) for _ in range(self.num_bits)]
        bases = [secrets.randbelow(2) for _ in range(self.num_bits)]
        return bits, bases

    def _measure_bits(self, sender_bases, receiver_bases, sender_bits):
        """Simulates measurement. If bases match, bit is kept."""
        measured_bits = []
        for s_base, r_base, bit in zip(sender_bases, receiver_bases, sender_bits):
            if s_base == r_base:
                measured_bits.append(bit)
            else:
                # Random outcome (Heisenberg Uncertainty)
                measured_bits.append(secrets.randbelow(2))
        return measured_bits

    def _sifting(self, sender_bases, receiver_bases, measured_bits):
        """Sifting Phase: Keep bits where bases matched."""
        sifted_key = []
        for s_base, r_base, bit in zip(sender_bases, receiver_bases, measured_bits):
            if s_base == r_base:
                sifted_key.append(bit)
        return sifted_key

    def execute_bb84_protocol(self) -> Dict[str, Any]:
        """Runs the full BB84 simulation loop."""
        
        # 1. Alice prepares qubits
        alice_bits, alice_bases = self._generate_quantum_bits()

        # 2. Bob generates his measuring bases
        bob_bases = [secrets.randbelow(2) for _ in range(self.num_bits)]

        # 3. Transmission & Measurement
        bob_measured_bits = self._measure_bits(alice_bases, bob_bases, alice_bits)

        # 4. Sifting
        sifted_key_bits = self._sifting(alice_bases, bob_bases, bob_measured_bits)

        # 5. Key Generation
        key_string = "".join(map(str, sifted_key_bits))
        final_key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        shared_key_bytes = hashlib.sha256(key_string.encode()).digest()
        
        # 6. Return Result (With the fix for your KeyError)
        return {
            "shared_key": shared_key_bytes,
            "final_key_hash": final_key_hash,
            "raw_bits_length": self.num_bits,      # 👈 The fix is here!
            "sifted_bits_count": len(sifted_key_bits),
            "protocol": "BB84 (Simulated)"
        }