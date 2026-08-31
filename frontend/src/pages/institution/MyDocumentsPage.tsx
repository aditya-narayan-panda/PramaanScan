import { Link } from "react-router-dom";
import { UploadCloud } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { DocumentsTable } from "@/components/common/DocumentsTable";
import { Button } from "@/components/ui/button";

export default function MyDocumentsPage() {
  return (
    <div>
      <PageHeader
        title="My Documents"
        description="All communications registered by your institution."
        action={
          <Button asChild>
            <Link to="/institution/upload-sign">
              <UploadCloud className="h-4 w-4" /> Upload & Sign
            </Link>
          </Button>
        }
      />
      <DocumentsTable detailBasePath="/institution/documents" />
    </div>
  );
}
