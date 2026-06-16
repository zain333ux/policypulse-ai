# Product Requirement Document — PolicyPulse AI

## 1. Product Name

PolicyPulse AI

## 2. One-Line Pitch

PolicyPulse AI turns proposed policies and public/student comments into clear concerns, policy gaps, and actionable recommendations using a multi-agent AI workflow.

## 3. Problem Statement

Universities, local governments, NGOs, and civic organizations often collect public feedback on proposed policies, but the feedback is usually difficult to analyze manually.

Common problems include:

* Large numbers of comments are hard to read quickly.
* Repeated concerns are missed.
* Minority or affected groups may be ignored.
* Policy gaps are not clearly identified.
* Decision-makers may receive only a basic summary instead of actionable recommendations.
* Students and citizens may feel that feedback is collected but not understood.

PolicyPulse AI solves this by automatically analyzing a policy document and public comments to produce a structured consultation report.

## 4. Target Users

Primary users:

* University administrations
* Student councils
* City councils
* NGOs
* Civic organizations
* Public policy researchers
* Community organizers

For the hackathon demo, the main target user is:

A university administration or student council reviewing student feedback on a new attendance policy.

## 5. Theme Fit

PolicyPulse AI fits two hackathon themes:

### Education

It can analyze university policies such as:

* attendance policy
* exam policy
* fee policy
* hostel policy
* grading policy
* scholarship policy
* transport policy

### Civic Tech

It can analyze public consultation documents such as:

* city policy proposals
* community feedback
* public complaints
* local government notices
* NGO program rules

## 6. MVP Goal

Build a working Streamlit app where a user can:

1. Upload or paste a policy document.
2. Upload or paste public/student comments.
3. Click an analyze button.
4. See a multi-agent AI-generated consultation report.

## 7. MVP Inputs

The MVP should support:

### Policy Input

* PDF upload
* TXT upload
* pasted text fallback

### Comments Input

* CSV upload
* TXT upload
* pasted comments fallback

The comments file may contain one comment per row or one comment per line.

## 8. MVP Outputs

The app should generate:

1. Policy Summary
2. Support / Opposition / Neutral analysis
3. Top public concerns
4. Affected groups
5. Policy gap analysis
6. Recommended policy changes
7. Suggested revised wording
8. Public meeting questions
9. Executive memo
## Optional Bonus Feature: Feedback Survey Generator

If an organization has not collected public or student feedback yet, PolicyPulse AI can generate a ready-to-use survey template based on the uploaded policy.

This survey can be copied into Google Forms and shared through a link.

The generated survey should include:
- survey title
- survey description
- 6–8 policy-specific questions
- question types such as multiple choice, paragraph, checkbox, and linear scale
- answer options where needed
- reason/purpose for each question
- copy-ready sharing message

For the hackathon MVP, the app will not automatically create a real Google Form. It will generate a Google-Forms-ready structure that the user can copy manually.

Future versions may integrate directly with Google Forms API or Google Apps Script.
## 9. Multi-Agent Workflow

The system uses five logical agents.

### Agent 1: Policy Extraction Agent

Reads the policy and extracts:

* policy title
* main rules
* deadlines
* penalties
* affected groups
* unclear clauses
* missing definitions

### Agent 2: Public Sentiment Agent

Reads the comments and analyzes:

* support
* opposition
* neutral or mixed feedback
* emotional tone
* urgency level

### Agent 3: Concern Clustering Agent

Groups comments into repeated concern themes such as:

* fairness
* medical exemptions
* working students
* disability accommodations
* transportation issues
* appeal process
* implementation clarity

### Agent 4: Gap Detection Agent

Compares the policy against the concerns and identifies:

* issues covered by the policy
* issues not covered by the policy
* unclear policy areas
* missing protections
* affected groups not considered

### Agent 5: Recommendation Agent

Generates:

* recommended changes
* revised policy wording
* questions for decision-makers
* executive memo

## 10. Demo Scenario

The demo scenario is a university attendance policy.

### Policy

The university proposes a rule requiring students to maintain 85% attendance in every course. Students below 85% attendance will not be allowed to sit in final exams. The policy does not clearly mention exemptions, appeal process, medical cases, disability accommodations, or students with transport issues.

### Sample Comment Themes

The uploaded comments should include:

* students who support attendance discipline
* working students concerned about flexibility
* students asking for medical exemptions
* students asking for an appeal process
* students concerned about transport issues
* students with disability or health needs
* students asking how attendance disputes will be handled
* students saying the policy is too strict

## 11. User Flow

1. User opens the Streamlit app.
2. User uploads or pastes policy text.
3. User uploads or pastes comments.
4. User clicks “Analyze Public Feedback”.
5. The app runs each AI agent in sequence.
6. The app displays results in tabs.
7. User reviews insights, recommendations, and executive memo.

## 12. UI Requirements

The Streamlit app should include:

* Page title: PolicyPulse AI
* Caption: Turn public feedback into clear policy decisions.
* Short explanation of the app
* Policy upload section
* Comments upload section
* Sample data option
* Analyze button
* Loading spinners
* Results tabs

Results tabs:

1. Overview
2. Public Concerns
3. Policy Gaps
4. Recommendations
5. Executive Memo

## 13. Out of Scope for Hackathon MVP

Do not build:

* user login
* database
* admin dashboard
* real-time collaboration
* cloud deployment
* payment system
* legal compliance engine
* vector database
* complex CrewAI setup
* external government API integrations
- direct Google Forms API integration unless time remains
- OAuth setup for Google Forms
- automatic response fetching from Google Forms
## 14. Success Criteria

The MVP is successful if:

* The app starts without import errors.
* The user can provide policy and comment inputs.
* The multi-agent pipeline runs end-to-end.
* Each agent produces structured output.
* Results are displayed clearly.
* The demo can be completed in under 5 minutes.
* The final output looks useful to a university or civic decision-maker.

## 15. Judging Criteria Alignment

### Technical Implementation

The project demonstrates file parsing, API integration, multi-agent workflow, structured output, and Streamlit dashboard.

### Innovation

The app goes beyond summarization by comparing public concerns against policy content and generating policy improvement recommendations.

### Real-World Relevance

Public consultation is a real challenge in education and civic decision-making. PolicyPulse AI helps organizations understand feedback more fairly and efficiently.

### Presentation

The app has a clear story, simple demo, and visible output that judges can understand quickly.

## 16. Final Presentation Statement

Public feedback is often collected but not properly understood. PolicyPulse AI uses multiple AI agents to turn proposed policies and public comments into clear concerns, policy gaps, and actionable recommendations.
