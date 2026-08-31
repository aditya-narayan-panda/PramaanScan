import { PageHeader } from "@/components/common/PageHeader";
import { VerificationLogsTable } from "@/components/common/VerificationLogsTable";

export default function AdminVerificationLogsPage() {
  return (
    <div>
      <PageHeader title="Verification Logs" description="Every verification attempt across the entire platform." />
      <VerificationLogsTable />
    </div>
  );
}
