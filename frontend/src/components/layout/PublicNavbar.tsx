import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ShieldCheck, ChevronRight, Landmark, Accessibility } from "lucide-react";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";
import { Button } from "@/components/ui/button";
import { LanguageSelector } from "./LanguageSelector";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { to: "/verify", label: "Verify Document" },
  { to: "/about", label: "About" },
  { to: "/faq", label: "FAQ" },
  { to: "/contact", label: "Contact" },
];

export function PublicNavbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/80 bg-background/90 shadow-[0_1px_0_hsl(var(--border)/.5)] backdrop-blur-xl">
      <div className="h-1.5 gov-tricolor" aria-hidden="true" />
      <div className="border-b border-border/60 bg-secondary/35">
        <div className="container flex h-8 items-center justify-between text-[11px] font-medium text-muted-foreground">
          <div className="flex min-w-0 items-center gap-2">
            <span className="gov-flag" aria-label="Indian flag" role="img" />
            <Landmark className="h-3.5 w-3.5 shrink-0 text-primary" />
            <span className="truncate">Digital public-service inspired verification platform</span>
          </div>
          <div className="hidden items-center gap-4 sm:flex"><span className="flex items-center gap-1.5"><Accessibility className="h-3.5 w-3.5" /> Accessible design</span><span>Secure • Transparent • Citizen-first</span></div>
        </div>
      </div>
      <div className="container flex h-[4.5rem] items-center justify-between gap-4">
        <Logo />
        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
          {NAV_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} className={({ isActive }) => cn("relative rounded-lg px-3.5 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground", isActive && "bg-secondary text-foreground after:absolute after:inset-x-3 after:-bottom-[18px] after:h-0.5 after:bg-primary")}>{link.label}</NavLink>
          ))}
        </nav>
        <div className="hidden items-center gap-2 lg:flex">
          <LanguageSelector />
          <ThemeToggle />
          <DropdownMenu>
            <DropdownMenuTrigger asChild><Button variant="outline" size="sm">Portal Login</Button></DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem asChild><Link to="/institution/login" className="cursor-pointer">Institution Login<ChevronRight className="ml-auto h-4 w-4 opacity-50" /></Link></DropdownMenuItem>
              <DropdownMenuItem asChild><Link to="/admin/login" className="cursor-pointer">Administrator Login<ChevronRight className="ml-auto h-4 w-4 opacity-50" /></Link></DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button asChild size="sm"><Link to="/verify"><ShieldCheck className="h-4 w-4" /> Verify Now</Link></Button>
        </div>
        <div className="flex items-center gap-1 lg:hidden">
          <LanguageSelector compact />
          <ThemeToggle />
          <Button variant="ghost" size="icon" onClick={() => setOpen((v) => !v)} aria-label="Toggle menu">{open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}</Button>
        </div>
      </div>
      <AnimatePresence>
        {open && <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-border lg:hidden">
          <div className="container flex flex-col gap-1 py-4">
            {NAV_LINKS.map((link) => <NavLink key={link.to} to={link.to} onClick={() => setOpen(false)} className="rounded-lg px-3 py-2.5 text-sm font-medium text-foreground hover:bg-secondary">{link.label}</NavLink>)}
            <div className="mt-2 flex justify-end border-t border-border pt-3"><LanguageSelector /></div>
            <div className="mt-2 grid grid-cols-2 gap-2 border-t border-border pt-3"><Button variant="outline" size="sm" asChild><Link to="/institution/login" onClick={() => setOpen(false)}>Institution</Link></Button><Button variant="outline" size="sm" asChild><Link to="/admin/login" onClick={() => setOpen(false)}>Admin</Link></Button></div>
            <Button size="sm" className="mt-2" asChild><Link to="/verify" onClick={() => setOpen(false)}><ShieldCheck className="h-4 w-4" /> Verify Now</Link></Button>
          </div>
        </motion.div>}
      </AnimatePresence>
    </header>
  );
}
