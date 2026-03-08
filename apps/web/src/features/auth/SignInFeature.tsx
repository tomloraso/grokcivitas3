import { useState, type FormEvent } from "react";
import { Link, useLocation } from "react-router-dom";

import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Panel } from "../../components/ui/Card";
import { TextInput } from "../../components/ui/TextInput";
import { paths } from "../../shared/routing/paths";
import { useAuth } from "./useAuth";

function normalizeReturnTo(value: string | null): string | null {
  if (!value) {
    return null;
  }

  if (!value.startsWith("/") || value.startsWith("//")) {
    return null;
  }

  return value;
}

function getErrorMessage(errorCode: string | null): string | null {
  if (errorCode === "invalid_state") {
    return "Your sign-in link has expired or could not be verified.";
  }

  if (errorCode === "callback_failed") {
    return "We could not complete sign-in. Please try again.";
  }

  if (errorCode === "unverified_email") {
    return "Your identity provider did not confirm this email address.";
  }

  return null;
}

export function SignInFeature(): JSX.Element {
  const location = useLocation();
  const { isLoading, session, signOut, startSignIn } = useAuth();
  const [email, setEmail] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const searchParams = new URLSearchParams(location.search);
  const returnTo = normalizeReturnTo(searchParams.get("returnTo"));
  const callbackError = getErrorMessage(searchParams.get("error"));
  const isBusy = isLoading || isSubmitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      await startSignIn(email.trim(), returnTo);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Could not start sign-in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSignOut(): Promise<void> {
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      await signOut();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageContainer className="max-w-3xl">
      <div className="mx-auto max-w-xl space-y-6">
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-secondary">
            Account
          </p>
          <h1 className="text-3xl font-display font-semibold tracking-tight text-primary sm:text-4xl">
            Sign in to Civitas
          </h1>
          <p className="max-w-2xl text-sm leading-6 text-secondary sm:text-base">
            Use your email address to start a Civitas-managed session. Premium access and
            billing are not part of this slice yet.
          </p>
        </div>

        {callbackError || submitError ? (
          <section
            role="alert"
            className="rounded-lg border border-danger/60 bg-danger/10 px-4 py-3 text-sm text-primary"
          >
            {callbackError ?? submitError}
          </section>
        ) : null}

        {session.state === "authenticated" && session.user ? (
          <Panel className="space-y-5">
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-primary">You are already signed in</h2>
              <p className="text-sm text-secondary">
                Current account: <span className="font-medium text-primary">{session.user.email}</span>
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button asChild>
                <Link to={returnTo ?? paths.home}>Continue</Link>
              </Button>
              <Button type="button" variant="secondary" onClick={() => void handleSignOut()}>
                Sign out
              </Button>
            </div>
          </Panel>
        ) : (
          <Panel className="space-y-5">
            <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
              <Field
                label="Email address"
                htmlFor="sign-in-email"
                helperText="We will hand this to the configured identity provider and return you to the app."
                required
              >
                <TextInput
                  id="sign-in-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.currentTarget.value)}
                  disabled={isBusy}
                  required
                />
              </Field>

              <div className="flex flex-wrap items-center gap-3">
                <Button type="submit" disabled={isBusy || email.trim().length === 0}>
                  Continue
                </Button>
                <Button asChild variant="ghost">
                  <Link to={paths.home}>Back to search</Link>
                </Button>
              </div>
            </form>
          </Panel>
        )}
      </div>
    </PageContainer>
  );
}
