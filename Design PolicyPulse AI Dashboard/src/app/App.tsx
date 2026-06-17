import { useState } from "react";
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  AlertTriangle,
  Lightbulb,
  ClipboardList,
  Settings,
  Bell,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Search,
  Download,
  Plus,
  Trash2,
  GripVertical,
  CheckCircle2,
  Circle,
  ArrowRight,
  BarChart3,
  Users,
  Globe,
  Shield,
  ChevronDown,
  ExternalLink,
  Printer,
} from "lucide-react";

const sentimentData = [
  { name: "Support", value: 54, color: "#2DD4BF" },
  { name: "Opposition", value: 28, color: "#EF4444" },
  { name: "Neutral", value: 18, color: "#6B7FA3" },
];

const gapData = [
  { label: "Housing Policy", gaps: 12, severity: "High" },
  { label: "Healthcare Access", gaps: 9, severity: "High" },
  { label: "Transit Funding", gaps: 7, severity: "Medium" },
  { label: "Education Reform", gaps: 5, severity: "Medium" },
  { label: "Climate Zoning", gaps: 4, severity: "Low" },
  { label: "Fiscal Policy", gaps: 3, severity: "Low" },
];

const feedbackData = [
  {
    id: 1,
    author: "Margaret L.",
    role: "Ward 7 Resident",
    sentiment: "support",
    date: "Jun 14, 2026",
    text: "The proposed transit expansion directly addresses the 40-minute commute gap between the eastern districts and the commercial core. Long overdue.",
    tags: ["Transit", "Infrastructure"],
  },
  {
    id: 2,
    author: "David Chen",
    role: "Small Business Owner",
    sentiment: "opposition",
    date: "Jun 13, 2026",
    text: "The zoning amendments as written would displace roughly 300 small businesses along the Corridor 9 stretch. We need an impact assessment first.",
    tags: ["Zoning", "Economic Impact"],
  },
  {
    id: 3,
    author: "Prof. Sarah Okonkwo",
    role: "Urban Policy Researcher",
    sentiment: "neutral",
    date: "Jun 12, 2026",
    text: "The framework is sound conceptually, but lacks measurable KPIs for the 18-month milestones. Without benchmarks, accountability is theoretical.",
    tags: ["Accountability", "Metrics"],
  },
  {
    id: 4,
    author: "James Whitfield",
    role: "City Council Advisory Board",
    sentiment: "support",
    date: "Jun 11, 2026",
    text: "The affordable housing density bonus structure aligns with the regional housing compact. Recommend expedited committee review.",
    tags: ["Housing", "Compliance"],
  },
];

const recommendations = [
  {
    priority: "Critical",
    title: "Establish Transit Equity Impact Assessment Protocol",
    description:
      "Deploy standardized impact scoring for all transit proposals affecting districts with below-median connectivity indices. Integrate scoring into pre-vote committee review.",
    status: "Pending Council Vote",
    assignee: "Office of Transportation",
  },
  {
    priority: "High",
    title: "Revise Housing Density Bonus Eligibility Thresholds",
    description:
      "Current 30% AMI threshold excludes workforce housing cohort (60–80% AMI). Recommend expanding eligibility to align with state housing compact requirements.",
    status: "Under Review",
    assignee: "Dept. of Planning & Zoning",
  },
  {
    priority: "High",
    title: "Mandate 18-Month Outcome Metrics for All Major Policy Initiatives",
    description:
      "Public feedback consistently identifies lack of measurable targets as a trust deficit. Introduce standardized KPI templates for any policy with budget impact exceeding $2M.",
    status: "Draft",
    assignee: "Office of the City Manager",
  },
  {
    priority: "Medium",
    title: "Create Small Business Displacement Mitigation Fund",
    description:
      "Zoning amendments in Corridor 9 and adjacent areas require a pre-displacement support mechanism. Recommend $4.2M fund with tiered eligibility.",
    status: "Research Phase",
    assignee: "Economic Development Office",
  },
];

const surveyQuestions = [
  {
    id: 1,
    type: "multiple_choice",
    question: "How would you rate the overall impact of the proposed transit expansion on your daily commute?",
    options: ["Significantly positive", "Somewhat positive", "No impact", "Somewhat negative", "Significantly negative"],
  },
  {
    id: 2,
    type: "scale",
    question: "On a scale of 1–10, how confident are you that the city will meet its 18-month housing targets?",
    options: [],
  },
  {
    id: 3,
    type: "open_text",
    question: "What is the single most important policy gap the city should address in the next fiscal year?",
    options: [],
  },
];

const pipelineSteps = [
  {
    id: "policy",
    label: "Policy Agent",
    sublabel: "Document ingestion & classification",
    status: "complete",
    icon: FileText,
  },
  {
    id: "sentiment",
    label: "Sentiment Agent",
    sublabel: "NLP scoring & tonal analysis",
    status: "complete",
    icon: MessageSquare,
  },
  {
    id: "gap",
    label: "Gap Agent",
    sublabel: "Coverage & inconsistency detection",
    status: "active",
    icon: AlertTriangle,
  },
  {
    id: "recommendation",
    label: "Recommendation Agent",
    sublabel: "Priority-ranked action synthesis",
    status: "queued",
    icon: Lightbulb,
  },
  {
    id: "survey",
    label: "Survey Agent",
    sublabel: "Civic feedback instrument generation",
    status: "queued",
    icon: ClipboardList,
  },
];

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "policy", label: "Policy Overview", icon: FileText },
  { id: "feedback", label: "Public Feedback", icon: MessageSquare },
  { id: "gaps", label: "Gap Analysis", icon: AlertTriangle },
  { id: "recommendations", label: "Recommendations", icon: Lightbulb },
  { id: "survey", label: "Survey Generator", icon: ClipboardList },
];

