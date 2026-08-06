import { AlertTriangle, Info, CheckCircle2 } from "lucide-react";

export function Alert({ type = "info", children, className = "" }) {
  const styles = {
    error: "border-red-200 bg-red-50 text-red-700",
    warning: "border-amber-200 bg-amber-50 text-amber-800",
    success: "border-brand-200 bg-brand-50 text-brand-800",
    info: "border-sky-200 bg-sky-50 text-sky-800",
  };
  const Icon = { error: AlertTriangle, warning: AlertTriangle, success: CheckCircle2, info: Info }[type];
  return (
    <div className={`flex items-start gap-2 rounded-xl border px-4 py-3 text-sm ${styles[type]} ${className}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}

export default Alert;
