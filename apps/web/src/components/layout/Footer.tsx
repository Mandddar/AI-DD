import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="border-t border-canvas-border bg-canvas-subtle px-4 sm:px-8 py-3">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
        <p className="text-center sm:text-left text-xs text-text-muted leading-relaxed flex-1">
          <span className="text-gold/70 font-semibold">AI Notice:</span>{" "}
          AI-generated results may be inaccurate or misleading. Responsibility lies exclusively with the human reviewer.
        </p>
        <div className="flex items-center gap-3 text-xs text-text-muted shrink-0">
          <Link to="/privacy" className="hover:text-text-secondary transition-colors">Privacy</Link>
          <span className="text-canvas-border">|</span>
          <Link to="/terms" className="hover:text-text-secondary transition-colors">Terms</Link>
          <span className="text-canvas-border">|</span>
          <Link to="/cookies" className="hover:text-text-secondary transition-colors">Cookies</Link>
        </div>
      </div>
    </footer>
  );
}
