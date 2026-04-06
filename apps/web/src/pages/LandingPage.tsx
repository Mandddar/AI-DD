import { Link } from "react-router-dom";
import {
  ShieldCheck,
  FileSearch,
  Zap,
  BarChart3,
  ArrowRight,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  Lock,
  Globe,
  Menu,
  X,
} from "lucide-react";
import { ThemeToggle } from "../components/ThemeToggle";
import { useState } from "react";

// ─── Navbar ───────────────────────────────────────────────────────────────────
function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 inset-x-0 z-50 border-b border-canvas-border/60 bg-canvas/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gold/10 ring-1 ring-gold/30">
            <span className="font-display text-base font-semibold text-gold">DD</span>
          </div>
          <span className="font-display text-xl text-text-primary">AI DD</span>
        </div>

        {/* Desktop nav */}
        <div className="hidden sm:flex items-center gap-3">
          <ThemeToggle />
          <Link
            to="/login"
            className="text-base text-text-secondary hover:text-text-primary transition-colors px-4 py-2"
          >
            Sign in
          </Link>
          <Link to="/register" className="btn-primary text-base">
            Get started
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button className="sm:hidden p-2 text-text-secondary" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="sm:hidden border-t border-canvas-border bg-canvas-card px-4 py-4 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <span className="text-xs text-text-muted font-medium">Theme</span>
            <ThemeToggle />
          </div>
          <Link to="/login" onClick={() => setMenuOpen(false)} className="block text-base text-text-secondary py-2">Sign in</Link>
          <Link to="/register" onClick={() => setMenuOpen(false)} className="btn-primary w-full text-base justify-center">Get started</Link>
        </div>
      )}
    </nav>
  );
}

