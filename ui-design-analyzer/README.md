# UI Design Analyzer

A Claude Code Skill for analyzing UI/UX design from screenshots using Claude's native multimodal capabilities.

## Overview

**UI Design Analyzer** provides comprehensive design analysis across 6 key dimensions:

1. 🎯 **Usability & UX** - Information hierarchy, user flow, clarity
2. 🎨 **Visual Design** - Color, typography, spacing, alignment
3. ♿ **Accessibility** - WCAG compliance, contrast ratios, touch targets
4. 📏 **Consistency** - Design system compliance, patterns
5. 📱 **Responsive** - Mobile/tablet/desktop considerations
6. 💡 **Improvements** - Actionable suggestions with specific values

**Key Advantage**: Uses Claude Code's native vision capabilities - no external tools required!

## Quick Start

### No Installation Required!

This skill works out of the box with Claude Code. No dependencies, no API keys, no setup!

### Usage

Simply ask Claude to analyze your UI screenshot:

```
Analyze this UI: /path/to/screenshot.png
```

```
Review this login page design: ~/Desktop/login-mockup.png
```

```
Is this mobile interface accessible?
Screenshot: /path/to/mobile-ui.png
```

```
Compare my implementation with Figma:
Implementation: /path/to/impl.png
Design: /path/to/figma-export.png
```

That's it! Claude will:
1. 👁️ Read and analyze the screenshot
2. 📊 Evaluate across 6 dimensions
3. 📝 Generate detailed report with specific recommendations
4. 💡 Provide actionable next steps

## What It Analyzes

### 1. Usability & Information Architecture

**Checks**:
- ✅ Visual hierarchy (most important elements stand out?)
- ✅ Navigation clarity (can users find their way?)
- ✅ Content scannability (F-pattern, visual flow)
- ✅ Action affordance (buttons look clickable?)
- ✅ User flow logic (next steps obvious?)

**Example Finding**:
```
⚠️ Primary CTA button not prominent enough
- Issue: "Submit" button uses same color as secondary actions
- Impact: Users may miss the primary action
- Fix: Use accent color (#3B82F6) for primary button,
      gray (#6B7280) for secondary
```

### 2. Visual Design & Aesthetics

**Checks**:
- ✅ Color harmony (complementary, analogous, monochromatic?)
- ✅ Typography (hierarchy, readability, pairing)
- ✅ Spacing (consistent 8px grid? proper breathing room?)
- ✅ Alignment (elements properly aligned?)
- ✅ Visual balance (weight distribution)
- ✅ White space usage

**Example Finding**:
```
🎨 Typography Hierarchy Issue
- Heading: 16px (too small for h1)
- Body: 14px (below recommended 16px for readability)
- Suggestion:
  - H1: 32px (2rem)
  - H2: 24px (1.5rem)
  - Body: 16px (1rem)
  - Caption: 14px (0.875rem)
```

### 3. Accessibility (WCAG 2.1)

**Checks**:
- ✅ Color contrast ratios (text, buttons, icons)
- ✅ Touch target sizes (minimum 44x44px for mobile)
- ✅ Font sizes (minimum 16px for body text)
- ✅ Visual indicators (not relying on color alone)
- ✅ Error message visibility
- ✅ Focus states (visible indicators)

**Example Finding**:
```
🔴 Accessibility Failure: Color Contrast
- Current: #999999 text on #FFFFFF background
- Contrast ratio: 2.8:1 ❌ (fails WCAG AA 4.5:1)
- Impact: Hard to read, especially for users with low vision
- Fix: Use #5F5F5F for 4.6:1 ratio ✅
      Or use #4A4A4A for 7.1:1 ratio ✅ (WCAG AAA)
```

### 4. Design System Compliance

**Checks**:
- ✅ Using defined color tokens vs hardcoded colors?
- ✅ Spacing from design system (4, 8, 16, 24, 32px)?
- ✅ Component variants consistent?
- ✅ Icon set cohesive?

**Example Finding**:
```
⚠️ Hardcoded spacing detected
- Card padding: 14px (non-standard)
- Button padding: 10px 18px (non-standard)
- Suggestion: Use design tokens:
  - Card: p-4 (16px) or p-6 (24px)
  - Button: px-4 py-2 (16px 8px)
```

