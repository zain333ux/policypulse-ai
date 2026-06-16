# DEMO_PLAN.md — PolicyPulse AI

## Project Name

PolicyPulse AI

## One-Line Pitch

PolicyPulse AI turns proposed policies and public/student comments into clear concerns, policy gaps, and actionable recommendations using a multi-agent AI workflow.

---

## Demo Scenario

The demo uses a university attendance policy.

The university proposes a strict rule:

Students must maintain 85% attendance in every course to sit in final exams. The policy does not clearly mention medical exemptions, appeal process, disability accommodations, working students, transport issues, or attendance dispute handling.

Students submit feedback comments.

PolicyPulse AI analyzes the policy and comments, then produces a public consultation report.

---

## Demo Goal

Show that PolicyPulse AI is not just a summarizer.

It acts like an AI public consultation committee that:

1. Understands the policy.
2. Listens to public/student feedback.
3. Groups repeated concerns.
4. Finds gaps between policy and feedback.
5. Suggests better policy wording.
6. Creates an executive memo.

---

## 3–5 Minute Demo Flow

### 1. Opening Problem — 30 seconds

Say:

“Public feedback is often collected, but it is not always properly understood. Universities, councils, and NGOs may receive hundreds of comments on a policy, but decision-makers need a fast way to identify repeated concerns, affected groups, and missing protections.”

---

### 2. Introduce Solution — 30 seconds

Say:

“PolicyPulse AI solves this by using a multi-agent workflow. A user uploads a proposed policy and public comments. The agents analyze the policy, measure public sentiment, cluster concerns, detect policy gaps, and generate recommendations.”

---

### 3. Show Inputs — 30 seconds

In the app, show:

* policy input section
* comments input section
* sample data button

Say:

“For this demo, we are using a university attendance policy and sample student comments.”

---

### 4. Run Analysis — 30 seconds

Click:

Analyze Public Feedback

While it runs, say:

“The system is running five agents: policy extraction, sentiment analysis, concern clustering, gap detection, and recommendation generation.”

---

### 5. Show Results — 90 seconds

Show these tabs:

#### Overview

Highlight:

* policy summary
* support/opposition numbers
* overall mood

#### Public Concerns

Highlight:

* medical exemptions
* appeal process
* working students
* transport issues
* fairness concerns

#### Policy Gaps

Highlight:

* policy does not define appeal process
* policy does not mention medical cases
* policy does not mention disability accommodations
* policy does not explain attendance dispute handling

#### Recommendations

Highlight:

* add medical exemption clause
* add appeal process
* define attendance dispute process
* create flexibility for verified emergency cases

#### Executive Memo

Show the final copy-ready memo.

Say:

“This memo can be used by a university committee, student council, or civic office to make a more informed decision.”

---

## Closing Statement — 30 seconds

Say:

“PolicyPulse AI improves public consultation by turning messy feedback into structured decisions. It helps institutions listen better, identify policy gaps, and respond with fairer recommendations.”

---

## Why This Project Fits the Hackathon

### Technical Implementation

The project uses:

* Python
* Streamlit
* file upload
* CSV/text parsing
* LLM API integration
* structured multi-agent pipeline
* dashboard output

### Innovation

It is not a chatbot and not a simple PDF summarizer. It compares public concerns against policy content and generates decision-support recommendations.

### Real-World Relevance

Universities, city councils, NGOs, and student bodies regularly collect feedback but struggle to analyze it clearly and fairly.

### Presentation

The demo is simple, visual, and easy to understand in under five minutes.

---

## Backup Demo Plan

If API fails:

1. Show the sample input files.
2. Show the app interface.
3. Explain the agent workflow.
4. Use pre-saved example output screenshots or cached sample output if available.
5. Present the final memo manually.

---

## Demo Files Needed

Create these files:

* `sample_data/attendance_policy.txt`
* `sample_data/student_comments.csv`

Optional later:

* `sample_data/sample_output.json`
* `sample_data/demo_report.md`

---

## Final Winning Line

“PolicyPulse AI helps institutions move from collecting feedback to actually understanding it.”
