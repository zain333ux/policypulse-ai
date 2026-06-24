# PolicyPulse AI Design System

This file is the visual source of truth for the production MVP. It follows the
workflow and pre-delivery checks in `ui-ux-pro-max-skill-main`.

## Product direction

- Pattern: focused AI-native SaaS workspace.
- Tone: civic, trustworthy, calm, precise.
- Primary action: one prominent CTA per screen.
- Avoid: futuristic HUD styling, constant animation, emoji icons, decorative AI
  gradients, tiny uppercase labels, and low-contrast gray text.

## Foundations

- Heading font: Lexend.
- Body font: Source Sans 3.
- Spacing: 4px base with an 8px layout rhythm.
- Icons: Lucide, consistent outline style.
- Radius: 12px controls, 16px cards, 24px primary workspace surfaces.
- Motion: 150–300ms state transitions using opacity or transform only.

## Semantic colors

| Role | Light | Dark |
| --- | --- | --- |
| Background | `#F6F9FC` | `#08111F` |
| Surface | `#FFFFFF` | `#0D1828` |
| Foreground | `#0F172A` | `#F1F5F9` |
| Muted text | `#526176` | `#B1BFD0` |
| Border | `#DCE6EF` | `#23344A` |
| Primary | `#0284C7` | `#38BDF8` |
| Primary soft | `#E0F2FE` | `#0C2D43` |
| Success | `#15803D` | `#4ADE80` |
| Warning | `#B45309` | `#FBBF24` |
| Danger | `#B91C1C` | `#F87171` |

## Interaction and accessibility

- Minimum interactive target: 44×44px.
- Visible labels for inputs; placeholders are examples, not labels.
- Visible keyboard focus ring on every interactive element.
- Normal text contrast must meet WCAG AA.
- Never communicate status through color alone.
- Respect `prefers-reduced-motion`.
- Provide a table alongside charts.
- Validate at 375, 768, 1024, and 1440 pixels without horizontal overflow.

## Page rules

- Landing: concise hero, three benefits, one CTA, then the workspace.
- Input workspace: policy and feedback are two clear steps with inline counts
  and validation.
- Progress: list each real analysis stage and its state.
- Results desktop: sticky report navigation, main content, evidence panel.
- Results mobile: horizontal section controls and a bottom evidence sheet.
- Reports: use document-like typography and include methodology and limitations.

