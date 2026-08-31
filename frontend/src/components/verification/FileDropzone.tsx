import { useCallback, useRef, useState, type DragEvent } from "react";
import { UploadCloud, FileText, X } from "lucide-react";
import { cn, formatBytes } from "@/lib/utils";

export function FileDropzone({
  file,
  onFileSelected,
  onClear,
  accept,
  hint,
}: {
  file: File | null;
  onFileSelected: (file: File) => void;
  onClear: () => void;
  accept?: string;
  hint?: string;
}) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const dropped = e.dataTransfer.files?.[0];
      if (dropped) onFileSelected(dropped);
    },
    [onFileSelected]
  );

  if (file) {
    return (
      <div className="flex items-center gap-4 rounded-2xl border border-border bg-secondary/40 p-5">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <FileText className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{file.name}</p>
          <p className="text-xs text-muted-foreground">
            {formatBytes(file.size)} · {file.type || "unknown type"}
          </p>
        </div>
        <button
          type="button"
          onClick={onClear}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          aria-label="Remove file"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-border bg-secondary/20 px-6 py-14 text-center transition-colors hover:border-primary/50 hover:bg-primary/5",
        dragging && "border-primary bg-primary/5"
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
        <UploadCloud className="h-7 w-7" />
      </div>
      <div>
        <p className="text-sm font-semibold">Drag & drop a file, or click to browse</p>
        <p className="mt-1 text-xs text-muted-foreground">{hint ?? "Documents, images, audio, or video files"}</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const selected = e.target.files?.[0];
          if (selected) onFileSelected(selected);
          e.target.value = "";
        }}
      />
    </div>
  );
}
