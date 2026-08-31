export const FAQ_ITEMS = [
  {
    question: "What does a \"VERIFIED\" result actually mean?",
    answer:
      "It means the exact file you uploaded matches the SHA-256 fingerprint that was signed by the issuing institution's private key, and that signature has been mathematically validated with Ed25519 — and the signing key was active (not revoked) at verification time.",
  },
  {
    question: "What's the difference between the cryptographic result and the AI analysis?",
    answer:
      "The cryptographic result (VERIFIED / MODIFIED / UNSIGNED / REVOKED / INVALID) is authoritative — it's mathematical proof. The AI-assisted media analysis is a separate, advisory-only signal that flags possible manipulation patterns in images, audio, video, or documents. It never changes the cryptographic verdict.",
  },
  {
    question: "How do institutions sign a document?",
    answer:
      "An institution's private Ed25519 signing key never touches PramaanScan's servers or network. Signing happens in a secure, external, offline process. Only the resulting signature and the document's SHA-256 fingerprint are submitted to register a communication.",
  },
  {
    question: "What happens if a signing key is compromised?",
    answer:
      "An administrator can revoke the key immediately. Every subsequent verification of any document signed with that key will report the key as REVOKED, even if the signature itself is mathematically valid.",
  },
  {
    question: "Can a communication be edited after it's published?",
    answer:
      "Yes, but never silently. Every edit creates a new, separately-signed version. The complete version history is preserved and publicly visible — nothing is overwritten or deleted.",
  },
  {
    question: "What if I scan a QR code and the result says UNSIGNED or INVALID?",
    answer:
      "UNSIGNED means the file's fingerprint doesn't match any registered communication. INVALID means a communication ID was found but the signature failed cryptographic validation. In both cases, treat the document as unverified and contact the institution directly.",
  },
  {
    question: "Is my uploaded file stored by PramaanScan?",
    answer:
      "Verification works by computing a cryptographic fingerprint of your file and comparing it against registered records — your file content itself is not required to be retained for that comparison to work.",
  },
  {
    question: "Which institutions can use PramaanScan?",
    answer:
      "Government departments, universities and examination boards, regulatory authorities, and other public-sector institutions can be onboarded by a PramaanScan administrator as verified issuers.",
  },
];
