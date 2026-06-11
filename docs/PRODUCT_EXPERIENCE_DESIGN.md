# Bioloop Product Experience Design Document

**Product idea:** Turn your wearable data into stories, memories, and art.  
**Document purpose:** Align product, design, engineering, and coding agents around the intended UX, UI, emotional tone, and non-goals.  
**Version:** Draft v0.1 - 2026-06-10

---

## 1. North Star

Bioloop is not another wearable dashboard.

Bioloop is a private studio that transforms long-term wearable history into beautiful, emotionally meaningful artifacts: life rings, seasonal maps, recovery landscapes, story cards, and museum-grade prints.

The product should make the user feel:

> "This is my life. I have never seen it this way before."

The first product goal is not to improve behavior. It is to create recognition, reflection, and emotional attachment.

### Core promise

**Your wearable already captured the data. Bioloop turns it into something worth remembering.**

### MVP success condition

A user connects data and, within 60 seconds of the first meaningful render, feels enough emotion or curiosity to save, share, or print the result.

---

## 2. Strategic Positioning

### What Bioloop is

- A personal data-art studio.
- A private life archive for wearable history.
- A narrative engine for health and rhythm over time.
- A creation tool for personal biometric artifacts.
- A product that treats biometric data as memory, not just metrics.

### What Bioloop is not

- Not a daily health dashboard.
- Not a medical tool.
- Not a diagnosis or prediction engine.
- Not another AI wellness coach.
- Not a replacement for Oura, Apple Health, Garmin, Whoop, or Fitbit.
- Not a gamified habit tracker.
- Not a biohacker control panel.

### Category hypothesis

Most health apps optimize for daily utility: readiness, recovery, strain, sleep scores, activity goals.

Bioloop should optimize for life utility: reflection, memory, identity, beauty, and ownership.

---

## 3. Product Principles

### 1. The artifact is the product

The visualization is not decoration. It is the central product experience. The app exists to help the user generate, understand, personalize, export, and preserve the artifact.

### 2. Show beauty before asking for work

Do not make users configure dashboards before they understand the value. The first experience should produce a beautiful artifact as quickly as possible.

### 3. Narrative beats analytics

A sentence like "This was your longest winter recovery streak" is more powerful than a table of weekly averages.

### 4. Privacy is part of the emotion

Users must feel safe enough to let the product handle intimate biometric history. Trust is not a compliance afterthought. It is part of the brand.

### 5. Let users recognize themselves

The product should help users connect data to lived context: parenthood, training, burnout, travel, holidays, illness, recovery, new jobs, moving countries, and routines.

### 6. Avoid score addiction

Bioloop should not intensify daily self-optimization anxiety. It should reduce noise and reveal long arcs.

### 7. Make the output shareable, but private by default

Exports should be beautiful and safe. Hide raw values unless users opt in.

### 8. Build for wonder, then depth

The first reaction should be wonder. Deeper analysis can be available, but it should never overpower the emotional artifact.

---

## 4. Expected Feeling

Bioloop should feel like opening a personal museum of your own life.

### Emotional target

Users should feel:

- Awe: "I cannot believe this came from my data."
- Recognition: "That period makes sense now."
- Calm: "This is not judging me."
- Ownership: "This belongs to me."
- Curiosity: "What else can I see?"
- Pride: "I want to keep or share this."

### Emotional anti-target

Users should not feel:

- Judged.
- Diagnosed.
- Overwhelmed.
- Tricked into sharing.
- Trapped in configuration.
- Pushed to optimize every day.
- Exposed by sensitive data.
- Like they are using a spreadsheet with nicer colors.

---

## 5. UX Paradigm

Do not copy traditional health apps.

The intended UX should borrow from:

- Spotify Wrapped: emotional storytelling and annual reflection.
- Apple Photos Memories: personal recall and gentle narrative.
- Figma: creative control once the user wants to customize.
- Arc Browser: delight, polish, and spatial clarity.
- Are.na: calm curation and personal collections.
- Museum catalogues: beautiful object presentation and restraint.

### Primary navigation model

Use four major spaces:

1. **Stories** - generated narrative experiences from the user's data.
2. **Artifacts** - saved visual works and export history.
3. **Timeline** - zoomable exploration of years, months, weeks, and nights.
4. **Studio** - creation and customization of new artifacts.

Avoid a metric-first sidebar like Sleep, HRV, Readiness, Activity, Trends, Insights. Metrics are materials, not destinations.

---

## 6. First-Run Experience

### Desired flow

1. User lands on a visually powerful promise.
2. User sees an example artifact before connecting data.
3. User connects one source.
4. Bioloop imports enough data to create a first artifact.
5. The artifact appears as the hero.
6. A short narrative explains what the user is seeing.
7. User can save, personalize, share, or print.

