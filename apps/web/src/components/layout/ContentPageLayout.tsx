import type { ReactNode } from "react";

import { siteConfig } from "../../shared/config/site";
import { cn } from "../../shared/utils/cn";
import { PageMeta } from "./PageMeta";
import { PageContainer } from "./PageContainer";

interface ContentPageLayoutProps {
  title: string;
  metaTitle?: string;
  metaDescription?: string;
  canonicalPath: string;
  eyebrow?: string;
  lede?: string;
  children: ReactNode;
  className?: string;
}

export function ContentPageLayout({
  title,
  metaTitle,
  metaDescription,
  canonicalPath,
  eyebrow = "Launch Foundations",
  lede,
  children,
  className,
}: ContentPageLayoutProps): JSX.Element {
  return (
    <>
      <PageMeta
        title={metaTitle ?? title}
        description={metaDescription}
        canonicalPath={canonicalPath}
      />
      <PageContainer className="max-w-4xl">
        <div className={cn("space-y-6 sm:space-y-8", className)}>
          <header className="space-y-3">
            <p className="eyebrow">{eyebrow}</p>
            <h1 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl lg:text-5xl">
              {title}
            </h1>
            <p className="max-w-3xl text-sm leading-6 text-secondary sm:text-base">
              {lede ?? siteConfig.defaultDescription}
            </p>
          </header>

          <article className="content-prose panel-surface rounded-2xl p-5 sm:p-8">
            {children}
          </article>
        </div>
      </PageContainer>
    </>
  );
}
