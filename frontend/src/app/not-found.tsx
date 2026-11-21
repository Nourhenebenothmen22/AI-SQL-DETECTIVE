import Link from "next/link";
import { AlertCircle, ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-status-error/10 text-status-error">
        <AlertCircle className="h-6 w-6" aria-hidden="true" />
      </div>
      <h1 className="text-xl font-semibold tracking-tight text-text-primary">
        Page Not Found
      </h1>
      <p className="mt-2 max-w-sm text-xs text-text-secondary">
        The requested resource or page does not exist in AI SQL Detective.
      </p>
      <div className="mt-6">
        <Button asChild variant="outline" size="sm">
          <Link href="/" className="inline-flex items-center gap-2">
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Return to Workbench</span>
          </Link>
        </Button>
      </div>
    </div>
  );
}