### First-run copy direction

Good:

> "Here are 2,316 nights of your life."

> "Every ring is a day. Every season leaves a trace."

> "Your data stays yours. Your story is yours to keep."

Avoid:

> "Your average sleep score is 82."

> "Improve your readiness by 12 percent."

> "Ask AI anything about your health."

### Time-to-wow target

The product should generate a meaningful first artifact in less than 60 seconds after data access is available. If full import takes longer, progressively render partial history while the rest loads.

---

## 7. Homepage Direction

The homepage should not be a dashboard.

It should open with one dominant artifact and a short story.

Example structure:

```text
YOUR LIFE
6.4 years captured

[Large artifact]

This winter, your sleep stretched 52 minutes longer than your summer average.
Your most stable rhythm appeared during February 2024.

[Explore Story] [Create Print] [Open Studio]
```

### Homepage requirements

- One dominant visual artifact above the fold.
- One emotionally meaningful insight in plain language.
- One clear primary action.
- Minimal chrome.
- No metric cards as the main hero.
- No dense tables on the first screen.

---

## 8. Core Product Spaces

### Stories

Stories are generated narrative experiences. They should feel like short documentaries about periods of the user's life.

Example story titles:

- The Winter You Recovered
- The Month You Burned Out
- Your Strongest Year
- The Summer of Travel
- Five Years of Sleep
- The Year Your Rhythm Changed
- Life Before and After Parenthood
- The Training Block That Changed Your Recovery

Each story should include:

- A beautiful hero visual.
- A short, human-readable explanation.
- A few evidence points.
- Optional user annotations.
- Safe export/share options.

### Artifacts

Artifacts are saved visual works. They should feel like a personal gallery.

Examples:

- Life Rings
- Sleep Seasons
- Recovery Landscape
- Heartbeat River
- Year in Motion
- Circadian Map
- Training Atlas

Each artifact should have:

- Title.
- Date range.
- Data sources used.
- Privacy level.
- Export formats.
- Print status, if ordered.

### Timeline

Timeline is the exploration layer. It should feel spatial and zoomable, not like a spreadsheet.

Zoom levels:

- Lifetime / full history.
- Year.
- Season.
- Month.
- Week.
- Day / night.

The user should be able to zoom into a suspicious or beautiful region of the artifact and ask, implicitly: "What happened here?"

### Studio

Studio is where the user creates and customizes artifacts.

Studio should feel creative but not complicated. Start with templates, then expose controls progressively.

Basic creation flow:

1. Choose artifact type.
2. Choose date range.
3. Choose data source or metric set.
4. Generate draft.
5. Personalize title, palette, labels, privacy, and caption.
6. Export or print.

---

## 9. AI and Narrative Direction

AI should not be the main interface.

Avoid making the product feel like a chatbot with charts attached.

### Correct role of AI

AI should act as:

- Narrator.
- Caption assistant.
- Pattern explainer.
- Story editor.
- Annotation helper.

### Incorrect role of AI

AI should not act as:

- Doctor.
- Therapist.
- Diagnostic engine.
- Generic wellness coach.
- An always-visible chat panel.
- The product's primary navigation model.

### Narrative card pattern

Each generated statement should be supported by visible evidence.

Example:

```text
January 2024
Your longest recovery streak.

Average sleep: 8h 41m
Sleep midpoint stability: +18 percent vs baseline
Tags: vacation, sauna, family

Why we said this: 21 nights above your 12-month sleep-duration baseline.
```

### AI guardrail

Never produce medical conclusions. Prefer: "Your data shows..." or "This period appears..." Do not say: "You had depression," "You were overtrained," or "This caused your insomnia."

---

## 10. UI Direction

### Visual style

The target style is Calm Museum.

It should feel:

- Warm.
- Premium.
- Quiet.
- Editorial.
- Personal.
- Trustworthy.
- Artful.

It should not feel:

- Neon.
- Clinical.
- Biohacker-heavy.
- Finance-dashboard-like.
- Fitness-gamified.
- Corporate wellness.
- Dark-mode-only hacker aesthetic.

### Color direction

Preferred palette families:

- Bone.
- Sand.
- Warm grey.
- Deep navy.
- Forest green.
- Copper.
- Muted amber.
- Soft graphite.

Avoid:

- Aggressive red/green score colors.
- Neon gradients.
- Pure black backgrounds as the default.
- Pure white dashboard surfaces everywhere.
- Warning colors unless truly needed.

### Typography direction

Use editorial typography. Headings may feel slightly literary or museum-like. Body copy should be highly readable.

