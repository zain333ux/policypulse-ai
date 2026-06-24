"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <button
      type="button"
      className="grid size-11 place-items-center rounded-xl border transition-colors hover:bg-[var(--surface-subtle)]"
      aria-label="Toggle color theme"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      <Sun className="hidden dark:block" aria-hidden="true" size={19} />
      <Moon className="block dark:hidden" aria-hidden="true" size={19} />
    </button>
  );
}
