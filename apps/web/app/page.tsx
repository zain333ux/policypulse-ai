import { ArrowDown, FileCheck2, Quote, ShieldCheck } from "lucide-react";
import { InputWorkspace } from "@/components/input-workspace";
import { SiteHeader } from "@/components/site-header";

const benefits = [
  {
    icon: Quote,
    title: "Grounded in source evidence",
    text: "Every concern and recommendation can be traced back to the exact passage or comment.",
  },
  {
    icon: FileCheck2,
    title: "Decision-ready output",
    text: "Move from unstructured feedback to prioritized gaps, revised wording, and an executive memo.",
  },
  {
    icon: ShieldCheck,
    title: "Built for responsible review",
    text: "Structured AI outputs, visible limitations, and human review are part of the workflow.",
  },
];

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="relative overflow-hidden">
          <div aria-hidden="true" className="subtle-grid absolute inset-0 -z-10" />
          <div className="mx-auto max-w-7xl px-4 pb-14 pt-16 sm:px-6 sm:pt-24 lg:px-8 lg:pb-20">
            <div className="mx-auto max-w-4xl text-center">
              <span
                className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-semibold"
                style={{ background: "var(--primary-soft)", color: "var(--primary-strong)" }}
              >
                Evidence-first policy intelligence
              </span>
              <h1 className="mt-6 text-balance text-4xl font-semibold leading-tight sm:text-5xl lg:text-6xl">
                Turn public feedback into policy decisions people can trace.
              </h1>
              <p
                className="mx-auto mt-6 max-w-3xl text-pretty text-lg sm:text-xl"
                style={{ color: "var(--muted-foreground)" }}
              >
                PolicyPulse AI analyzes a proposed policy and stakeholder comments, then surfaces
                grounded concerns, missing protections, and practical recommendations.
              </p>
              <a
                href="#workspace"
                className="mt-8 inline-flex min-h-13 items-center gap-2 rounded-xl bg-[var(--primary)] px-6 font-semibold text-[var(--on-primary)] transition hover:bg-[var(--primary-strong)]"
              >
                Analyze a policy
                <ArrowDown aria-hidden="true" size={19} />
              </a>
            </div>

            <div className="mx-auto mt-14 grid max-w-5xl gap-4 md:grid-cols-3">
              {benefits.map(({ icon: Icon, title, text }) => (
                <article key={title} className="rounded-2xl border bg-[var(--surface)] p-5 shadow-sm">
                  <Icon aria-hidden="true" size={21} style={{ color: "var(--primary)" }} />
                  <h2 className="mt-4 text-base font-semibold">{title}</h2>
                  <p className="mt-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
                    {text}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="workspace" className="scroll-mt-24 pb-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <InputWorkspace />
          </div>
        </section>
      </main>
    </>
  );
}

