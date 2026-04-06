import { Link } from "react-router-dom";
import { ArrowLeft, FileText } from "lucide-react";
import { ThemeToggle } from "../../components/ThemeToggle";

export default function TermsPage() {
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
            <FileText size={20} className="text-gold" />
          </div>
          <div>
            <h1 className="font-display text-3xl text-text-primary">Terms & Conditions</h1>
            <p className="text-sm text-text-muted mt-0.5">Last updated: April 2026</p>
          </div>
        </div>

        <div className="card p-6 sm:p-8 space-y-8 text-text-secondary leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">1. Acceptance of Terms</h2>
            <p>
              By accessing or using the AI DD platform ("Service"), you agree to be bound by these Terms &
              Conditions. If you do not agree, you may not use the Service. These terms apply to all users,
              including administrators, advisors, sellers, and buyers.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">2. Description of Service</h2>
            <p>
              AI DD is an AI-powered M&A due diligence platform that provides document management, automated
              analysis, risk scoring, and report generation for mergers and acquisitions advisory. The Service
              includes document upload, AI-driven analysis across legal, tax, finance, and general workstreams,
              and collaborative review workflows.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">3. AI Disclaimer</h2>
            <div className="bg-canvas-subtle border border-canvas-border rounded-lg p-4">
              <p className="text-risk-high font-medium mb-2">Important Notice</p>
              <p>
                AI-generated results may be <strong className="text-text-primary">inaccurate, incomplete, or
                misleading</strong>. The AI works exclusively with uploaded documents and does not have access
                to external data sources. All AI-generated findings, risk assessments, and reports must be
                independently verified by qualified professionals before reliance. AI DD does not replace
                qualified legal, tax, or financial advisory services.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">4. User Accounts</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>You must provide accurate and complete registration information.</li>
              <li>You are responsible for maintaining the confidentiality of your credentials.</li>
              <li>You must not share your account or allow unauthorized access.</li>
              <li>We may suspend or terminate accounts that violate these terms.</li>
              <li>Two-factor authentication (2FA) is available and recommended for all accounts.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">5. Acceptable Use</h2>
            <p className="mb-3">You agree not to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Use the Service for any unlawful purpose or in violation of any applicable laws.</li>
              <li>Upload malicious files, viruses, or harmful content.</li>
              <li>Attempt to gain unauthorized access to other users' projects or data.</li>
              <li>Reverse-engineer, decompile, or disassemble any part of the Service.</li>
              <li>Use the Service to process data in violation of applicable data protection regulations.</li>
              <li>Share confidential deal information obtained through the platform with unauthorized parties.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">6. Confidentiality</h2>
            <p>
              All documents, data, and analysis results within a project are confidential. Users must accept
              a Non-Disclosure Agreement (NDA) before accessing any deal's data room. The NDA obligations
              survive termination of access to the platform.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">7. Intellectual Property</h2>
            <p>
              You retain ownership of all documents and data you upload. We retain ownership of the platform,
              its design, code, and AI models. AI-generated findings and reports are licensed to you for use
              in connection with the relevant deal.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">8. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, AI DD shall not be liable for any indirect, incidental,
              special, consequential, or punitive damages, including loss of profits, data, or business
              opportunities, arising from your use of the Service. Our total liability shall not exceed the
              amount paid by you for the Service in the twelve months preceding the claim.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">9. Indemnification</h2>
            <p>
              You agree to indemnify and hold harmless AI DD from any claims, damages, or expenses arising
              from your use of the Service, your violation of these terms, or your violation of any rights
              of a third party.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">10. Termination</h2>
            <p>
              Either party may terminate this agreement at any time. Upon termination, your access to the
              Service will cease. You may request deletion of your data in accordance with our{" "}
              <Link to="/privacy" className="text-gold hover:text-gold-light transition-colors">Privacy Policy</Link>.
              Provisions that by their nature should survive termination (confidentiality, limitation of
              liability, indemnification) shall survive.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">11. Changes to Terms</h2>
            <p>
              We reserve the right to modify these terms at any time. We will notify registered users of
              material changes via email or in-app notification. Continued use of the Service after changes
              constitutes acceptance of the updated terms.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">12. Governing Law</h2>
            <p>
              These terms shall be governed by and construed in accordance with applicable law. Any disputes
              shall be resolved through binding arbitration or in the courts of the applicable jurisdiction.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">13. Contact</h2>
            <p>
              For questions about these terms, contact us at:{" "}
              <span className="text-gold">legal@aidd.io</span>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