### 5. Mobile/Responsive Considerations

**Checks** (for mobile UIs):
- ✅ Single column layout for small screens?
- ✅ Touch-friendly tap targets?
- ✅ Thumb-zone optimization?
- ✅ Horizontal scroll avoided?
- ✅ Text readable without zoom?

**Example Finding**:
```
🟡 Mobile UX Issue
- Touch targets too small: 32x32px (below 44x44px minimum)
- Form inputs too close together: 8px gap (recommend 16px+)
- Suggestion: Increase button height to 44px, spacing to 16px
```

### 6. Improvement Suggestions

**Provides**:
- 🎯 Quick wins (easy, high impact)
- 🔄 Important improvements (medium effort)
- 🚀 Long-term enhancements (nice-to-have)

## Features

### 🎯 No External Dependencies

- **No external tools required** - Uses native multimodal capabilities
- **No API keys needed** - Works directly in Claude Code
- **No installation** - Ready to use immediately

### 🧠 Comprehensive Analysis

Covers all aspects of UI/UX:
- Usability (is it easy to use?)
- Aesthetics (does it look good?)
- Accessibility (can everyone use it?)
- Consistency (does it follow patterns?)
- Responsiveness (does it work on all devices?)

### ✨ Actionable Feedback

Every finding includes:
- **What's wrong**: Clear problem description
- **Why it matters**: Impact on users
- **How to fix**: Specific recommendations with values
- **Examples**: Code snippets or specific hex codes

### 🔄 Iterative Improvement

Can engage in conversation:
```
You: "Can you suggest better colors?"
Claude: [Suggests 2-3 color schemes with hex codes]

You: "I like option 2, can you show how it would look on buttons?"
Claude: [Provides CSS code and description]
```

## Examples

### Example 1: General UI Review

**Input**:
```
Analyze this dashboard: ~/Desktop/dashboard.png
```

**Output**:
```
UI Design Analysis: Dashboard

Overall Score: 7.5/10 ⭐⭐⭐⭐☆

Strengths:
✅ Clean layout with good use of white space
✅ Clear data visualization
✅ Consistent color usage

Issues Found:
🔴 Color contrast failure on secondary text (3.1:1)
🟡 Inconsistent spacing (12px, 16px, 20px mixed)
🟢 Consider larger heading sizes for better hierarchy

Top 3 Recommendations:
1. Fix text color: #999 → #5F5F5F (4.6:1 contrast)
2. Standardize spacing to 8px increments
3. Increase h2 from 18px to 24px

[Full detailed report...]
```

### Example 2: Figma Comparison

**Input**:
```
Does my implementation match Figma?
Figma: ~/figma-export.png
Implementation: ~/actual-screenshot.png
```

**Output**:
```
Design Implementation Comparison

Match Score: 82% 🎯

Deviations:
🔴 Button color: Figma #3B82F6 vs Actual #60A5FA (+25 lighter)
🟡 Spacing: Header 64px → 72px (+8px deviation)
🟢 Border radius: 8px → 6px (-2px, minor)

Perfect Matches:
✅ Typography sizes
✅ Icon placement
✅ Component proportions

[Detailed diff report...]
```

### Example 3: Color Improvement

**Input**:
```
This color scheme feels off, can you improve it?
Screenshot: ~/ui.png
```

**Output**:
```
Color Analysis & Suggestions

Current Palette:
🔴 Primary: #FF5733 (Bright red-orange)
🔵 Secondary: #3498DB (Blue)
⚪ Background: #ECF0F1 (Light gray)

Issue: Red-orange creates urgency/alarm throughout UI

Suggested Schemes:

Option 1: Professional Blue
🔵 Primary: #3B82F6
🟣 Accent: #8B5CF6
⚪ Background: #F9FAFB
⚫ Text: #111827
→ Trustworthy, modern, tech-forward

Option 2: Calm Green
🟢 Primary: #10B981
🔵 Accent: #6366F1
⚪ Background: #FFFFFF
⚫ Text: #1F2937
→ Growth, success, accessible

All options meet WCAG AAA (7:1+ contrast)

[CSS/Tailwind code provided...]
```

