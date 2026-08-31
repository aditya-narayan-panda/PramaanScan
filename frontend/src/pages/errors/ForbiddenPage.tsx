import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-grid-slate px-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
        <ShieldAlert className="h-8 w-8" />
      </div>
      <p className="mt-6 font-display text-6xl font-bold text-destructive">403</p>
      <h1 className="mt-3 font-display text-2xl font-bold">Access denied</h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        You don't have permission to view this page with your current account role.
      </p>
      <div className="mt-7 flex gap-3">
        <Button variant="outline" asChild>
          <Link to="/">Home</Link>
        </Button>
        <Button asChild>
          <Link to="/institution/login">Switch Account</Link>
        </Button>
      </div>
    </div>
  );
}