function DonutChart({ data }: { data: { name: string; value: number; color: string }[] }) {
  const cx = 65, cy = 65, r = 50, innerR = 32, gap = 2;
  const total = data.reduce((s, d) => s + d.value, 0);
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  let angle = -90;
  const slices = data.map((d) => {
    const sweep = (d.value / total) * 360 - gap;
    const start = angle + gap / 2;
    const end = start + sweep;
    angle += (d.value / total) * 360;
    const largeArc = sweep > 180 ? 1 : 0;
    const x1 = cx + r * Math.cos(toRad(start));
    const y1 = cy + r * Math.sin(toRad(start));
    const x2 = cx + r * Math.cos(toRad(end));
    const y2 = cy + r * Math.sin(toRad(end));
    const x3 = cx + innerR * Math.cos(toRad(end));
    const y3 = cy + innerR * Math.sin(toRad(end));
    const x4 = cx + innerR * Math.cos(toRad(start));
    const y4 = cy + innerR * Math.sin(toRad(start));
    return { ...d, path: `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${innerR} ${innerR} 0 ${largeArc} 0 ${x4} ${y4} Z` };
  });
  return (
    <svg width={130} height={130} viewBox="0 0 130 130">
      {slices.map((s) => (
        <path key={s.name} d={s.path} fill={s.color} />
      ))}
    </svg>
  );
}

