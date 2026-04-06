import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Cookie, X } from "lucide-react";

const CONSENT_KEY = "cookie_consent";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem(CONSENT_KEY);
    if (!consent) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem(CONSENT_KEY, "accepted");
    setVisible(false);
  };

  const decline = () => {
    localStorage.setItem(CONSENT_KEY, "declined");
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 inset-x-0 z-[100] p-4 animate-slide-in">
      <div className="mx-auto max-w-3xl rounded-xl border border-canvas-border bg-canvas-card shadow-elevated p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <div className="hidden sm:flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gold/10">
            <Cookie size={20} className="text-gold" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-text-primary mb-1">Cookie Notice</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              We use essential cookies for authentication and session management. No tracking
              or advertising cookies are used. By continuing to use AI DD, you consent to our use
              of essential cookies. Learn more in our{" "}
              <Link to="/cookies" className="text-gold hover:text-gold-light transition-colors underline">
                Cookie Policy
              </Link>
              .
            </p>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 mt-4">
              <button onClick={accept} className="btn-primary text-sm px-5 py-2 justify-center">
                Accept All
              </button>
              <button onClick={decline} className="btn-ghost text-sm px-5 py-2 justify-center">
                Essential Only
              </button>
              <Link to="/cookies" className="btn-ghost text-sm px-5 py-2 justify-center">
                Cookie Policy
              </Link>
            </div>
          </div>
          <button
            onClick={decline}
            className="text-text-muted hover:text-text-secondary transition-colors p-1 shrink-0"
            title="Dismiss"
          >
            <X size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
