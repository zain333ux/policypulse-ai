import { ScanSearch } from "lucide-react";
import Link from "next/link";

export function Brand() {
  return (
    <Link href="/" className="flex min-h-11 items-center gap-3 rounded-xl" aria-label="PolicyPulse AI home">
      <span
        className="grid size-10 place-items-center rounded-xl border"
        style={{ background: "var(--primary-soft)", color: "var(--primary)" }}
      >
        <ScanSearch aria-hidden="true" size={21} strokeWidth={2} />
      </span>
      <span>
        <span className="block font-[family-name:var(--font-lexend)] text-[15px] font-semibold leading-5">
          PolicyPulse AI
        </span>
        <span className="block text-xs" style={{ color: "var(--muted-foreground)" }}>
          Evidence-first consultation
        </span>
      </span>
    </Link>
  );
}

