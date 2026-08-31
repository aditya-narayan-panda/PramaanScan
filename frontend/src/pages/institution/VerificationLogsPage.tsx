import { PageHeader } from "@/components/common/PageHeader";
import { VerificationLogsTable } from "@/components/common/VerificationLogsTable";

export default function VerificationLogsPage() {
  return (
    <div>
      <PageHeader title="Verification Logs" description="Every verification attempt made against your institution's documents." />
      <VerificationLogsTable />
    </div>
  );
}