Good typography qualities:

- Calm.
- Spacious.
- High legibility.
- Strong hierarchy.
- Few sizes used well.

Avoid:

- Tiny dense analytics labels.
- Overuse of monospace.
- Startup SaaS sameness.
- Excessive badges and pills.

### Layout direction

Prefer:

- Large visual canvases.
- Generous margins.
- Slow reveal of detail.
- One primary focus per screen.
- Editorial captions near visuals.

Avoid:

- Dense dashboards.
- Many cards competing for attention.
- Table-first layouts.
- Multiple charts above the fold.
- Settings and controls visible before they are needed.

---

## 11. Motion and Interaction

Motion should feel organic and quiet.

### Good motion

- Rings grow as data imports.
- Timeline zooms smoothly from years to weeks.
- Story captions fade in like documentary subtitles.
- Hover reveals evidence without disrupting the artifact.
- Export preview appears like placing art in a frame.

### Bad motion

- Gamified confetti for health data.
- Hyperactive dashboard transitions.
- Loading spinners as the main import state.
- Distracting micro-animations on every element.
- Motion that makes the artifact feel like an ad banner.

### Loading states

Do not show a generic spinner for long imports. Show progress through the artifact itself.

Example:

```text
Growing your rings...
2019 imported
2020 imported
2021 imported
```

---

## 12. Privacy and Trust UX

Privacy is part of the product experience, not a footer link.

### Trust principles

- Explain why each permission is needed.
- Request the minimum required data for the selected artifact.
- Show which data sources were used.
- Make local/private mode obvious.
- Let the user delete imports and artifacts.
- Redact sensitive values by default in social exports.
- Never surprise the user with public sharing.

### Share defaults

Default share cards should avoid exposing:

- Exact HRV values.
- Exact resting heart rate values.
- Medical-looking labels.
- Sensitive date annotations.
- Raw sleep disruptions unless user opts in.

Better default share text:

> "Six years of sleep, visualized as Life Rings."

Not:

> "My HRV dropped 22 percent during burnout."

---

## 13. Artifact Design Requirements

An artifact must be beautiful before it is explanatory.

### Every artifact needs

- Strong visual identity.
- Clear mapping from data to form.
- Date range.
- Legend, but not too much legend.
- Optional title.
- Optional personal caption.
- Print-safe composition.
- Social-safe crop.
- Export-safe privacy settings.

### First artifact: Life Rings

Life Rings should be the flagship format.

Concept:

- One day is represented as a 24-hour circle.
- Days move from oldest in the center to most recent at the edge.
- Sleep and wake states are encoded as contrasting segments.
- Seasonal patterns should become visible naturally.
- The result should feel like tree rings, a fingerprint, and a clock at once.

Life Rings should support:

- Full history.
- One year.
- Custom date range.
- Sleep/wake view.
- Optional naps.
- Optional major life tags.
- Poster export.
- Square social export.

### Print requirement

Print should not feel like an afterthought. The digital artifact should be designed from the start as something that can become a poster, framed print, or premium physical object.

---

## 14. Content and Voice

### Voice attributes

- Reflective.
- Warm.
- Precise.
- Quietly poetic.
- Non-judgmental.
- Evidence-aware.
- Human.

### Good copy

> "Every winter left a longer blue arc."

> "This was your most regular month of sleep."

> "Your rhythm changed here. Add a memory?"

> "A quiet record of 2,316 nights."

### Bad copy

> "You failed to meet your sleep goal."

> "Your readiness optimization opportunity is 14 percent."

> "AI has detected poor lifestyle choices."

> "Unlock your peak performance now."

### Tone guardrail

Never shame. Never diagnose. Never overclaim causality. Never turn intimate data into clickbait.

---

## 15. What We Do Not Want

### Product anti-patterns

- Metric dashboard as homepage.
- Chatbot as primary interface.
- Overloaded settings panels.
- Daily streak mechanics.
- Leaderboards.
- Competitive social sharing.
- Medical interpretation without clinical basis.
- Ads or ad-tech tied to health data.
- Growth hacks that pressure users to overshare.

### UX anti-patterns

- Asking for too many permissions before showing value.
- Making users choose from dozens of chart options first.
- Using technical data labels without human explanation.
- Treating empty states as errors instead of invitations.
- Showing raw data tables before story or artifact.
- Hiding export and delete controls.

### Visual anti-patterns

- Neon cyberpunk biohacker style.
- Dense enterprise BI charts.
- Generic SaaS card grids.
- Fitness app badges and trophies.
- Red warning states for normal human variation.
- Overuse of gradients and glassmorphism.

---

