import { Link } from "react-router-dom";
import { ArrowLeft, Cookie } from "lucide-react";
import { ThemeToggle } from "../../components/ThemeToggle";

export default function CookiePolicyPage() {
  return (
    <div className="min-h-screen bg-canvas">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10">
        <div className="flex items-center justify-between mb-10">
          <Link to="/" className="flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition-colors">
            <ArrowLeft size={16} /> Back to home
          </Link>
          <ThemeToggle />
        </div>

        <div className="flex items-center gap-3 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gold/10 ring-1 ring-gold/25">
            <Cookie size={20} className="text-gold" />
          </div>
          <div>
            <h1 className="font-display text-3xl text-text-primary">Cookie Policy</h1>
            <p className="text-sm text-text-muted mt-0.5">Last updated: April 2026</p>
          </div>
        </div>

        <div className="card p-6 sm:p-8 space-y-8 text-text-secondary leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">1. What Are Cookies</h2>
            <p>
              Cookies are small text files stored on your device when you visit a website. They are widely
              used to make websites work efficiently and to provide information to site owners. We use
              cookies and similar technologies (localStorage) to operate the AI DD platform.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">2. Cookies We Use</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-canvas-border rounded-lg overflow-hidden">
                <thead>
                  <tr className="bg-canvas-subtle">
                    <th className="text-left p-3 font-semibold text-text-primary">Name</th>
                    <th className="text-left p-3 font-semibold text-text-primary">Type</th>
                    <th className="text-left p-3 font-semibold text-text-primary">Purpose</th>
                    <th className="text-left p-3 font-semibold text-text-primary">Duration</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-canvas-border">
                  <tr>
                    <td className="p-3 font-mono text-xs text-gold">access_token</td>
                    <td className="p-3">Essential</td>
                    <td className="p-3">JWT authentication token for API requests</td>
                    <td className="p-3">60 minutes</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono text-xs text-gold">refresh_token</td>
                    <td className="p-3">Essential</td>
                    <td className="p-3">Token to renew authentication without re-login</td>
                    <td className="p-3">30 days</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono text-xs text-gold">theme</td>
                    <td className="p-3">Functional</td>
                    <td className="p-3">Stores your preferred theme (light/dark/system)</td>
                    <td className="p-3">Persistent</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono text-xs text-gold">nda_accepted_*</td>
                    <td className="p-3">Essential</td>
                    <td className="p-3">Tracks NDA acceptance per project data room</td>
                    <td className="p-3">Session</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono text-xs text-gold">cookie_consent</td>
                    <td className="p-3">Essential</td>
                    <td className="p-3">Records your cookie consent preference</td>
                    <td className="p-3">1 year</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">3. Cookie Categories</h2>
            <div className="space-y-4">
              <div className="bg-canvas-subtle border border-canvas-border rounded-lg p-4">
                <h3 className="font-semibold text-text-primary mb-1">Essential Cookies</h3>
                <p>
                  Required for the platform to function. These cannot be disabled. They include
                  authentication tokens and session management.
                </p>
              </div>
              <div className="bg-canvas-subtle border border-canvas-border rounded-lg p-4">
                <h3 className="font-semibold text-text-primary mb-1">Functional Cookies</h3>
                <p>
                  Used to remember your preferences such as theme selection. These enhance your
                  experience but are not strictly necessary.
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">4. Third-Party Cookies</h2>
            <p>
              AI DD does not use third-party tracking cookies, advertising cookies, or analytics cookies.
              We do not share cookie data with advertisers or data brokers.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">5. Managing Cookies</h2>
            <p>
              You can manage cookies through your browser settings. Note that disabling essential cookies
              will prevent you from logging in or using the platform. You can clear localStorage data
              at any time through your browser's developer tools.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">6. Updates</h2>
            <p>
              We may update this Cookie Policy from time to time. Changes will be posted on this page
              with an updated revision date. For questions, contact us at:{" "}
              <span className="text-gold">privacy@aidd.io</span>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
