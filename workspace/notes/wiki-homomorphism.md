# Wiki Swarm: Homomorphism

- Resolved topic: `Homomorphism`
- Topic source: `human-requested`
- Depth: 1
- Fanout: 7
- Language: `en`
- Generated: 2026-03-23 UTC

## Homomorphism (depth 0)
- URL: https://en.wikipedia.org/wiki/Homomorphism
- Summary: In algebra, a homomorphism is a structure-preserving map between two algebraic structures of the same type (groups, rings, vector spaces, etc.). The word comes from Greek homos ("same") + morphe ("form"). Term attributed to Felix Klein (1892).

### Core definition
A map f: A → B between two sets equipped with the same algebraic structure preserves operations:
- **Binary**: f(x · y) = f(x) · f(y)
- **General arity k**: f(μ_A(a₁,...,aₖ)) = μ_B(f(a₁),...,f(aₖ))
- **0-ary (constants)**: identity elements must map to identity elements

### Key examples
1. **Exponential function**: e^(x+y) = e^x · e^y — homomorphism from (ℝ,+) to (ℝ⁺,×)
2. **Scalar matrices**: f(r) = [[r,0],[0,r]] — ring homomorphism from ℝ to Mat₂(ℝ)
3. **Absolute value**: |z₁z₂| = |z₁||z₂| — group homomorphism from (ℂ\0,×) to (ℝ⁺,×)
   - Note: |z₁+z₂| ≠ |z₁|+|z₂|, so NOT a ring homomorphism (preserves × but not +)
4. **Monoid**: f(x) = 2^x from (ℕ,+,0) to (ℕ,×,1) — injective but not surjective

### Special types
| Type | Definition | Key property |
|------|-----------|-------------|
| **Isomorphism** | Bijective homomorphism | Invertible; structures are "the same" |
| **Endomorphism** | Homomorphism A → A | Maps structure to itself |
| **Automorphism** | Bijective endomorphism | Self-isomorphism |
| **Monomorphism** | Injective homomorphism | Left-cancellable: f∘g = f∘h → g = h |
| **Epimorphism** | Surjective homomorphism | Right-cancellable: g∘f = h∘f → g = h |

### Kernel
- **Definition**: ker(f) = equivalence relation ~ where a ~ b iff f(a) = f(b)
- It's a congruence relation on X
- **First isomorphism theorem**: im(f) ≅ X/~
- For groups: kernel = equivalence class of identity element → normal subgroup
- For rings: kernel → ideal (two-sided ideal for non-commutative rings)
- For vector spaces: kernel → subspace

### Relational structures (model theory generalization)
- Extends beyond algebraic operations to include relations
- h preserves functions: h(F^A(a₁,...,aₙ)) = F^B(h(a₁),...,h(aₙ))
- h preserves relations: R^A(a₁,...,aₙ) → R^B(h(a₁),...,h(aₙ))
- Special case with one binary relation = graph homomorphism

### Formal language theory
- Given alphabets Σ₁, Σ₂: h: Σ₁* → Σ₂* is homomorphism if h(uv) = h(u)h(v)
- Determined entirely by h's values on individual characters
- Types: ε-free (no letter maps to empty), coding (each letter → single letter)

### See also
- Diffeomorphism, Homomorphic encryption, Homomorphic secret sharing, Morphism, Quasimorphism

---

## Swarm relevance analysis

### Direct isomorphisms to swarm concepts
1. **Structure preservation under transformation**: Homomorphism is EXACTLY what swarm does when compacting knowledge — the compaction map must preserve operational structure (lessons that compose must still compose after compression). Violation = information-destroying compression.

2. **Kernel as compression**: The kernel of a homomorphism identifies elements that become equivalent in the image. Swarm's compaction identifies lessons that say "the same thing" — the quotient X/~ is the compressed knowledge base. First isomorphism theorem guarantees the compressed base retains all structural information.

3. **Special types map to swarm operations**:
   - Compaction = epimorphism (surjective onto compressed space, not injective — many lessons map to one)
   - Cell replication = attempted isomorphism (daughter should be structurally identical)
   - Orient = endomorphism (swarm maps its own state to prioritized state)
   - Expert dispatch = monomorphism (specialist injects domain knowledge faithfully)

4. **Formal language homomorphism**: Swarm's bridge files (CLAUDE.md → AGENTS.md → GEMINI.md) are exactly formal language homomorphisms — same operational semantics, different syntactic alphabets.

5. **Kernel detection for near-duplicates**: Two lessons L₁, L₂ with same kernel (same implications/effects) are near-duplicates even if stated differently. This is a more principled duplicate detector than string similarity.

---

## Related pages (depth 1)

### Morphism
- URL: https://en.wikipedia.org/wiki/Morphism
- Summary: In category theory, a morphism generalizes structure-preserving maps such as homomorphism between algebraic structures, functions between sets, and continuous functions between topological spaces.

### Isomorphism
- URL: https://en.wikipedia.org/wiki/Isomorphism
- Summary: A structure-preserving mapping between two structures of the same type that can be reversed by an inverse mapping. Two structures are isomorphic if such a mapping exists.

### Group homomorphism
- URL: https://en.wikipedia.org/wiki/Group_homomorphism
- Summary: Given two groups (G,∗) and (H,·), a group homomorphism h: G → H satisfies h(u∗v) = h(u)·h(v) for all u,v in G.

### Ring homomorphism
- URL: https://en.wikipedia.org/wiki/Ring_homomorphism
- Summary: A structure-preserving function f: R → S between rings that preserves addition, multiplication, and multiplicative identity.

### Kernel (algebra)
- URL: https://en.wikipedia.org/wiki/Kernel_(algebra)
- Summary: The kernel of a homomorphism describes how elements in the domain become related in the image. Captures the "information lost" by the map.

### Diffeomorphism
- URL: https://en.wikipedia.org/wiki/Diffeomorphism
- Summary: An isomorphism of differentiable manifolds — an invertible function where both the function and its inverse are continuously differentiable.

### Homomorphic encryption
- URL: https://en.wikipedia.org/wiki/Homomorphic_encryption
- Summary: Encryption that allows computations on encrypted data without decryption. The encrypted computation produces results identical to operations on plaintext. **Swarm relevance**: Could swarm operate on "encrypted" (compressed/abstracted) knowledge and still produce valid results? Homomorphic compression.
