import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function LoadingSpinner({ size = "md", className = "" }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  };

  return (
    <Loader2 
      className={`animate-spin ${sizeClasses[size]} ${className}`}
    />
  );
}

interface FullPageLoadingProps {
  message?: string;
}

export function FullPageLoading({ message = "Loading…" }: FullPageLoadingProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">
      <div className="flex flex-col items-center gap-3">
        <LoadingSpinner size="lg" />
        <span className="text-sm">{message}</span>
      </div>
    </div>
  );
}

interface InlineLoadingProps {
  message?: string;
  className?: string;
}

export function InlineLoading({ message = "Loading…", className = "" }: InlineLoadingProps) {
  return (
    <div className={`flex items-center justify-center gap-2 text-slate-400 ${className}`}>
      <LoadingSpinner size="sm" />
      <span className="text-sm">{message}</span>
    </div>
  );
}
