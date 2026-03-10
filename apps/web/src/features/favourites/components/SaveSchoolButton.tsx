import { Bookmark, LockKeyhole } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

import {
  ApiClientError,
  removeAccountFavourite,
  resetApiRequestCache,
  saveAccountFavourite
} from "../../../api/client";
import { Button, type ButtonProps } from "../../../components/ui/Button";
import { useToast } from "../../../components/ui/ToastContext";
import { paths } from "../../../shared/routing/paths";
import { mapSavedSchoolState } from "../mappers";
import type { SavedSchoolStateVM } from "../types";

interface SaveSchoolButtonProps {
  schoolUrn: string;
  savedState: SavedSchoolStateVM;
  onSavedStateChange: (savedState: SavedSchoolStateVM) => void;
  size?: ButtonProps["size"];
  className?: string;
}

function buttonLabel(
  savedState: SavedSchoolStateVM,
  pendingAction: "save" | "remove" | null
): string {
  if (pendingAction === "save") {
    return "Saving...";
  }
  if (pendingAction === "remove") {
    return "Removing...";
  }

  switch (savedState.status) {
    case "saved":
      return "Saved";
    case "requires_auth":
      return "Sign in to save";
    case "locked":
      return "Unlock save";
    case "not_saved":
    default:
      return "Save";
  }
}

export function SaveSchoolButton({
  schoolUrn,
  savedState,
  onSavedStateChange,
  size = "sm",
  className
}: SaveSchoolButtonProps): JSX.Element {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [pendingAction, setPendingAction] = useState<"save" | "remove" | null>(
    null
  );

  const returnTo = `${location.pathname}${location.search}${location.hash}`;
  const isSaved = savedState.status === "saved";
  const isLocked = savedState.status === "locked";
  const isRequiresAuth = savedState.status === "requires_auth";

  async function handleClick(): Promise<void> {
    if (pendingAction !== null) {
      return;
    }

    if (isRequiresAuth) {
      navigate(paths.signIn(returnTo));
      return;
    }

    if (isLocked) {
      navigate(
        paths.upgrade({
          capability: savedState.capabilityKey ?? undefined,
          returnTo
        })
      );
      return;
    }

    const action = isSaved ? "remove" : "save";
    setPendingAction(action);

    try {
      const nextState = mapSavedSchoolState(
        action === "save"
          ? await saveAccountFavourite(schoolUrn)
          : await removeAccountFavourite(schoolUrn)
      );
      resetApiRequestCache();
      onSavedStateChange(nextState);
      toast({
        title:
          action === "save"
            ? "Saved to your library"
            : "Removed from saved schools",
        description:
          action === "save"
            ? "This school now appears in your saved research."
            : "This school has been removed from your saved research.",
        variant: "success"
      });
    } catch (error: unknown) {
      if (error instanceof ApiClientError && error.status === 401) {
        navigate(paths.signIn(returnTo));
        return;
      }

      toast({
        title:
          action === "save" ? "Could not save school" : "Could not remove save",
        description:
          error instanceof Error
            ? error.message
            : "Please try again.",
        variant: "warning"
      });
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <Button
      type="button"
      variant={isSaved ? "ghost" : "secondary"}
      size={size}
      className={className}
      onClick={() => {
        void handleClick();
      }}
      disabled={pendingAction !== null}
      aria-pressed={isSaved}
    >
      {isLocked ? (
        <LockKeyhole className="mr-1.5 h-3.5 w-3.5" aria-hidden />
      ) : (
        <Bookmark className="mr-1.5 h-3.5 w-3.5" aria-hidden />
      )}
      {buttonLabel(savedState, pendingAction)}
    </Button>
  );
}