## 16. Coding Agent Instructions

Coding agents should treat this document as product specification and design constitution.

### Default implementation priority

When choosing between a dashboard-style implementation and an artifact-first implementation, choose artifact-first.

When choosing between more metrics and better narrative, choose better narrative.

When choosing between more controls and faster first output, choose faster first output.

When choosing between impressive AI and trustworthy evidence, choose trustworthy evidence.

### Required product structure

Implement around these top-level spaces:

- Stories
- Artifacts
- Timeline
- Studio
- Settings / Privacy

Do not implement the main app as metric tabs unless explicitly requested later.

### Core components to create

- `ArtifactHero`: large visual-first presentation component.
- `StoryCard`: narrative card with evidence drawer.
- `TimelineZoom`: zoomable time navigation from years to days.
- `ArtifactStudio`: guided artifact creation flow.
- `PrivacyBadge`: shows local/private/share status.
- `ExportPanel`: export and print actions with privacy controls.
- `DataSourcePanel`: shows sources, sync status, and permissions.
- `MomentTagger`: lets users annotate life events.

### First-run flow components

- `WelcomePromise`
- `ExampleArtifactPreview`
- `ConnectDataSource`
- `ImportProgressRings`
- `FirstArtifactReveal`
- `FirstStoryCaption`
- `SaveSharePrintActions`

### Implementation guardrails

- Do not display dense metric cards on the first screen.
- Do not expose raw health values in share cards by default.
- Do not make AI chat the main navigation.
- Do not request unnecessary permissions.
- Do not use red/green scoring as the dominant visual system.
- Do not use gamification patterns like streaks, trophies, or leaderboards.
- Do not generate medical claims.

### Data and narrative guardrails

All generated narratives should be traceable to source data or derived metrics.

Each narrative statement should have an optional "Why we said this" drawer.

Use language like:

- "Your data shows..."
- "This period appears..."
- "Compared with your baseline..."
- "You may remember this as..."

Avoid language like:

- "This caused..."
- "You were diagnosed with..."
- "You should..."
- "Your body is telling you..."

---

## 17. MVP UX Spec

### MVP goal

Let a user import one source, generate one stunning artifact, read one meaningful story caption, and save/share/print the result.

### MVP scope

Must have:

- One import path.
- One flagship artifact: Life Rings.
- Local archive.
- First-run artifact reveal.
- Basic narrative captions.
- Evidence drawer.
- Privacy redaction for exports.
- PNG export.
- Print-ready PDF or SVG export.
- Saved artifact gallery.

Should have:

- Manual tags / moments.
- Palette selection.
- Date range selection.
- Social share crop.
- Print preview.

Not needed for MVP:

- Chatbot.
- Advanced correlations.
- Multi-wearable deduplication.
- Public community gallery.
- Marketplace.
- Complex subscriptions.
- Native mobile apps, unless required for data access.

---

## 18. Acceptance Criteria

### First-run acceptance criteria

- User understands the product promise before connecting data.
- User can connect or import data without reading developer documentation.
- User sees artifact progress during import.
- User receives a first artifact without configuring chart settings.
- User can save or export the artifact.
- User can see what data was used.
- User can delete imported data.

### Artifact acceptance criteria

- Artifact looks beautiful at full screen.
- Artifact works as a square social image.
- Artifact works as a print composition.
- Artifact has a clear date range.
- Artifact has a minimal legend.
- Artifact does not expose sensitive raw metrics by default.
- Artifact can be regenerated deterministically from the same data and settings.

### Narrative acceptance criteria

- Narrative is short and human-readable.
- Narrative avoids diagnosis and causality overclaims.
- Narrative is supported by evidence.
- User can edit or hide narrative text.
- Narrative makes the artifact easier to understand without reducing its mystery.

---

## 19. Product Decision Checklist

Before adding a feature, ask:

1. Does this help users see themselves more clearly?
2. Does this make the artifact more beautiful, meaningful, or trustworthy?
3. Does this preserve privacy by default?
4. Does this reduce or increase dashboard anxiety?
5. Does this support stories, memories, or art?
6. Could this be printed, saved, or shared safely?
7. Is this better as a narrative moment than as another chart?
8. Would this still feel premium and calm?

If the answer is mostly no, do not build it yet.

---

## 20. One-Sentence Product Brief

Bioloop is a private data-art studio that turns years of wearable history into beautiful life artifacts, reflective stories, and museum-grade memories.

## 21. One-Sentence UX Brief

Make the user emotional about their own data before asking them to analyze it.

## 22. One-Sentence Engineering Brief

Build an artifact-first, privacy-first, narrative-supported system where metrics power the experience but never dominate it.
