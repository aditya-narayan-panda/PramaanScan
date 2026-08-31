import { Outlet } from "react-router-dom";
import { PortalSidebar, ADMIN_LINKS } from "./PortalSidebar";
import { PortalTopbar } from "./PortalTopbar";

export function AdminLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <PortalSidebar links={ADMIN_LINKS} portalLabel="Admin Portal" className="hidden lg:flex" />
      <div className="flex flex-1 flex-col overflow-hidden">
        <PortalTopbar links={ADMIN_LINKS} portalLabel="Admin Portal" profilePath="/admin/settings" />
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="container max-w-6xl py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
