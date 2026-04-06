import { Link } from "react-router-dom";
import { ArrowLeft, Shield } from "lucide-react";
import { ThemeToggle } from "../../components/ThemeToggle";

export default function PrivacyPolicyPage() {
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
            <Shield size={20} className="text-gold" />
          </div>
          <div>
            <h1 className="font-display text-3xl text-text-primary">Privacy Policy</h1>
            <p className="text-sm text-text-muted mt-0.5">Last updated: April 2026</p>
          </div>
        </div>

        <div className="card p-6 sm:p-8 space-y-8 text-text-secondary leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">1. Introduction</h2>
            <p>
              AI DD ("we", "our", "us") operates the AI DD M&A Due Diligence Platform. This Privacy Policy
              explains how we collect, use, disclose, and safeguard your information when you use our platform.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">2. Information We Collect</h2>
            <p className="mb-3">We collect the following types of information:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong className="text-text-primary">Account Information:</strong> Name, email address, and encrypted password when you register.</li>
              <li><strong className="text-text-primary">Deal Data:</strong> Documents, financial data, and analysis results uploaded to or generated within your projects.</li>
              <li><strong className="text-text-primary">Usage Data:</strong> IP address, browser type, pages visited, and timestamps for audit trail and security purposes.</li>
              <li><strong className="text-text-primary">Cookies:</strong> Essential cookies for authentication and session management. See our <Link to="/cookies" className="text-gold hover:text-gold-light transition-colors">Cookie Policy</Link>.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>To provide and maintain the platform, including AI-powered document analysis.</li>
              <li>To authenticate users and enforce role-based access control.</li>
              <li>To generate audit trails as required for M&A compliance.</li>
              <li>To improve platform performance and develop new features.</li>
              <li>To communicate with you about your account or service updates.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">4. AI Processing</h2>
            <p>
              Our platform uses artificial intelligence (including third-party LLM providers) to analyse uploaded
              documents and generate findings. Document content may be sent to AI service providers for processing.
              We select providers that do not retain or train on your data. AI-generated results are stored within
              your project and are subject to the same access controls as all other data.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">5. Data Sharing</h2>
            <p className="mb-3">We do not sell your personal data. We may share information with:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong className="text-text-primary">AI Service Providers:</strong> For document analysis (e.g., Groq API). These providers process data under strict confidentiality terms.</li>
              <li><strong className="text-text-primary">Infrastructure Providers:</strong> Cloud hosting, database, and storage services required to operate the platform.</li>
              <li><strong className="text-text-primary">Legal Obligations:</strong> When required by law, regulation, or legal process.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">6. Data Retention</h2>
            <p>
              Account data is retained for as long as your account is active. Deal data is retained for the
              duration of the project plus any legally required retention period. You may request deletion
              of your account and associated data at any time through the Settings page (GDPR Article 17).
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">7. Data Security</h2>
            <p>
              We implement industry-standard security measures including encrypted passwords (bcrypt),
              JWT-based authentication with token blacklisting, role-based access control, and comprehensive
              audit logging. All data is transmitted over HTTPS.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">8. Your Rights (GDPR)</h2>
            <p className="mb-3">If you are in the EU/EEA, you have the right to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Access, correct, or delete your personal data.</li>
              <li>Restrict or object to processing of your data.</li>
              <li>Data portability - receive your data in a structured format.</li>
              <li>Withdraw consent at any time.</li>
              <li>Lodge a complaint with a supervisory authority.</li>
            </ul>
            <p className="mt-3">
              To exercise these rights, use the account deletion feature in Settings or contact us at the
              address below.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-text-primary mb-3">9. Contact</h2>
            <p>
              For privacy-related inquiries, contact us at:{" "}
              <span className="text-gold">ayushcreations2005@gmail.com</span>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
