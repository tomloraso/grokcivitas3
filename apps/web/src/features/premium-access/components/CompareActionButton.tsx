import { LockKeyhole } from "lucide-react";
import { Link } from "react-router-dom";

import { Button, type ButtonProps } from "../../../components/ui/Button";
import { paths } from "../../../shared/routing/paths";
import { useAuth } from "../../auth/useAuth";
import { COMPARE_CAPABILITY_KEY } from "../types";

interface CompareActionButtonProps {
  urns: string[];
  label: string;
  lockedLabel?: string;
  ariaLabel?: string;
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];
}

export function CompareActionButton({
  urns,
  label,
  lockedLabel,
  ariaLabel,
  variant = "secondary",
  size = "default",
}: CompareActionButtonProps): JSX.Element {
  const { session } = useAuth();
  const compareHref = paths.compare(urns);

  if (urns.length < 2) {
    return (
      <Button
        type="button"
        variant={variant}
        size={size}
        disabled
        aria-label={ariaLabel}
      >
        {label}
      </Button>
    );
  }

  if (session.capabilityKeys.includes(COMPARE_CAPABILITY_KEY)) {
    return (
      <Button asChild variant={variant} size={size}>
        <Link to={compareHref} aria-label={ariaLabel}>
          {label}
        </Link>
      </Button>
    );
  }

  const upgradeHref =
    session.state === "authenticated"
      ? paths.upgrade({
          capability: COMPARE_CAPABILITY_KEY,
          returnTo: compareHref,
        })
      : paths.signIn(
          paths.upgrade({
            capability: COMPARE_CAPABILITY_KEY,
            returnTo: compareHref,
          })
        );

  return (
    <Button asChild variant={variant} size={size}>
      <Link to={upgradeHref} aria-label={ariaLabel}>
        <LockKeyhole className="mr-1.5 h-3.5 w-3.5" aria-hidden />
        {lockedLabel ?? label}
      </Link>
    </Button>
  );
}
