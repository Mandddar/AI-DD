import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, FolderOpen, Building2 } from "lucide-react";
import { Link } from "react-router-dom";
import { projectsApi, type CreateProjectData } from "../../api/projects";

function CreateProjectModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<CreateProjectData>({
    name: "",
    company_name: "",
    legal_form: "GmbH",
    deal_type: "share_deal",
    industry: "",
    registered_office: "",
    employee_count: "",
    revenue_size: "",
  });

  const mutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      onClose();
    },
  });

  const field = (key: keyof CreateProjectData, label: string, type = "text", placeholder = "") => (
    <div>
      <label className="label">{label}</label>
      <input
        className="input"
        type={type}
        placeholder={placeholder}
        value={(form[key] as string) ?? ""}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
      />
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="card w-full max-w-lg p-6 animate-slide-in max-h-[90vh] overflow-y-auto">
        <h2 className="mb-5 font-display text-lg text-text-primary">New Deal</h2>

        <div className="space-y-3">
          {field("name", "Deal Name", "text", "e.g. Acquisition of MediTech GmbH")}
          {field("company_name", "Target Company", "text", "Legal company name")}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Legal Form</label>
              <select className="input" value={form.legal_form} onChange={(e) => setForm({ ...form, legal_form: e.target.value })}>
                <option>GmbH</option>
                <option>AG</option>
                <option>KG</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <label className="label">Deal Type</label>
              <select className="input" value={form.deal_type} onChange={(e) => setForm({ ...form, deal_type: e.target.value })}>
                <option value="share_deal">Share Deal</option>
                <option value="asset_deal">Asset Deal</option>
              </select>
            </div>
          </div>

          {field("industry", "Industry", "text", "e.g. Healthcare, Manufacturing")}
          {field("registered_office", "Registered Office", "text", "e.g. Munich, Germany")}

          <div className="grid grid-cols-2 gap-3">
            {field("employee_count", "Employees", "text", "e.g. 50–200")}
            {field("revenue_size", "Revenue (approx.)", "text", "e.g. €10–50M")}
          </div>
        </div>

        {mutation.error && (
          <p className="mt-3 rounded bg-risk-high/10 px-3 py-2 text-xs text-risk-high">
            {(mutation.error as any).response?.data?.detail ?? "Something went wrong"}
          </p>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="btn-ghost">Cancel</button>
          <button
            onClick={() => mutation.mutate(form)}
            disabled={mutation.isPending || !form.name || !form.company_name}
            className="btn-primary"
          >
            {mutation.isPending ? "Creating…" : "Create Deal"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function ProjectsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
  });

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-text-primary">Deals</h1>
          <p className="mt-1 text-sm text-text-secondary">{projects.length} deal{projects.length !== 1 ? "s" : ""}</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus size={14} />
          New Deal
        </button>
      </div>

      {isLoading ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-text-muted">Loading deals…</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="card p-12 text-center">
          <FolderOpen size={40} className="mx-auto mb-4 text-text-muted" />
          <p className="text-sm font-medium text-text-primary">No deals yet</p>
          <p className="mt-1 text-xs text-text-muted">Create your first deal to get started</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary mt-4">
            <Plus size={14} /> New Deal
          </button>
        </div>
      ) : (
        <div className="grid gap-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}/documents`}
              className="card p-4 flex items-center justify-between hover:shadow-card-hover hover:border-canvas-border/80 transition-all group"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface group-hover:bg-surface-hover transition-colors">
                  <Building2 size={18} className="text-text-secondary" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-text-primary">{project.name}</p>
                  <p className="text-xs text-text-muted">
                    {project.company_name} · {project.legal_form} · {project.industry ?? "—"} ·{" "}
                    {project.deal_type.replace("_", " ")}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {project.registered_office && (
                  <span className="text-xs text-text-muted">{project.registered_office}</span>
                )}
                <span
                  className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                    project.status === "active"
                      ? "bg-risk-low/10 text-risk-low"
                      : project.status === "completed"
                      ? "bg-gold/10 text-gold"
                      : "bg-surface text-text-muted"
                  }`}
                >
                  {project.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {showCreate && <CreateProjectModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}
