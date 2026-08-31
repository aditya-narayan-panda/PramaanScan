import { Link } from "react-router-dom";
import { Logo } from "./Logo";
import { ShieldCheck, Github, Mail } from "lucide-react";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { to: "/verify", label: "Verify a Document" },
      { to: "/about", label: "About PramaanScan" },
      { to: "/faq", label: "FAQ" },
    ],
  },
  {
    title: "Portals",
    links: [
      { to: "/institution/login", label: "Institution Login" },
      { to: "/admin/login", label: "Administrator Login" },
    ],
  },
  {
    title: "Support",
    links: [
      { to: "/contact", label: "Contact Us" },
      { to: "/faq", label: "Help Center" },
    ],
  },
];

export function PublicFooter() {
  return (
    <footer className="border-t border-border bg-secondary/30">
      <div className="container py-14">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              Cryptographic verification for official institutional communications. Every
              certificate, notice, and press release is Ed25519-signed and independently
              verifiable — no trust required.
            </p>
            <div className="mt-5 flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <ShieldCheck className="h-4 w-4 text-primary" />
              Government-grade cryptographic provenance
            </div>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="font-display text-sm font-semibold">{col.title}</h4>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.to}
                      className="text-sm text-muted-foreground transition-colors hover:text-primary"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-6 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} PramaanScan. All rights reserved.
          </p>
          <div className="flex items-center gap-4 text-muted-foreground">
            <a href="mailto:support@pramaanscan.example" aria-label="Email" className="hover:text-primary">
              <Mail className="h-4 w-4" />
            </a>
            <a href="https://github.com" target="_blank" rel="noreferrer" aria-label="GitHub" className="hover:text-primary">
              <Github className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