function BarChartSVG({ data }: { data: { label: string; gaps: number; severity: string }[] }) {
  const w = 420, h = 140, paddingL = 28, paddingB = 28, paddingT = 8, paddingR = 8;
  const maxVal = Math.max(...data.map((d) => d.gaps));
  const chartW = w - paddingL - paddingR;
  const chartH = h - paddingT - paddingB;
  const barW = Math.floor(chartW / data.length) - 8;
  const severityColor = (s: string) => s === "High" ? "#EF4444" : s === "Medium" ? "#F59E0B" : "#3B82F6";
  const gridLines = [0, Math.ceil(maxVal / 2), maxVal];
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ overflow: "visible" }}>
      {gridLines.map((v) => {
        const y = paddingT + chartH - (v / maxVal) * chartH;
        return (
          <g key={`grid-${v}`}>
            <line x1={paddingL} y1={y} x2={w - paddingR} y2={y} stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
            <text x={paddingL - 4} y={y + 3.5} textAnchor="end" fontSize={8} fill="#4A6080" fontFamily="JetBrains Mono">{v}</text>
          </g>
        );
      })}
      {data.map((d, i) => {
        const slotW = chartW / data.length;
        const x = paddingL + i * slotW + (slotW - barW) / 2;
        const barH = (d.gaps / maxVal) * chartH;
        const y = paddingT + chartH - barH;
        const labelWords = d.label.split(" ");
        return (
          <g key={`bar-svg-${i}`}>
            <rect x={x} y={y} width={barW} height={barH} fill={severityColor(d.severity)} rx={3} />
            {labelWords.map((word, wi) => (
              <text key={wi} x={x + barW / 2} y={h - 14 + wi * 9} textAnchor="middle" fontSize={8} fill="#4A6080" fontFamily="JetBrains Mono">
                {word}
              </text>
            ))}
          </g>
        );
      })}
    </svg>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [surveyQuestionList, setSurveyQuestionList] = useState(surveyQuestions);
  const [expandedRecommendation, setExpandedRecommendation] = useState<number | null>(0);

  const kpis = [
    {
      label: "Public Support",
      value: "54%",
      delta: "+3.2%",
      direction: "up",
      sub: "vs. prior 30-day period",
      color: "#2DD4BF",
      icon: TrendingUp,
    },
    {
      label: "Opposition",
      value: "28%",
      delta: "−1.8%",
      direction: "down",
      sub: "vs. prior 30-day period",
      color: "#EF4444",
      icon: TrendingDown,
    },
    {
      label: "Neutral",
      value: "18%",
      delta: "−1.4%",
      direction: "down",
      sub: "vs. prior 30-day period",
      color: "#6B7FA3",
      icon: Minus,
    },
    {
      label: "Critical Gaps Found",
      value: "40",
      delta: "+7 this week",
      direction: "up",
      sub: "across 6 policy domains",
      color: "#F59E0B",
      icon: AlertTriangle,
    },
  ];

  const priorityColor: Record<string, string> = {
    Critical: "#EF4444",
    High: "#F59E0B",
    Medium: "#3B82F6",
    Low: "#6B7FA3",
  };

  const sentimentColor: Record<string, string> = {
    support: "#2DD4BF",
    opposition: "#EF4444",
    neutral: "#6B7FA3",
  };

  const sentimentLabel: Record<string, string> = {
    support: "Support",
    opposition: "Opposition",
    neutral: "Neutral",
  };

  const removeQuestion = (id: number) => {
    setSurveyQuestionList((prev) => prev.filter((q) => q.id !== id));
  };

  const addQuestion = () => {
    const newQ = {
      id: Date.now(),
      type: "open_text",
      question: "New question — click to edit",
      options: [],
    };
    setSurveyQuestionList((prev) => [...prev, newQ]);
  };

  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{ fontFamily: "'Inter', sans-serif", background: "#0B1220", color: "#E8EDF5" }}
    >
      {/* Sidebar */}
      <aside
        className="w-[220px] flex-shrink-0 flex flex-col border-r"
        style={{ background: "#0D1626", borderColor: "rgba(255,255,255,0.06)" }}
      >
        {/* Logo */}
        <div className="px-5 pt-6 pb-5 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-2.5 mb-0.5">
            <div
              className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0"
              style={{ background: "linear-gradient(135deg, #2DD4BF 0%, #3B82F6 100%)" }}
            >
              <Globe size={14} color="#0B1220" strokeWidth={2.5} />
            </div>
            <span className="font-semibold text-sm tracking-tight" style={{ color: "#E8EDF5" }}>
              PolicyPulse AI
            </span>
          </div>
          <p className="text-[10px] leading-tight mt-2" style={{ color: "#4A6080", fontFamily: "'JetBrains Mono', monospace" }}>
            CIVIC INTELLIGENCE SYSTEM
          </p>
        </div>

        {/* Live status */}
        <div className="px-5 py-3 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                style={{ background: "#2DD4BF" }}
              ></span>
              <span className="relative inline-flex rounded-full h-2 w-2" style={{ background: "#2DD4BF" }}></span>
            </span>
            <span className="text-[11px]" style={{ color: "#2DD4BF", fontFamily: "'JetBrains Mono', monospace" }}>
              Live Analysis Running
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 overflow-y-auto">
          <p className="text-[10px] px-2 mb-2 tracking-widest uppercase" style={{ color: "#3D5070", fontFamily: "'JetBrains Mono', monospace" }}>
            Navigation
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm mb-0.5 transition-all duration-150"
                style={{
                  background: isActive ? "rgba(45,212,191,0.08)" : "transparent",
                  color: isActive ? "#2DD4BF" : "#6B7FA3",
                  borderLeft: isActive ? "2px solid #2DD4BF" : "2px solid transparent",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    (e.currentTarget as HTMLButtonElement).style.color = "#A0AEC0";
                    (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.03)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    (e.currentTarget as HTMLButtonElement).style.color = "#6B7FA3";
                    (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                  }
                }}
              >
                <Icon size={15} strokeWidth={isActive ? 2 : 1.5} />
                <span style={{ fontWeight: isActive ? 500 : 400 }}>{item.label}</span>
              </button>
            );
          })}

          <div className="border-t mt-4 pt-4" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
            <p className="text-[10px] px-2 mb-2 tracking-widest uppercase" style={{ color: "#3D5070", fontFamily: "'JetBrains Mono', monospace" }}>
              System
            </p>
            {[
              { label: "Settings", icon: Settings },
              { label: "Notifications", icon: Bell },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm mb-0.5 transition-colors"
                  style={{ color: "#6B7FA3" }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.color = "#A0AEC0";
                    (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.03)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.color = "#6B7FA3";
                    (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                  }}
                >
                  <Icon size={15} strokeWidth={1.5} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-2.5">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0"
              style={{ background: "#1E3A5F", color: "#93C5FD" }}
            >
              AC
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium truncate" style={{ color: "#E8EDF5" }}>
                Administrator
              </p>
              <p className="text-[10px] truncate" style={{ color: "#4A6080" }}>
                City of Maplewood
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header
          className="flex items-center justify-between px-8 py-4 border-b flex-shrink-0"
          style={{ borderColor: "rgba(255,255,255,0.06)", background: "#0B1220" }}
        >
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold" style={{ color: "#E8EDF5" }}>
                {activeTab === "dashboard" && "Civic Intelligence Dashboard"}
                {activeTab === "policy" && "Policy Overview"}
                {activeTab === "feedback" && "Public Feedback"}
                {activeTab === "gaps" && "Gap Analysis"}
                {activeTab === "recommendations" && "Recommendations"}
                {activeTab === "survey" && "Survey Generator"}
              </h1>
              <span
                className="text-[10px] px-2 py-0.5 rounded-sm font-medium"
                style={{
                  background: "rgba(45,212,191,0.1)",
                  color: "#2DD4BF",
                  fontFamily: "'JetBrains Mono', monospace",
                  border: "1px solid rgba(45,212,191,0.2)",
                }}
              >
                LIVE
              </span>
            </div>
            <p className="text-xs mt-0.5" style={{ color: "#4A6080" }}>
              City of Maplewood — Policy Cycle Q3 2026 · Last sync 3 min ago
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div
              className="flex items-center gap-2 px-3 py-2 rounded text-sm"
              style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              <Search size={13} style={{ color: "#4A6080" }} />
              <span style={{ color: "#4A6080" }}>Search policies…</span>
              <span
                className="text-[10px] px-1.5 py-0.5 rounded"
                style={{ background: "#162032", color: "#4A6080", fontFamily: "'JetBrains Mono', monospace" }}
              >
                ⌘K
              </span>
            </div>
            <button
              className="flex items-center gap-1.5 px-3 py-2 rounded text-sm font-medium transition-opacity"
              style={{ background: "#2DD4BF", color: "#0B1220" }}
            >
              <Download size={13} strokeWidth={2} />
              Export Report
            </button>
          </div>
        </header>

        {/* Scrollable content area */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-8 py-6">

            {/* ── DASHBOARD TAB ── */}
            {activeTab === "dashboard" && (
              <div className="space-y-6">

                {/* KPI Row */}
                <div className="grid grid-cols-4 gap-4">
                  {kpis.map((kpi) => {
                    const Icon = kpi.icon;
                    return (
                      <div
                        key={kpi.label}
                        className="rounded-lg p-5"
                        style={{
                          background: "#111827",
                          border: "1px solid rgba(255,255,255,0.07)",
                        }}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <p className="text-xs font-medium uppercase tracking-wider" style={{ color: "#6B7FA3", fontFamily: "'JetBrains Mono', monospace" }}>
                            {kpi.label}
                          </p>
                          <div
                            className="w-7 h-7 rounded flex items-center justify-center"
                            style={{ background: `${kpi.color}18` }}
                          >
                            <Icon size={14} style={{ color: kpi.color }} strokeWidth={2} />
                          </div>
                        </div>
                        <p className="text-3xl font-semibold tracking-tight mb-1" style={{ color: "#E8EDF5" }}>
                          {kpi.value}
                        </p>
                        <div className="flex items-center gap-1.5">
                          <span
                            className="text-[11px] font-medium"
                            style={{ color: kpi.direction === "up" && kpi.label !== "Critical Gaps Found" ? "#2DD4BF" : kpi.direction === "down" ? "#EF4444" : "#6B7FA3" }}
                          >
                            {kpi.delta}
                          </span>
                          <span className="text-[11px]" style={{ color: "#4A6080" }}>{kpi.sub}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-5 gap-4">
                  {/* Donut */}
                  <div
                    className="col-span-2 rounded-lg p-5"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-sm font-semibold" style={{ color: "#E8EDF5" }}>Sentiment Distribution</h3>
                        <p className="text-xs mt-0.5" style={{ color: "#4A6080" }}>Based on 2,847 responses</p>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: "#162032", color: "#6B7FA3", fontFamily: "'JetBrains Mono', monospace" }}>
                        30D
                      </span>
                    </div>
                    <div className="flex items-center gap-6">
                      <DonutChart data={sentimentData} />
                      <div className="space-y-3 flex-1">
                        {sentimentData.map((d) => (
                          <div key={d.name} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: d.color }} />
                              <span className="text-xs" style={{ color: "#A0AEC0" }}>{d.name}</span>
                            </div>
                            <span className="text-xs font-medium font-mono" style={{ color: "#E8EDF5", fontFamily: "'JetBrains Mono', monospace" }}>
                              {d.value}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Bar chart */}
                  <div
                    className="col-span-3 rounded-lg p-5"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-sm font-semibold" style={{ color: "#E8EDF5" }}>Policy Gaps by Domain</h3>
                        <p className="text-xs mt-0.5" style={{ color: "#4A6080" }}>Identified coverage deficiencies</p>
                      </div>
                      <button className="flex items-center gap-1 text-xs" style={{ color: "#2DD4BF" }}>
                        View all <ChevronRight size={12} />
                      </button>
                    </div>
                    <BarChartSVG data={gapData} />
                    <div className="flex items-center gap-4 mt-2">
                      {[["High", "#EF4444"], ["Medium", "#F59E0B"], ["Low", "#3B82F6"]].map(([label, color]) => (
                        <div key={label} className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-sm" style={{ background: color }} />
                          <span className="text-[10px]" style={{ color: "#4A6080" }}>{label} Severity</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Pipeline */}
                <div
                  className="rounded-lg p-5"
                  style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                >
                  <div className="flex items-center justify-between mb-5">
                    <div>
                      <h3 className="text-sm font-semibold" style={{ color: "#E8EDF5" }}>Multi-Agent Analysis Pipeline</h3>
                      <p className="text-xs mt-0.5" style={{ color: "#4A6080" }}>Policy Cycle Q3 2026 — Run #47</p>
                    </div>
                    <span
                      className="text-[10px] px-2 py-0.5 rounded"
                      style={{ background: "rgba(245,158,11,0.1)", color: "#F59E0B", border: "1px solid rgba(245,158,11,0.2)", fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      IN PROGRESS
                    </span>
                  </div>

                  <div className="flex items-stretch gap-0">
                    {pipelineSteps.map((step, idx) => {
                      const Icon = step.icon;
                      const isLast = idx === pipelineSteps.length - 1;
                      return (
                        <div key={step.id} className="flex items-center flex-1">
                          <div className="flex-1">
                            <div
                              className="rounded-lg p-4 relative"
                              style={{
                                background:
                                  step.status === "active"
                                    ? "rgba(45,212,191,0.06)"
                                    : step.status === "complete"
                                    ? "rgba(255,255,255,0.03)"
                                    : "rgba(255,255,255,0.01)",
                                border:
                                  step.status === "active"
                                    ? "1px solid rgba(45,212,191,0.25)"
                                    : step.status === "complete"
                                    ? "1px solid rgba(255,255,255,0.08)"
                                    : "1px solid rgba(255,255,255,0.04)",
                              }}
                            >
                              <div className="flex items-center gap-2 mb-2">
                                <div
                                  className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
                                  style={{
                                    background:
                                      step.status === "complete"
                                        ? "rgba(45,212,191,0.15)"
                                        : step.status === "active"
                                        ? "rgba(245,158,11,0.15)"
                                        : "rgba(255,255,255,0.05)",
                                  }}
                                >
                                  <Icon
                                    size={12}
                                    style={{
                                      color:
                                        step.status === "complete"
                                          ? "#2DD4BF"
                                          : step.status === "active"
                                          ? "#F59E0B"
                                          : "#3D5070",
                                    }}
                                    strokeWidth={2}
                                  />
                                </div>
                                <div
                                  className="w-2 h-2 rounded-full"
                                  style={{
                                    background:
                                      step.status === "complete"
                                        ? "#2DD4BF"
                                        : step.status === "active"
                                        ? "#F59E0B"
                                        : "#1E2D40",
                                  }}
                                />
                              </div>
                              <p
                                className="text-xs font-semibold mb-0.5"
                                style={{
                                  color:
                                    step.status === "complete"
                                      ? "#E8EDF5"
                                      : step.status === "active"
                                      ? "#F59E0B"
                                      : "#3D5070",
                                }}
                              >
                                {step.label}
                              </p>
                              <p className="text-[10px] leading-tight" style={{ color: "#3D5070" }}>
                                {step.sublabel}
                              </p>
                              <div className="mt-2.5">
                                <span
                                  className="text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider font-medium"
                                  style={{
                                    fontFamily: "'JetBrains Mono', monospace",
                                    background:
                                      step.status === "complete"
                                        ? "rgba(45,212,191,0.1)"
                                        : step.status === "active"
                                        ? "rgba(245,158,11,0.1)"
                                        : "rgba(255,255,255,0.04)",
                                    color:
                                      step.status === "complete"
                                        ? "#2DD4BF"
                                        : step.status === "active"
                                        ? "#F59E0B"
                                        : "#3D5070",
                                  }}
                                >
                                  {step.status === "complete" ? "Complete" : step.status === "active" ? "Running" : "Queued"}
                                </span>
                              </div>
                            </div>
                          </div>
                          {!isLast && (
                            <div className="flex items-center px-1.5 flex-shrink-0">
                              <ArrowRight
                                size={14}
                                style={{ color: idx < 2 ? "#2DD4BF" : idx === 2 ? "#F59E0B" : "#1E2D40" }}
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Bottom row: recent feedback + executive memo preview */}
                <div className="grid grid-cols-3 gap-4">
                  <div
                    className="col-span-2 rounded-lg p-5"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold" style={{ color: "#E8EDF5" }}>Recent Public Feedback</h3>
                      <button className="text-xs" style={{ color: "#2DD4BF" }} onClick={() => setActiveTab("feedback")}>
                        View all responses →
                      </button>
                    </div>
                    <div className="space-y-3">
                      {feedbackData.slice(0, 2).map((item) => (
                        <div
                          key={item.id}
                          className="p-3.5 rounded-lg"
                          style={{ background: "#0D1626", border: "1px solid rgba(255,255,255,0.05)" }}
                        >
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <div className="flex items-center gap-2">
                              <div
                                className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0"
                                style={{ background: "#1E3A5F", color: "#93C5FD" }}
                              >
                                {item.author.charAt(0)}
                              </div>
                              <div>
                                <span className="text-xs font-medium" style={{ color: "#E8EDF5" }}>{item.author}</span>
                                <span className="text-[10px] ml-1.5" style={{ color: "#4A6080" }}>{item.role}</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <span
                                className="text-[10px] px-2 py-0.5 rounded capitalize"
                                style={{
                                  background: `${sentimentColor[item.sentiment]}15`,
                                  color: sentimentColor[item.sentiment],
                                  fontFamily: "'JetBrains Mono', monospace",
                                  border: `1px solid ${sentimentColor[item.sentiment]}30`,
                                }}
                              >
                                {sentimentLabel[item.sentiment]}
                              </span>
                              <span className="text-[10px]" style={{ color: "#3D5070" }}>{item.date}</span>
                            </div>
                          </div>
                          <p className="text-xs leading-relaxed" style={{ color: "#8A9AB5" }}>{item.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Quick stats */}
                  <div
                    className="rounded-lg p-5 flex flex-col"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <h3 className="text-sm font-semibold mb-4" style={{ color: "#E8EDF5" }}>System Summary</h3>
                    <div className="space-y-4 flex-1">
                      {[
                        { label: "Policies Analyzed", value: "34", icon: FileText, color: "#3B82F6" },
                        { label: "Responses Ingested", value: "2,847", icon: Users, color: "#2DD4BF" },
                        { label: "Active Policy Areas", value: "6", icon: BarChart3, color: "#F59E0B" },
                        { label: "Compliance Score", value: "87%", icon: Shield, color: "#8B5CF6" },
                      ].map((s) => {
                        const Icon = s.icon;
                        return (
                          <div key={s.label} className="flex items-center justify-between">
                            <div className="flex items-center gap-2.5">
                              <div className="w-6 h-6 rounded flex items-center justify-center" style={{ background: `${s.color}15` }}>
                                <Icon size={12} style={{ color: s.color }} />
                              </div>
                              <span className="text-xs" style={{ color: "#6B7FA3" }}>{s.label}</span>
                            </div>
                            <span className="text-sm font-semibold" style={{ color: "#E8EDF5", fontFamily: "'JetBrains Mono', monospace" }}>
                              {s.value}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                    <button
                      onClick={() => setActiveTab("recommendations")}
                      className="mt-5 w-full text-xs py-2 rounded font-medium flex items-center justify-center gap-1.5 transition-opacity hover:opacity-80"
                      style={{ background: "rgba(45,212,191,0.1)", color: "#2DD4BF", border: "1px solid rgba(45,212,191,0.2)" }}
                    >
                      View Recommendations <ArrowRight size={11} />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ── POLICY OVERVIEW TAB ── */}
            {activeTab === "policy" && (
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { title: "Transit Expansion Bill 2026-T4", status: "Under Review", area: "Infrastructure", responses: 842, support: 61 },
                    { title: "Affordable Housing Density Amendment", status: "Public Comment", area: "Housing", responses: 1203, support: 49 },
                    { title: "Climate Resilience Zoning Ordinance", status: "Draft", area: "Environment", responses: 318, support: 55 },
                    { title: "Fiscal Year 2027 Budget Framework", status: "Committee", area: "Finance", responses: 484, support: 42 },
                  ].map((policy) => (
                    <div
                      key={policy.title}
                      className="rounded-lg p-5"
                      style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                    >
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div>
                          <h4 className="text-sm font-semibold mb-1" style={{ color: "#E8EDF5" }}>{policy.title}</h4>
                          <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: "#162032", color: "#6B7FA3", fontFamily: "'JetBrains Mono', monospace" }}>
                            {policy.area}
                          </span>
                        </div>
                        <span
                          className="text-[10px] px-2 py-0.5 rounded flex-shrink-0"
                          style={{
                            background: policy.status === "Under Review" ? "rgba(245,158,11,0.1)" : policy.status === "Public Comment" ? "rgba(59,130,246,0.1)" : "rgba(255,255,255,0.05)",
                            color: policy.status === "Under Review" ? "#F59E0B" : policy.status === "Public Comment" ? "#3B82F6" : "#6B7FA3",
                            fontFamily: "'JetBrains Mono', monospace",
                          }}
                        >
                          {policy.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mb-3">
                        <div>
                          <p className="text-[10px] mb-1" style={{ color: "#4A6080" }}>Public Support</p>
                          <p className="text-lg font-semibold" style={{ color: "#2DD4BF", fontFamily: "'JetBrains Mono', monospace" }}>{policy.support}%</p>
                        </div>
                        <div>
                          <p className="text-[10px] mb-1" style={{ color: "#4A6080" }}>Responses</p>
                          <p className="text-lg font-semibold" style={{ color: "#E8EDF5", fontFamily: "'JetBrains Mono', monospace" }}>{policy.responses.toLocaleString()}</p>
                        </div>
                      </div>
                      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "#162032" }}>
                        <div className="h-full rounded-full" style={{ width: `${policy.support}%`, background: "linear-gradient(90deg, #2DD4BF, #3B82F6)" }} />
                      </div>
                      <div className="flex justify-end mt-3">
                        <button className="flex items-center gap-1 text-xs" style={{ color: "#6B7FA3" }}>
                          Full Analysis <ExternalLink size={11} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── FEEDBACK TAB ── */}
            {activeTab === "feedback" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs" style={{ color: "#4A6080" }}>Showing 4 of 2,847 responses · Sorted by recency</p>
                  <div className="flex items-center gap-2">
                    {["All", "Support", "Opposition", "Neutral"].map((f) => (
                      <button
                        key={f}
                        className="text-xs px-3 py-1.5 rounded transition-colors"
                        style={{ background: f === "All" ? "#2DD4BF" : "#111827", color: f === "All" ? "#0B1220" : "#6B7FA3", border: "1px solid rgba(255,255,255,0.07)" }}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                </div>
                {feedbackData.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-lg p-5"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)", borderLeft: `3px solid ${sentimentColor[item.sentiment]}` }}
                  >
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0"
                          style={{ background: "#1E3A5F", color: "#93C5FD" }}
                        >
                          {item.author.charAt(0)}
                        </div>
                        <div>
                          <p className="text-sm font-medium" style={{ color: "#E8EDF5" }}>{item.author}</p>
                          <p className="text-xs" style={{ color: "#4A6080" }}>{item.role}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span
                          className="text-[10px] px-2 py-0.5 rounded capitalize"
                          style={{ background: `${sentimentColor[item.sentiment]}15`, color: sentimentColor[item.sentiment], fontFamily: "'JetBrains Mono', monospace", border: `1px solid ${sentimentColor[item.sentiment]}30` }}
                        >
                          {sentimentLabel[item.sentiment]}
                        </span>
                        <span className="text-xs" style={{ color: "#3D5070" }}>{item.date}</span>
                      </div>
                    </div>
                    <p className="text-sm leading-relaxed mb-3" style={{ color: "#8A9AB5" }}>{item.text}</p>
                    <div className="flex items-center gap-2">
                      {item.tags.map((tag) => (
                        <span key={tag} className="text-[10px] px-2 py-0.5 rounded" style={{ background: "#162032", color: "#6B7FA3" }}>{tag}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ── GAP ANALYSIS TAB ── */}
            {activeTab === "gaps" && (
              <div className="space-y-4">
                <div
                  className="rounded-lg p-5"
                  style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                >
                  <h3 className="text-sm font-semibold mb-4" style={{ color: "#E8EDF5" }}>Policy Gap Registry</h3>
                  <div className="space-y-3">
                    {[
                      { domain: "Housing Policy", gap: "No inclusionary zoning requirement for developments under 20 units", severity: "High", policy: "Affordable Housing Density Amendment" },
                      { domain: "Healthcare Access", gap: "Mobile clinic coverage excludes Districts 4, 6, and 9", severity: "High", policy: "Community Health Services Framework" },
                      { domain: "Transit Funding", gap: "Funding formula does not account for low-density connectivity deficits", severity: "High", policy: "Transit Expansion Bill 2026-T4" },
                      { domain: "Education Reform", gap: "Per-pupil equity adjustments lag state benchmarks by 3 fiscal years", severity: "Medium", policy: "Public Education Equity Plan" },
                      { domain: "Climate Zoning", gap: "No enforcement mechanism for tree canopy preservation ordinance", severity: "Medium", policy: "Climate Resilience Zoning Ordinance" },
                      { domain: "Fiscal Policy", gap: "Capital reserve fund lacks statutory minimum floor", severity: "Low", policy: "FY2027 Budget Framework" },
                    ].map((g, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-4 p-4 rounded-lg"
                        style={{ background: "#0D1626", border: "1px solid rgba(255,255,255,0.05)" }}
                      >
                        <div className="w-1.5 h-full rounded-full flex-shrink-0 mt-1" style={{ background: priorityColor[g.severity], minHeight: 40 }} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <p className="text-xs font-semibold" style={{ color: "#E8EDF5" }}>{g.gap}</p>
                            <span
                              className="text-[10px] px-2 py-0.5 rounded flex-shrink-0"
                              style={{ background: `${priorityColor[g.severity]}15`, color: priorityColor[g.severity], fontFamily: "'JetBrains Mono', monospace" }}
                            >
                              {g.severity}
                            </span>
                          </div>
                          <p className="text-[11px]" style={{ color: "#4A6080" }}>
                            {g.domain} · <span style={{ color: "#3B82F6" }}>{g.policy}</span>
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── RECOMMENDATIONS TAB ── */}
            {activeTab === "recommendations" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs" style={{ color: "#4A6080" }}>4 recommendations · Priority ranked by Gap Agent</p>
                </div>
                {recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg overflow-hidden"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)", borderLeft: `3px solid ${priorityColor[rec.priority]}` }}
                  >
                    <button
                      className="w-full flex items-center justify-between p-4 text-left"
                      onClick={() => setExpandedRecommendation(expandedRecommendation === idx ? null : idx)}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span
                          className="text-[10px] px-2 py-0.5 rounded flex-shrink-0"
                          style={{ background: `${priorityColor[rec.priority]}15`, color: priorityColor[rec.priority], fontFamily: "'JetBrains Mono', monospace" }}
                        >
                          {rec.priority}
                        </span>
                        <p className="text-sm font-medium truncate" style={{ color: "#E8EDF5" }}>{rec.title}</p>
                      </div>
                      <ChevronDown
                        size={14}
                        style={{ color: "#4A6080", flexShrink: 0, transform: expandedRecommendation === idx ? "rotate(180deg)" : "none", transition: "transform 0.15s" }}
                      />
                    </button>
                    {expandedRecommendation === idx && (
                      <div className="px-4 pb-4 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
                        <p className="text-sm leading-relaxed mt-3 mb-3" style={{ color: "#8A9AB5" }}>{rec.description}</p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div>
                              <p className="text-[10px] mb-0.5" style={{ color: "#3D5070" }}>Assigned To</p>
                              <p className="text-xs" style={{ color: "#A0AEC0" }}>{rec.assignee}</p>
                            </div>
                            <div>
                              <p className="text-[10px] mb-0.5" style={{ color: "#3D5070" }}>Status</p>
                              <p className="text-xs" style={{ color: "#A0AEC0" }}>{rec.status}</p>
                            </div>
                          </div>
                          <button className="text-xs px-3 py-1.5 rounded" style={{ background: "rgba(45,212,191,0.1)", color: "#2DD4BF", border: "1px solid rgba(45,212,191,0.2)" }}>
                            Assign Task
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* ── SURVEY GENERATOR TAB ── */}
            {activeTab === "survey" && (
              <div className="grid grid-cols-3 gap-6">
                {/* Builder */}
                <div className="col-span-2 space-y-4">
                  <div
                    className="rounded-lg p-5"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <div className="flex items-center justify-between mb-5">
                      <div>
                        <h3 className="text-sm font-semibold" style={{ color: "#E8EDF5" }}>Civic Feedback Survey — Q3 2026</h3>
                        <p className="text-xs mt-0.5" style={{ color: "#4A6080" }}>City of Maplewood · Policy Cycle Q3</p>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: "#162032", color: "#6B7FA3", fontFamily: "'JetBrains Mono', monospace" }}>
                        DRAFT
                      </span>
                    </div>

                    {/* Survey meta */}
                    <div className="grid grid-cols-2 gap-3 mb-5">
                      <div>
                        <label className="text-xs font-medium block mb-1.5" style={{ color: "#6B7FA3" }}>Survey Title</label>
                        <input
                          type="text"
                          defaultValue="Q3 2026 Public Policy Feedback Survey"
                          className="w-full rounded px-3 py-2 text-sm outline-none focus:ring-1"
                          style={{ background: "#0D1626", border: "1px solid rgba(255,255,255,0.08)", color: "#E8EDF5", ringColor: "#2DD4BF" }}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium block mb-1.5" style={{ color: "#6B7FA3" }}>Target Audience</label>
                        <input
                          type="text"
                          defaultValue="City of Maplewood Residents"
                          className="w-full rounded px-3 py-2 text-sm outline-none"
                          style={{ background: "#0D1626", border: "1px solid rgba(255,255,255,0.08)", color: "#E8EDF5" }}
                        />
                      </div>
                    </div>

                    {/* Questions */}
                    <div className="space-y-3">
                      {surveyQuestionList.map((q, idx) => (
                        <div
                          key={q.id}
                          className="rounded-lg p-4"
                          style={{ background: "#0D1626", border: "1px solid rgba(255,255,255,0.06)" }}
                        >
                          <div className="flex items-start gap-3">
                            <GripVertical size={14} style={{ color: "#3D5070", marginTop: 2, flexShrink: 0 }} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <span
                                  className="text-[10px] px-2 py-0.5 rounded"
                                  style={{
                                    fontFamily: "'JetBrains Mono', monospace",
                                    background: "#162032",
                                    color: "#6B7FA3",
                                  }}
                                >
                                  {q.type === "multiple_choice" ? "Multiple Choice" : q.type === "scale" ? "1–10 Scale" : "Open Text"}
                                </span>
                                <span className="text-[10px]" style={{ color: "#3D5070" }}>Q{idx + 1}</span>
                              </div>
                              <p className="text-sm" style={{ color: "#E8EDF5" }}>{q.question}</p>
                              {q.options.length > 0 && (
                                <div className="mt-2 space-y-1">
                                  {q.options.map((opt, oi) => (
                                    <div key={oi} className="flex items-center gap-2">
                                      <Circle size={10} style={{ color: "#3D5070" }} />
                                      <span className="text-xs" style={{ color: "#6B7FA3" }}>{opt}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {q.type === "scale" && (
                                <div className="flex items-center gap-1 mt-2">
                                  {[1,2,3,4,5,6,7,8,9,10].map((n) => (
                                    <div
                                      key={n}
                                      className="w-7 h-7 rounded flex items-center justify-center text-xs"
                                      style={{ background: "#162032", color: "#6B7FA3" }}
                                    >
                                      {n}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                            <button
                              onClick={() => removeQuestion(q.id)}
                              className="flex-shrink-0 p-1 rounded hover:opacity-80 transition-opacity"
                              style={{ color: "#3D5070" }}
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>

                    <button
                      onClick={addQuestion}
                      className="mt-4 w-full flex items-center justify-center gap-2 py-2.5 rounded text-sm transition-opacity hover:opacity-80"
                      style={{ background: "#162032", color: "#6B7FA3", border: "1px dashed rgba(255,255,255,0.1)" }}
                    >
                      <Plus size={13} /> Add Question
                    </button>
                  </div>
                </div>

                {/* Deploy panel */}
                <div className="space-y-4">
                  <div
                    className="rounded-lg p-5"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <h3 className="text-sm font-semibold mb-4" style={{ color: "#E8EDF5" }}>Deployment Settings</h3>
                    <div className="space-y-3">
                      {[
                        { label: "Distribution Channel", value: "City Portal + Email" },
                        { label: "Response Deadline", value: "July 15, 2026" },
                        { label: "Anonymization", value: "Enabled" },
                        { label: "Auto-Analysis", value: "On completion" },
                      ].map((s) => (
                        <div key={s.label} className="flex items-center justify-between py-2 border-b" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
                          <span className="text-xs" style={{ color: "#6B7FA3" }}>{s.label}</span>
                          <span className="text-xs font-medium" style={{ color: "#A0AEC0" }}>{s.value}</span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 p-3 rounded-lg" style={{ background: "#0D1626", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <p className="text-[10px] mb-1" style={{ color: "#3D5070" }}>Survey URL</p>
                      <p className="text-xs font-mono break-all" style={{ color: "#3B82F6", fontFamily: "'JetBrains Mono', monospace" }}>
                        maplewood.gov/survey/q3-2026
                      </p>
                    </div>
                    <button
                      className="mt-4 w-full py-2.5 rounded text-sm font-semibold transition-opacity hover:opacity-90 flex items-center justify-center gap-2"
                      style={{ background: "linear-gradient(135deg, #2DD4BF 0%, #3B82F6 100%)", color: "#0B1220" }}
                    >
                      <CheckCircle2 size={14} strokeWidth={2.5} />
                      Deploy Form
                    </button>
                    <button
                      className="mt-2 w-full py-2 rounded text-sm transition-opacity hover:opacity-80 flex items-center justify-center gap-2"
                      style={{ background: "#162032", color: "#6B7FA3" }}
                    >
                      <Download size={13} /> Export as PDF
                    </button>
                  </div>

                  {/* Executive memo preview */}
                  <div
                    className="rounded-lg p-5"
                    style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold" style={{ color: "#E8EDF5" }}>Executive Memo</h3>
                      <button className="flex items-center gap-1 text-xs" style={{ color: "#6B7FA3" }}>
                        <Printer size={11} /> Print
                      </button>
                    </div>
                    <div
                      className="rounded p-4"
                      style={{ background: "#F8F7F4", border: "1px solid #E0DDD8" }}
                    >
                      <div className="border-b pb-3 mb-3" style={{ borderColor: "#D4CFC8" }}>
                        <p className="text-[10px] tracking-widest uppercase mb-1" style={{ color: "#8A8070", fontFamily: "'JetBrains Mono', monospace" }}>
                          CITY OF MAPLEWOOD — OFFICIAL MEMORANDUM
                        </p>
                        <h4 className="text-sm font-bold leading-snug" style={{ color: "#1A1510", fontFamily: "'Libre Baskerville', serif" }}>
                          Policy Analysis Summary: Q3 2026
                        </h4>
                      </div>
                      <div className="space-y-1 mb-3">
                        {[
                          ["TO:", "City Council Members"],
                          ["FROM:", "Office of Civic Intelligence"],
                          ["DATE:", "June 17, 2026"],
                          ["RE:", "Public Feedback & Gap Analysis"],
                        ].map(([key, val]) => (
                          <div key={key} className="flex gap-2 text-[10px]" style={{ color: "#5A5040" }}>
                            <span className="font-semibold w-10 flex-shrink-0" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{key}</span>
                            <span>{val}</span>
                          </div>
                        ))}
                      </div>
                      <p className="text-[10px] leading-relaxed" style={{ color: "#6A6050" }}>
                        Analysis of 2,847 public responses identified 40 policy gaps across 6 domains. Public support at 54%; primary concerns center on transit equity and housing affordability.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
