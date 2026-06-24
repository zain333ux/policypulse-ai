import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b bg-[color-mix(in_srgb,var(--background)_88%,transparent)] backdrop-blur-xl">
      <div className="mx-auto flex min-h-18 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Brand />
        <div className="flex items-center gap-3">
          <span
            className="hidden rounded-full border px-3 py-1.5 text-sm sm:inline-flex"
            style={{ color: "var(--muted-foreground)" }}
          >
            Private by default · expires automatically
          </span>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

