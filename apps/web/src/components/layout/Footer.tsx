export function Footer() {
  return (
    <footer className="border-t border-canvas-border bg-canvas-subtle px-8 py-3">
      <p className="text-center text-xs text-text-muted leading-relaxed">
        <span className="text-gold/70 font-semibold">AI Notice:</span>{" "}
        This system uses Artificial Intelligence to support due diligence review. AI-generated results may be inaccurate,
        incomplete, or misleading. Responsibility for audit results and all decisions lies exclusively with the human
        reviewer. This tool does not replace qualified legal, tax, or financial advisory services.
      </p>
    </footer>
  );
}
