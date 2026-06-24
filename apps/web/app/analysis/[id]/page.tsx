import { AnalysisExperience } from "@/components/analysis-experience";
import { SiteHeader } from "@/components/site-header";

export default async function AnalysisPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <SiteHeader />
      <AnalysisExperience analysisId={id} />
    </>
  );
}
