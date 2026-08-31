import { PageHeader } from "@/components/common/PageHeader";
import { DocumentsTable } from "@/components/common/DocumentsTable";

export default function DocumentManagementPage() {
  return (
    <div>
      <PageHeader title="Document Management" description="All communications registered across every institution." />
      <DocumentsTable detailBasePath="/admin/documents" />
    </div>
  );
}