## Best Practices

### For Better Analysis

✅ **Good**:
```
Analyze this mobile app home screen. Target users are elderly (60+),
so readability and touch-friendliness are critical.
Screenshot: ~/elderly-app.png
```

✅ **Also Good**:
```
Quick accessibility check on this form: ~/form.png
```

❌ **Too Vague**:
```
Is this good?
```

### Provide Context

Mention:
- Target platform (web/mobile/tablet/desktop)
- Target users (age, tech-savviness)
- App purpose (e-commerce, healthcare, productivity)
- Any brand guidelines or constraints
- Specific concerns (accessibility, mobile-friendly, etc.)

## Analysis Dimensions Explained

### Dimension 1: Usability
**Question**: Can users accomplish their goals easily?

**Checks**:
- Primary action obvious?
- Information findable?
- Steps clear?
- Feedback provided?

### Dimension 2: Visual Design
**Question**: Is it aesthetically pleasing and professional?

**Checks**:
- Color harmony
- Typography pairing
- Visual balance
- Consistent spacing

### Dimension 3: Accessibility
**Question**: Can everyone use it, including users with disabilities?

**Checks**:
- WCAG AA/AAA compliance
- Color contrast
- Touch target sizes
- Screen reader friendly

### Dimension 4: Consistency
**Question**: Does it follow established patterns?

**Checks**:
- Design system usage
- Component consistency
- Pattern reuse

### Dimension 5: Responsive
**Question**: Does it adapt well to different screen sizes?

**Checks**:
- Mobile optimization
- Touch targets
- Content priority

### Dimension 6: Improvements
**Question**: How can we make it better?

**Provides**:
- Specific suggestions
- Alternative approaches
- Best practice recommendations

## Output Formats

### Format 1: Comprehensive Report (Default)
~200-300 lines covering all 6 dimensions.
**Use when**: Full design review needed.

### Format 2: Executive Summary
Top 5-10 issues with quick explanations.
**Use when**: Quick feedback needed or time-limited.

### Format 3: Focused Analysis
Deep dive on one aspect (e.g., "focus on accessibility only").
**Use when**: Specific area needs attention.

### Format 4: Side-by-Side Comparison
Before/after or design/implementation comparison.
**Use when**: Validating implementation or testing improvements.

## Real-World Use Cases

### Use Case 1: Pre-Development Design Review
**When**: Before developers start coding
**Goal**: Catch design issues early
**Analysis**: Feasibility, missing states, edge cases

### Use Case 2: Implementation Validation
**When**: After coding, before QA
**Goal**: Ensure pixel-perfect implementation
**Analysis**: Design vs implementation diff

### Use Case 3: Accessibility Audit
**When**: Before launch or compliance check
**Goal**: Meet WCAG standards
**Analysis**: Contrast, sizes, semantic structure

### Use Case 4: Design Iteration
**When**: Improving existing UI
**Goal**: Identify improvement opportunities
**Analysis**: UX issues, visual polish, modernization

### Use Case 5: Competitive Analysis
**When**: Benchmarking against competitors
**Goal**: Learn from others' designs
**Analysis**: Best practices, patterns, innovations

## Tips & Tricks

### Get More Detailed Analysis

```
Analyze this UI with emphasis on accessibility and color contrast
```

### Focus on Specific Aspect

```
Only check if this mobile UI has appropriate touch target sizes
```

### Compare Multiple Versions

```
Compare these 3 design iterations and tell me which is best:
- Version A: ~/v1.png
- Version B: ~/v2.png
- Version C: ~/v3.png
```

### Request Specific Output

```
Analyze this UI and give me CSS code to fix the color contrast issues
```

## Advantages

| Aspect | Manual Review | ui-design-analyzer |
|--------|---------------|-------------------|
| **Setup** | Designer expertise | None - works immediately |
| **Speed** | 15-30 min per screen | 1-2 minutes |
| **Consistency** | Varies by reviewer | Standardized framework |
| **Accessibility** | Often overlooked | Visual accessibility checked (WCAG contrast, sizes) |
| **Metrics** | Subjective | Estimated metrics (approximate values) |

## Typical Output

