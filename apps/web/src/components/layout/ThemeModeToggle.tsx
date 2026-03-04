import type { ThemeMode } from "../../shared/theme/theme-mode";

/* ------------------------------------------------------------------ */
/* Icons (inline SVG to avoid external deps)                           */
/* ------------------------------------------------------------------ */

function SunIcon({ className }: { className?: string }): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={className}
      aria-hidden="true"
    >
      <path d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zm0 13a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zm8-5a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10zm11.364-5.364a.75.75 0 010 1.06l-1.06 1.061a.75.75 0 11-1.061-1.06l1.06-1.061a.75.75 0 011.061 0zm-9.9 9.9a.75.75 0 010 1.06l-1.06 1.06a.75.75 0 01-1.061-1.06l1.06-1.06a.75.75 0 011.061 0zm9.9 0a.75.75 0 01-1.06 1.06l-1.061-1.06a.75.75 0 011.06-1.06l1.061 1.06zM6.404 6.404a.75.75 0 01-1.06 1.061l-1.061-1.06a.75.75 0 011.06-1.061l1.061 1.06zM10 7a3 3 0 100 6 3 3 0 000-6z" />
    </svg>
  );
}

function MoonIcon({ className }: { className?: string }): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={className}
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M7.455 2.004a.75.75 0 01.26.77 7 7 0 009.958 7.967.75.75 0 011.067.853A8.5 8.5 0 118.58 1.514a.75.75 0 01-.126.49z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function MonitorIcon({ className }: { className?: string }): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={className}
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M2 4.25A2.25 2.25 0 014.25 2h11.5A2.25 2.25 0 0118 4.25v8.5A2.25 2.25 0 0115.75 15h-3.091l.386 1.542a.75.75 0 01-.727.958H7.682a.75.75 0 01-.727-.958L7.341 15H4.25A2.25 2.25 0 012 12.75v-8.5zm2.25-.75a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h11.5a.75.75 0 00.75-.75v-8.5a.75.75 0 00-.75-.75H4.25z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/* Label lookup                                                         */
/* ------------------------------------------------------------------ */

const MODE_LABEL: Record<ThemeMode, string> = {
  system: "System theme",
  light: "Light theme",
  dark: "Dark theme",
};

/* ------------------------------------------------------------------ */
/* Component                                                            */
/* ------------------------------------------------------------------ */

interface ThemeModeToggleProps {
  mode: ThemeMode;
  onCycle: () => void;
}

export function ThemeModeToggle({ mode, onCycle }: ThemeModeToggleProps): JSX.Element {
  const label = MODE_LABEL[mode];
  const Icon = mode === "light" ? SunIcon : mode === "dark" ? MoonIcon : MonitorIcon;

  return (
    <button
      type="button"
      onClick={onCycle}
      aria-label={label}
      title={label}
      className="inline-flex h-9 w-9 items-center justify-center rounded-md text-secondary transition-colors duration-fast hover:bg-surface/60 hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
    >
      <Icon className="h-[18px] w-[18px]" />
    </button>
  );
}
