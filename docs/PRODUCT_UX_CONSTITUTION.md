# Bioloop Product and UX Constitution

This is the first product document to read before designing or implementing Bioloop features.

Bioloop is artifact-first, not dashboard-first. It should feel like a private museum of the user's wearable history: calm, premium, reflective, private, and artful.

The product should make the user think:

> "This is my life. I have never seen it this way before."

## Source of Truth

This constitution is the operational summary of:

- [Product Experience Design](PRODUCT_EXPERIENCE_DESIGN.md)
- [Visual References](VISUAL_REFERENCES.md)

When implementation details are unclear, choose the path that best preserves the artifact-first, privacy-first, narrative-supported experience described in those documents.

## Core Rule

Build artifact-first, not dashboard-first.

The first experience should create emotional recognition through a beautiful artifact, especially Life Rings, before exposing metrics, controls, or analysis. Metrics are material for stories and artifacts. They are not the primary destination.

## Product Priority

Coding agents should prioritize these product spaces in this order:

1. Stories
2. Artifacts
3. Timeline
4. Studio
5. Settings / Privacy

Avoid organizing the main app around metric tabs such as Sleep, HRV, Readiness, Activity, Scores, Trends, and Insights. Those views can exist later as supporting depth, but they should not define the user's first impression.

## First Experience

The first-run experience should:

- Show a compelling example artifact before asking for work.
- Connect or import one source.
- Render the first meaningful artifact as quickly as possible.
- Use Life Rings as the flagship first artifact when enough data is available.
- Explain the artifact with one short, human-readable narrative.
- Offer save, personalize, export, print, and privacy controls after the emotional reveal.

Do not make users configure dashboards before they understand the value.

## Preferred Patterns

Favor:

- Beautiful artifacts with clear data mappings.
- Reflective stories supported by evidence.
- Timeline exploration that moves from years to days.
- Studio-style creation and customization.
- Privacy-safe exports and print-ready outputs.
- Museum-caption language near visuals.
- Calm, editorial, premium visual design.

Use language such as:

- "Your data shows..."
- "This period appears..."
- "Every ring is a day."
- "A quiet record of 2,316 nights."
- "Your rhythm changed here. Add a memory?"

## Avoided Patterns

Do not lead with:

- Metric-dashboard homepage.
- Chatbot as primary interface.
- Red/green scoring systems.
- Gamification, streaks, trophies, leaderboards, or competitive sharing.
- Medical claims, diagnosis, treatment, or causal overreach.
- Raw health values in shared outputs by default.
- Dense tables or analytics cards above the fold.
- Optimization-pressure copy.

Avoid language such as:

- "You failed..."
- "You should..."
- "This caused..."
- "AI detected poor lifestyle choices."
- "Improve your readiness by 12 percent."

## Privacy Rule

Privacy is part of the emotional experience, not a compliance footer.

Shared and exported artifacts should hide raw health values by default. Show patterns, rhythm, seasons, date ranges, and user-approved captions first. Exact HRV, resting heart rate, readiness scores, sensitive dates, and medical-looking labels require explicit user choice.

## Narrative Rule

Narrative should be reflective, humble, editable, evidence-based, and privacy-safe.

Every generated narrative should be traceable to source data or derived metrics and should support an optional "Why we said this" explanation. Never diagnose, moralize, or imply causality the data cannot support.

## Feature Decision Checklist

Before adding a feature, ask:

1. Does this help users see themselves more clearly?
2. Does this make the artifact more beautiful, meaningful, or trustworthy?
3. Does this preserve privacy by default?
4. Does this reduce dashboard anxiety?
5. Does this support stories, memories, or art?
6. Could this be saved, printed, or shared safely?
7. Is this better as a narrative moment than as another chart?
8. Would this still feel calm, premium, reflective, private, and artful?

If the answer is mostly no, do not build it yet.