- **Analysis time**: 1-2 minutes per screenshot
- **Report length**: 150-300 lines (comprehensive)
- **Issues found**: Typically 5-15 per screen
- **Success rate**: High (based on established UX principles)

## Limitations

- Static screenshots only (not interactive prototypes)
- Color detection is approximate (verify hex codes manually)
- Cannot test actual user behavior (use usability testing for that)
- Best for web/mobile UI (less suitable for specialized UI like games, AR)
- Analysis based on general principles (may not fit every brand/context)

## Integration with Other Skills

### Complete Design-to-Code Workflow

```
1. Designer creates mockup
2. ui-design-analyzer reviews design ← Catch issues early
3. Write implementation spec (see CLAUDE.md spec guidelines)
4. Developers implement
5. ui-design-analyzer checks implementation ← Verify match
6. code-review-gemini reviews code
7. Ship with confidence!
```

## Common Questions

### Q: Can it detect specific pixel values?

**A**: Claude can detect approximate sizes and spacing. For pixel-perfect validation, measurements are estimates. Best used for:
- Identifying obvious inconsistencies
- Checking relative proportions
- Verifying general adherence to design

### Q: Can it suggest code to implement fixes?

**A**: Yes! Claude can generate:
- CSS/Tailwind classes for spacing and colors
- Hex codes for better color contrast
- Component structure suggestions
- Design token definitions

### Q: Can it analyze dark mode designs?

**A**: Absolutely! Just mention it:
```
Analyze this dark mode UI for contrast and readability
```

### Q: Can it compare before and after redesigns?

**A**: Yes! Provide both screenshots:
```
Compare these designs and tell me which UX is better:
Before: ~/before.png
After: ~/after.png
```

## Advanced Usage

### Extract Color Palette

```
Extract the color palette from this screenshot
```

Output:
```
Detected Colors:
🔵 #3B82F6 (Primary - Blue)
🟣 #8B5CF6 (Accent - Purple)
⚪ #FFFFFF (Background)
⚫ #1F2937 (Text)
```

### Generate Design Tokens

```
Analyze this UI and generate design tokens
```

Output:
```css
:root {
  /* Colors */
  --color-primary: #3B82F6;
  --color-accent: #8B5CF6;
  --color-bg: #FFFFFF;
  --color-text: #1F2937;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;

  /* Typography */
  --font-base: 16px;
  --font-lg: 20px;
  --font-xl: 24px;
}
```

### Accessibility Compliance Check

```
Check if this UI meets WCAG 2.1 AA standards
```

Output:
```
WCAG 2.1 AA Compliance Report

✅ Passed (8/10 criteria)
❌ Failed (2/10 criteria)

Failures:
1. Color Contrast (1.4.3) - Text has 3.2:1 (needs 4.5:1)
2. Target Size (2.5.5) - Buttons are 38x38px (needs 44x44px)

Action items to achieve compliance:
1. Change text color from #888 to #595959
2. Increase button padding to achieve 44x44px minimum
```

## Example Reports

### Full Analysis Report Structure

```markdown
# UI Design Analysis: [Screen Name]

**Overall Score**: 8/10 ⭐⭐⭐⭐⭐

## Executive Summary
[2-3 sentence overview]

## 1. Usability & UX
✅ Strengths: [List]
⚠️ Issues: [Prioritized list]
💡 Suggestions: [Specific recommendations]

## 2. Visual Design
[Color, typography, spacing analysis]

## 3. Accessibility
[WCAG compliance check]

## 4. Consistency
[Design system compliance]

## 5. Responsive (if applicable)
[Mobile/tablet considerations]

## 6. Recommendations Summary

### Quick Wins
1. [Easy fix, high impact]

### Important Improvements
1. [Medium effort, good impact]

### Long-term Enhancements
1. [Nice-to-have]

## Next Steps
[Action items]
```

## Related Skills

- **code-review-gemini**: Review UI implementation code

## Support

Since this skill uses Claude Code directly:
- No dependencies to troubleshoot
- No API keys to configure
- No installation required

If you need help:
- Ask Claude to explain any finding
- Request alternative suggestions
- Ask for specific code examples

---

**Happy UI Analyzing! 🎨✨**

_Powered by Claude Code's multimodal AI - See and understand your designs instantly!_
