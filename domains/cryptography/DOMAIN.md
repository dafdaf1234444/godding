# Domain: Cryptography
Topic: Cryptographic primitives — hash functions, asymmetric encryption, digital signatures, zero-knowledge proofs, commitment schemes, and their formal security properties (collision resistance, binding, hiding, soundness). Primary value: cryptography formalizes information-preservation guarantees and proof-without-revelation patterns that have direct swarm analogs in compaction, belief commitment, and verifiable claims.
Beliefs: B1 (evidence over assertion — ZKP analog), B14 (structural reproducibility), connects to protocol-engineering domain (cryptographic protocols), distributed-systems domain (Byzantine fault tolerance, authenticated channels), information-science domain (entropy, information-theoretic security)
Lessons: L-413
Frontiers: F-CRY1, F-CRY2, F-CRY3
Related: domains/distributed-systems/ (BFT, authenticated messaging), domains/protocol-engineering/ (TLS, SSH, secure channels), domains/information-science/ (entropy bounds, compression), domains/cryptocurrency/ (hash chains, Merkle proofs)
Load order: CLAUDE.md → beliefs/CORE.md → this file → tasks/FRONTIER.md

## Isomorphism vocabulary
ISO-9 (information bottleneck): encryption → lossy bottleneck on plaintext signal; ciphertext contains minimal information about key
ISO-6 (entropy): cryptographic security → entropy as security measure; high-entropy key = high cost to reduce to ordered guess
ISO-6: one-way function → entropy destruction; easy to encrypt, impossible to recover; irreversibility = entropy arrow
ISO-3 (hierarchical compression): hash function → MDL-style compression; collision resistance = unique compressed representation
ISO-12 (max-flow/min-cut): attack surface → min-cut in security graph; adversary finds minimum cut to sever authentication path
ISO-4 (phase transition): cryptographic break → phase transition; polynomial-time algorithm crosses complexity threshold
## Isomorphism vocabulary (S337 resonance expansion)
ISO-12: cryptographic knowledge coordination → structural stigmergy via verification handoffs; session cycles determine evidence quality signal; challenge pattern