// ─── Hero ─────────────────────────────────────────────────────────────────────
function Hero() {
  return (
    <section className="relative pt-28 sm:pt-32 pb-16 sm:pb-24 overflow-hidden">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 -translate-x-1/2 h-[400px] sm:h-[600px] w-[600px] sm:w-[900px] rounded-full bg-gold/5 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        {/* Badge */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-gold/20 bg-gold/5 px-4 py-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-gold animate-pulse" />
          <span className="text-xs sm:text-sm font-medium text-gold tracking-wide">AI-Powered M&A Due Diligence</span>
        </div>

        {/* Headline */}
        <h1 className="font-display text-3xl sm:text-5xl md:text-6xl lg:text-7xl leading-tight text-text-primary">
          Close deals faster.
          <br />
          <span className="text-gold">Miss nothing.</span>
        </h1>

        <p className="mx-auto mt-4 sm:mt-6 max-w-2xl text-base sm:text-xl text-text-secondary leading-relaxed px-2">
          AI DD automates the most labour-intensive parts of due diligence - document review, red-flag detection, and risk scoring - so your advisors focus on decisions, not reading.
        </p>

        {/* CTAs */}
        <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
          <Link to="/register" className="btn-primary gap-2 text-base px-6 py-2.5 w-full sm:w-auto justify-center">
            Start free trial <ArrowRight size={17} />
          </Link>
          <Link to="/login" className="flex items-center gap-1.5 text-base text-text-secondary hover:text-text-primary transition-colors">
            Sign in to your account <ChevronRight size={16} />
          </Link>
        </div>

        {/* Social proof strip */}
        <div className="mt-10 sm:mt-14 grid grid-cols-2 sm:flex sm:items-center sm:justify-center gap-6 sm:gap-8 text-text-muted">
          {[
            { value: "2×", label: "faster reviews" },
            { value: "98%", label: "doc coverage" },
            { value: "4", label: "workstreams" },
            { value: "< 5 min", label: "to first findings" },
          ].map(({ value, label }) => (
            <div key={label} className="text-center">
              <p className="font-display text-2xl text-text-primary">{value}</p>
              <p className="text-sm mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Static data ──────────────────────────────────────────────────────────────
const MOCK_FINDINGS = [
  { label: "Critical", text: "Change-of-control clause in 2 customer contracts - consent required before ownership transfer.", color: "text-risk-high bg-risk-high/10" },
  { label: "High", text: "Transfer pricing documentation gap - management fee lacks arm's-length substantiation.", color: "text-risk-medium bg-risk-medium/10" },
  { label: "Medium", text: "IP assignment agreements missing for 3 freelance contractors engaged in FY2023.", color: "text-gold bg-gold/10" },
];

const WORKSTREAMS = [
  { name: "General", count: "4", color: "text-risk-low", active: false },
  { name: "Legal", count: "7", color: "text-gold", active: true },
  { name: "Tax", count: "3", color: "text-text-muted", active: false },
  { name: "Finance", count: "2", color: "text-text-muted", active: false },
];

// ─── Mock UI Preview ──────────────────────────────────────────────────────────
function UIPreview() {
  return (
    <section className="py-8">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <div className="rounded-2xl border border-canvas-border bg-canvas-card shadow-2xl overflow-hidden">
          {/* Window chrome */}
          <div className="flex items-center gap-2 border-b border-canvas-border bg-canvas-subtle px-4 py-3">
            <div className="h-3 w-3 rounded-full bg-risk-high/60" />
            <div className="h-3 w-3 rounded-full bg-risk-medium/60" />
            <div className="h-3 w-3 rounded-full bg-risk-low/60" />
            <span className="ml-3 text-xs sm:text-sm text-text-muted font-mono hidden sm:inline">AI DD - MediTech GmbH - Analysis Run #4</span>
          </div>

          {/* Mobile: stack, Desktop: side by side */}
          <div className="grid grid-cols-1 md:grid-cols-3 md:divide-x divide-canvas-border">
            {/* Sidebar mock - hidden on small screens */}
            <div className="hidden md:block col-span-1 bg-canvas-subtle p-4 space-y-1">
              <p className="text-sm text-text-muted uppercase tracking-wider mb-3">Workstreams</p>
              {WORKSTREAMS.map((ws) => (
                <div key={ws.name} className={`flex items-center justify-between rounded-lg px-3 py-2 text-base ${ws.active ? "bg-gold/10 text-gold" : "text-text-secondary"}`}>
                  <span>{ws.name}</span>
                  <span className={`text-sm font-medium ${ws.color}`}>{ws.count}</span>
                </div>
              ))}
              <div className="mt-4 pt-4 border-t border-canvas-border">
                <p className="text-sm text-text-muted uppercase tracking-wider mb-2">Run Status</p>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-risk-low" />
                  <span className="text-sm text-risk-low">Completed</span>
                </div>
                <p className="mt-1 text-sm text-text-muted">16 findings · 3 critical</p>
              </div>
            </div>

            {/* Findings list mock */}
            <div className="md:col-span-2 divide-y divide-canvas-border">
              <div className="px-4 py-3 flex items-center justify-between">
                <p className="text-base font-semibold text-text-primary">Findings - Legal</p>
                <span className="text-sm text-text-muted">7 items</span>
              </div>
              {MOCK_FINDINGS.map(({ label, text, color }) => (
                <div key={label} className="px-4 py-3.5">
                  <div className="flex items-start gap-3">
                    <span className={`mt-0.5 inline-flex shrink-0 rounded-full px-2 py-0.5 text-sm font-semibold ${color}`}>
                      {label}
                    </span>
                    <p className="text-sm text-text-secondary leading-relaxed">{text}</p>
                  </div>
                </div>
              ))}
              <div className="px-4 py-3 text-center">
                <span className="text-sm text-text-muted">4 more findings…</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Features ─────────────────────────────────────────────────────────────────
const FEATURES = [
  { icon: Zap, title: "Instant document processing", body: "Upload PDFs, Word, and Excel files. Text extraction begins immediately - no manual copy-paste, no delays." },
  { icon: ShieldCheck, title: "AI red-flag detection", body: "Agents scan every document for change-of-control clauses, IP gaps, litigation risk, tax exposure, and more." },
  { icon: BarChart3, title: "Workstream risk scoring", body: "Legal, Tax, Finance, and General workstreams are scored independently so your team knows exactly where to focus." },
  { icon: FileSearch, title: "Reviewer workflow", body: "Approve or reject each finding. Every decision is logged. Full audit trail for your compliance team." },
  { icon: Lock, title: "Secure by design", body: "Role-based access, JWT authentication, and encrypted storage. Your deal data never leaves your infrastructure." },
  { icon: Globe, title: "Multi-deal management", body: "Manage a full pipeline of deals simultaneously. Each deal has its own workstream, documents, and analysis runs." },
];

function Features() {
  return (
    <section className="py-16 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-10 sm:mb-14 text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-gold mb-3">Capabilities</p>
          <h2 className="font-display text-3xl sm:text-4xl text-text-primary">Everything a deal team needs</h2>
          <p className="mt-4 text-text-secondary max-w-xl mx-auto">
            Built specifically for M&A advisors, legal counsel, and financial analysts running buy-side and sell-side mandates.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="card p-6 group hover:border-gold/20 transition-colors">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gold/10 ring-1 ring-gold/20 group-hover:bg-gold/15 transition-colors">
                <Icon size={20} className="text-gold" />
              </div>
              <h3 className="mb-2 text-base font-semibold text-text-primary">{title}</h3>
              <p className="text-sm leading-relaxed text-text-secondary">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── How it works ─────────────────────────────────────────────────────────────
const STEPS = [
  { step: "01", title: "Create a deal", body: "Set up a new deal with company details, legal form, industry, and deal type. Invite your team." },
  { step: "02", title: "Upload the data room", body: "Drag and drop documents into Legal, Tax, Finance, or General workstreams. Processing starts automatically." },
  { step: "03", title: "Run the AI agents", body: "Select which workstreams to analyse. Our agents read every document and surface findings within minutes." },
  { step: "04", title: "Review & report", body: "Your advisors review each finding, approve or reject, and export a clean risk report for the deal committee." },
];

function HowItWorks() {
  return (
    <section className="py-16 sm:py-24 border-t border-canvas-border">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-10 sm:mb-14 text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-gold mb-3">Process</p>
          <h2 className="font-display text-3xl sm:text-4xl text-text-primary">From data room to red flags in minutes</h2>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(({ step, title, body }) => (
            <div key={step}>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-canvas-card border border-canvas-border">
                <span className="font-display text-xl text-gold">{step}</span>
              </div>
              <h3 className="mb-2 text-base font-semibold text-text-primary">{title}</h3>
              <p className="text-sm leading-relaxed text-text-secondary">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const CTA_TRUST_ITEMS = [
  "No credit card required",
  "Full feature access during trial",
  "Your data stays on your infrastructure",
];

// ─── CTA Section ──────────────────────────────────────────────────────────────
function CTASection() {
  return (
    <section className="py-16 sm:py-24 border-t border-canvas-border">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center">
        <h2 className="font-display text-3xl sm:text-4xl text-text-primary mb-4">
          Ready to run your first deal?
        </h2>
        <p className="text-text-secondary mb-8">
          Set up an account in under two minutes. Your first analysis run is on us.
        </p>

        <Link to="/register" className="btn-primary gap-2 text-base px-8 py-3 inline-flex">
          Create free account <ArrowRight size={17} />
        </Link>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
          {CTA_TRUST_ITEMS.map((item) => (
            <div key={item} className="flex items-center gap-2 text-sm text-text-muted">
              <CheckCircle size={15} className="text-risk-low shrink-0" />
              {item}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Footer ───────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="border-t border-canvas-border py-8">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-5">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gold/10">
              <span className="font-display text-base text-gold">DD</span>
            </div>
            <span className="text-base text-text-muted">AI DD</span>
          </div>
          <div className="flex items-center gap-2 text-xs sm:text-sm text-text-muted text-center">
            <AlertTriangle size={13} className="text-gold shrink-0" />
            AI-generated findings require human verification.
          </div>
          <p className="text-sm text-text-muted">© {new Date().getFullYear()} AI DD</p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-sm text-text-muted">
          <Link to="/privacy" className="hover:text-text-primary transition-colors">Privacy Policy</Link>
          <Link to="/terms" className="hover:text-text-primary transition-colors">Terms & Conditions</Link>
          <Link to="/cookies" className="hover:text-text-primary transition-colors">Cookie Policy</Link>
        </div>
      </div>
    </footer>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <Hero />
        <UIPreview />
        <Features />
        <HowItWorks />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
