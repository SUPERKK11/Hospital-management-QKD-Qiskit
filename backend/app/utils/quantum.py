import random
import hashlib

# ---------------------------------------------------------
# ⚛️ QUANTUM SIMULATION ENGINE (BB84 Protocol)
# ---------------------------------------------------------

def generate_random_bits(length):
    """Step 1: Alice generates random bits (0s and 1s)."""
    return [random.randint(0, 1) for _ in range(length)]

def generate_bases(length):
    """Step 2: Alice chooses random bases to encode qubits.
       0 = Rectilinear Base (+) | 1 = Diagonal Base (x)
    """
    return [random.randint(0, 1) for _ in range(length)]

def measure_qubits(alice_bits, alice_bases, bob_bases):
    """Step 3: Bob measures the qubits.
       If Bob chooses the SAME base as Alice, he gets the correct bit.
       If he chooses the WRONG base, he has a 50% chance of error.
    """
    bob_results = []
    for i in range(len(alice_bits)):
        if alice_bases[i] == bob_bases[i]:
            # Bases match -> Perfect transmission
            bob_results.append(alice_bits[i])
        else:
            # Bases don't match -> Quantum randomness (50% noise)
            bob_results.append(random.randint(0, 1))
    return bob_results

def sift_keys(alice_bases, bob_bases, bob_results):
    """Step 4: Sifting.
       Alice and Bob publicly compare bases (not bits!).
       They keep bits only where their bases MATCHED.
    """
    sifted_key = []
    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            sifted_key.append(bob_results[i])
    return sifted_key

def simulate_qkd_exchange(key_length=128):
    """
    Runs a full simulation of Alice and Bob creating a secret key.
    Returns: A 256-bit Hash of the shared key (for AES encryption).
    """
    # 1. Setup
    n_qubits = key_length * 4  # We need extra qubits because many get discarded
    
    # 2. Alice prepares qubits
    alice_bits = generate_random_bits(n_qubits)
    alice_bases = generate_bases(n_qubits)
    
    # 3. Bob measures qubits (randomly choosing bases)
    bob_bases = generate_bases(n_qubits)
    bob_results = measure_qubits(alice_bits, alice_bases, bob_bases)
    
    # 4. Sifting (Discarding bad measurements)
    shared_key_bits = sift_keys(alice_bases, bob_bases, bob_results)
    
    # 5. Convert bits to a string
    shared_key_str = "".join(map(str, shared_key_bits))
    
    # 6. Final Polish: Hash it to make a strong password for AES
    final_key = hashlib.sha256(shared_key_str.encode()).hexdigest()
    
    return {
        "success": True,
        "raw_bits_count": len(shared_key_bits),
        "final_key": final_key
    }