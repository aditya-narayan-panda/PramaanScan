import { Outlet } from "react-router-dom";
import { PortalSidebar, INSTITUTION_LINKS } from "./PortalSidebar";
import { PortalTopbar } from "./PortalTopbar";

export function InstitutionLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <PortalSidebar links={INSTITUTION_LINKS} portalLabel="Institution Portal" className="hidden lg:flex" />
      <div className="flex flex-1 flex-col overflow-hidden">
        <PortalTopbar
          links={INSTITUTION_LINKS}
          portalLabel="Institution Portal"
          profilePath="/institution/profile"
        />
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="container max-w-6xl py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
