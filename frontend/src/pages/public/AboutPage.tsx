import { motion } from "framer-motion";
import { ShieldCheck, KeyRound, History, Sparkles, Building2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const PRINCIPLES = [
  {
    icon: KeyRound,
    title: "Cryptography over trust",
    description: "Every signature is Ed25519. Every fingerprint is SHA-256. Verification is math, not a promise.",
  },
  {
    icon: History,
    title: "Nothing is silently changed",
    description: "Edits create new signed versions. The full provenance trail stays visible and auditable forever.",
  },
  {
    icon: Sparkles,
    title: "AI assists, never decides",
    description: "Media analysis is a clearly-labeled advisory signal — it can never override a cryptographic result.",
  },
  {
    icon: Building2,
    title: "Built for institutions",
    description: "Government departments, universities, and regulatory bodies each manage an independent signing identity.",
  },
];

export default function AboutPage() {
  return (
    <div>
      <section className="border-b border-border bg-secondary/30 py-16 sm:py-20">
        <div className="container max-w-3xl text-center">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h1 className="mt-5 font-display text-3xl font-bold sm:text-4xl">About PramaanScan</h1>
            <p className="mt-4 text-base leading-relaxed text-muted-foreground">
              "Pramaan" (प्रमाण) means proof. PramaanScan exists so that anyone — a citizen, a
              journalist, another institution — can independently confirm that an official
              communication genuinely came from the institution it claims to, without needing to
              trust a phone number, an email domain, or a logo.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="container py-16 sm:py-20">
        <h2 className="text-center font-display text-2xl font-bold">Our principles</h2>
        <div className="mt-10 grid gap-5 sm:grid-cols-2">
          {PRINCIPLES.map((p) => (
            <Card key={p.title}>
              <CardContent className="flex gap-4 p-6">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <p.icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-display text-base font-semibold">{p.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{p.description}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-secondary/30 py-16">
        <div className="container max-w-2xl text-center">
          <h2 className="font-display text-xl font-bold">How verification stays independent</h2>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
            A signature is verified against the institution's public key using the Ed25519
            algorithm — the same primitive used to secure SSH keys and modern TLS handshakes.
            Anyone can, in principle, re-implement the verification logic themselves and reach
            the identical result. PramaanScan doesn't ask you to trust it; it gives you the proof.
          </p>
        </div>
      </section>
    </div>
  );
}
