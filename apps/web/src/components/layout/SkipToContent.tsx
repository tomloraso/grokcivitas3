export function SkipToContent(): JSX.Element {
  return (
    <a
      href="#main-content"
      className="fixed left-2 top-2 z-toast -translate-y-full rounded-md bg-brand-solid px-4 py-2 text-sm font-semibold text-white transition-transform duration-fast focus:translate-y-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-hover focus-visible:ring-offset-2 focus-visible:ring-offset-canvas"
    >
      Skip to content
    </a>
  );
}
