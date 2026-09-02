import { Languages } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { LANGUAGES, useLanguage } from "@/context/LanguageContext";

export function LanguageSelector({ compact = false }: { compact?: boolean }) {
  const { language, setLanguage, languageName, t } = useLanguage();
  return (
    <DropdownMenu>
      <div data-ps-no-translate="true"><DropdownMenuTrigger asChild>
        <Button variant="outline" size={compact ? "icon" : "sm"} aria-label={t("Language")} title={t("Language")}>
          <Languages className="h-4 w-4" />
          {!compact && <span className="hidden sm:inline">{languageName}</span>}
        </Button>
      </DropdownMenuTrigger></div>
      <DropdownMenuContent data-ps-no-translate="true" align="end" className="max-h-[min(70vh,480px)] w-56 overflow-y-auto">
        {LANGUAGES.map((item) => (
          <DropdownMenuItem key={item.code} onClick={() => setLanguage(item.code)} className="cursor-pointer justify-between">
            <span>{item.native}</span>
            <span className="text-[11px] text-muted-foreground">{item.label}</span>
            {language === item.code && <span className="ml-2 text-primary">✓</span>}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
