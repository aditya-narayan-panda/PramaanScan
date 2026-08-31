import { Link, useNavigate } from "react-router-dom";
import { ServerCrash, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ServerErrorPage() {
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-grid-slate px-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-warning/10 text-warning">
        <ServerCrash className="h-8 w-8" />
      </div>
      <p className="mt-6 font-display text-6xl font-bold text-warning">500</p>
      <h1 className="mt-3 font-display text-2xl font-bold">Something went wrong</h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        An unexpected error occurred. Try refreshing the page, or head back home.
      </p>
      <div className="mt-7 flex gap-3">
        <Button variant="outline" asChild>
          <Link to="/">Home</Link>
        </Button>
        <Button onClick={() => navigate(0)}>
          <RotateCw className="h-4 w-4" />
          Reload
        </Button>
      </div>
    </div>
  );
}
