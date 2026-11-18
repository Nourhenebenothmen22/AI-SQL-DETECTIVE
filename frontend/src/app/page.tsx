import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { WorkbenchView } from "@/components/workbench/workbench-view";

function WorkbenchFallback() {
  return (
    <div className="mx-auto max-w-[1600px] space-y-4 p-5">
      <Skeleton className="h-10 w-72" />
      <div className="grid gap-4 xl:grid-cols-[288px_minmax(0,1fr)]">
        <Skeleton className="h-96 w-full" />
        <div className="space-y-4">
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<WorkbenchFallback />}>
      <WorkbenchView />
    </Suspense>
  );
}
