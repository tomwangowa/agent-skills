---
name: ui-design-analyzer
description: Analyze UI/UX design from screenshots. Use this Skill when the user asks to analyze UI design, review interface screenshots, check design quality, evaluate user experience, or get design improvement suggestions.
---

# UI Design Analyzer

## Purpose

This Skill performs comprehensive UI/UX analysis on interface screenshots by:
1. Using Claude's multimodal capabilities to analyze UI screenshots
2. Evaluating design across multiple dimensions (usability, accessibility, aesthetics, consistency)
3. Providing actionable improvement suggestions with specific recommendations
4. Generating structured analysis reports

The Skill helps designers and developers improve UI quality, catch UX issues early, and ensure accessibility compliance.

---

## Instructions

When the user requests UI design analysis (for example: "analyze this UI", "review this screenshot", "is this design good", "check this interface", "improve this UI"), follow these steps strictly.

### Step 1: Receive and read the screenshot

The user will provide a screenshot in one of these ways:
- **Direct path**: "Analyze /path/to/screenshot.png"
- **Attached in conversation**: User uploads image
- **Multiple screenshots**: For before/after comparison or multi-screen analysis

Use the **Read tool** (read_file) to load and view the screenshot(s). Claude Code's multimodal capabilities will allow you to see and analyze the visual content.

**Important**: If the platform (Mobile/Desktop/Tablet) or screen context is not obvious from the screenshot, ask the user to clarify to ensure accurate sizing and interaction recommendations.

### Step 2: Perform comprehensive UI/UX analysis

Analyze the screenshot across these dimensions:

#### 1. **Usability & Information Architecture**
- Is the information hierarchy clear?
- Are primary actions easily identifiable?
- Is the navigation intuitive?
- Is the content scannable?
- Are labels and instructions clear?
- Is the user flow logical?

#### 2. **Visual Design & Aesthetics**
- Is the visual hierarchy effective?
- Is the color scheme harmonious?
- Is the typography readable and appropriate?
- Is spacing consistent (8px/16px grid)?
- Are design elements aligned properly?
- Is there visual balance?

#### 3. **Accessibility (WCAG)**
- Color contrast ratio (AA: 4.5:1 for text, AAA: 7:1)
- Touch target sizes (24x24px minimum for WCAG AA; 44x44px recommended for best practice/AAA)
- Text readability (font size minimum 16px, line height 1.5+)
- Visual affordances (buttons look clickable)
- Error states visibility
- Focus indicators

#### 4. **Consistency & Design System**
- Are components consistent with design system?
- Is spacing systematic?
- Are colors from defined palette?
- Is typography consistent?
- Are icons and illustrations cohesive?

#### 5. **Mobile/Responsive Considerations** (if applicable)
- Is content prioritized for small screens?
- Are touch targets appropriately sized?
- Is text readable without zooming?
- Is horizontal scrolling avoided?

#### 6. **Specific Analysis** (based on user's question)
If user asked specific questions like:
- "Is this reasonable?" → Focus on usability and user flow
- "Does this match the Figma design?" → Compare with provided Figma reference
- "Are the colors comfortable?" → Deep dive into color harmony and contrast

### Step 3: Generate structured analysis report

Create a comprehensive but concise report with:

```markdown
# UI Design Analysis Report

**Screenshot**: [filename]
**Analysis Date**: [date]
**Analyzer**: UI Design Analyzer (Claude Code Skill)

---

## Overall Assessment

**Design Quality Score**: [X]/10
**Overall Rating**: ⭐⭐⭐⭐☆ (4/5)

**Summary**: [2-3 sentence executive summary]

---

## 1. Usability & UX

### ✅ Strengths
- [Specific positive observations]

### ⚠️ Issues Found
1. **[Issue Title]** - [Priority: High/Medium/Low]
   - Description: [What's the problem]
   - Impact: [How this affects users]
   - Recommendation: [Specific fix]

### 💡 Suggestions
- [Actionable improvement suggestions]

---

## 2. Visual Design

### Color Scheme
- **Primary Color**: [Detected color, e.g., Blue (#3B82F6)]
- **Harmony**: [Harmonious / Needs improvement]
- **Contrast**: [Analysis]

### Typography
- **Hierarchy**: [Clear / Needs improvement]
- **Readability**: [Good / Issues detected]
- **Sizes**: [Detected font sizes]

### Spacing & Layout
- **Consistency**: [Consistent / Inconsistent]
- **Grid**: [Follows 8px grid / Custom spacing]
- **Alignment**: [Well-aligned / Issues detected]

---

## 3. Accessibility (WCAG)

### Color Contrast
- **Text on Background**: [Ratio] ([Pass/Fail] WCAG AA)
- **Interactive Elements**: [Ratio] ([Pass/Fail])

### Touch Targets (Mobile)
- **Button Sizes**: [Size] ([Pass/Fail] 44x44px minimum)

### Readability
- **Font Size**: [Size] ([Pass/Fail] 16px minimum for body)
- **Line Height**: [Ratio]

**Overall Accessibility**: [Pass/Fail] WCAG 2.1 AA

---

## 4. Design System Compliance

[If applicable, check against design system]

### Issues
- [Hardcoded values instead of tokens]
- [Inconsistent spacing]
- [Non-standard colors]

---

## 5. Detailed Findings by Priority

### 🔴 High Priority (Must Fix)
1. **[Issue]**
   - Location: [Where in the UI]
   - Problem: [Detailed description]
   - Fix: [Specific recommendation with examples]

### 🟡 Medium Priority (Should Fix)
[Similar format]

### 🟢 Low Priority (Nice to Have)
[Similar format]

---

## 6. Color Palette Analysis

**Detected Colors**:
- Primary: [#HEXCODE]
- Secondary: [#HEXCODE]
- Background: [#HEXCODE]
- Text: [#HEXCODE]

**Harmony Assessment**: [Complementary/Analogous/Monochromatic/Needs work]

**Suggestions for Better Harmony**:
- Option 1: [Color scheme with hex codes]
- Option 2: [Alternative scheme]

---

## 7. Recommendations Summary

### Quick Wins (Easy to implement, high impact)
1. [Recommendation]
2. [Recommendation]

### Important Improvements
1. [Recommendation]
2. [Recommendation]

### Long-term Enhancements
1. [Recommendation]

---

## 8. Before & After Suggestion

[If suggesting changes, describe or mock up what improvements would look like]

Example:
**Current**: Button uses #888888 on #FFFFFF (contrast 2.9:1) ❌
**Suggested**: Button uses #5F5F5F on #FFFFFF (contrast 4.6:1) ✅

---

## Next Steps

1. Address high priority issues first
2. Review with team/stakeholders
3. Implement changes iteratively
4. Test on actual devices (if mobile UI)
5. Run accessibility audit tools for verification

---

**Analysis powered by**: Claude Code (Multimodal AI)
```

### Step 4: Generate actionable design files (optional)

If user requests, you can:
- Generate CSS/Tailwind code for suggested improvements
- Create color palette definitions
- Provide specific spacing values
- Generate accessibility-compliant alternatives

### Step 5: Offer follow-up analysis

After presenting the report, offer:
- **Compare with another screenshot**: "Want to compare with a different version?"
- **Deep dive on specific aspect**: "Want me to focus on color scheme specifically?"
- **Generate improvement mockup**: "Want me to describe what the improved version would look like?"
- **Save report**: "Should I save this analysis report to a file?"

---

## Quality Standards

Your analysis must be:

### Specific and Measurable
- ❌ "Color is not good"
- ✅ "Primary button color has contrast ratio 3.2:1 (approximate), below WCAG AA standard (4.5:1). Suggest using #5F5F5F for 4.6:1 ratio."

**Important**: Always label hex codes, pixel values, and contrast ratios extracted from screenshots as "approximate" or "estimated", as vision-based detection may have slight inaccuracies. Recommend manual verification using browser DevTools or design tools for critical accessibility compliance or pixel-perfect implementation.

**Example**:
- ✅ "Button appears to be approximately 38x38px (below recommended 44x44px)"
- ✅ "Estimated color: #888888 (approximately 2.9:1 contrast - verify with DevTools)"
- ❌ "Button is exactly 38x38px" (too definitive without measurement tools)

### Actionable
- ❌ "Improve spacing"
- ✅ "Increase padding from 8px to 16px to match standard touch target size of 44x44px"

### Balanced
- Highlight both strengths and weaknesses
- Don't only criticize - recognize what's done well
- Prioritize issues by severity and impact

### Context-Aware
- Consider the platform (web/mobile/desktop)
- Consider the app type (dashboard/consumer app/tool)
- Consider cultural context if visible
- Consider brand identity if known

---

## Analysis Frameworks to Apply

### Nielsen's Usability Heuristics
1. Visibility of system status
2. Match between system and real world
3. User control and freedom
4. Consistency and standards
5. Error prevention
6. Recognition rather than recall
7. Flexibility and efficiency of use
8. Aesthetic and minimalist design
9. Help users recognize, diagnose, and recover from errors
10. Help and documentation

### Gestalt Principles
- Proximity (grouping related items)
- Similarity (consistent styling)
- Continuity (visual flow)
- Closure (complete forms)
- Figure-ground (clear focal points)

### WCAG 2.1 Criteria
- Perceivable
- Operable
- Understandable
- Robust

---

## Example Interactions

### Example 1: General UI Review

**User:**
> Analyze this login page screenshot: /path/to/login.png

**Your Actions:**
1. Read the image using Read tool
2. Analyze all aspects (usability, visual design, accessibility, etc.)
3. Generate comprehensive report
4. Highlight 2-3 most critical issues
5. Provide specific recommendations with examples

**Your Response:**
```
UI Design Analysis Complete! 📊

**Overall Assessment**: 7/10 - Good foundation with some improvements needed

**Key Findings**:
🔴 High Priority:
- Password field lacks "show/hide" toggle (UX issue)
- "Forgot password" link has poor contrast ratio (2.8:1 vs required 4.5:1)

🟡 Medium Priority:
- Form width too narrow on desktop (280px vs recommended 320-400px)
- Missing error message placeholder space (will cause layout shift)

✅ Strengths:
- Clear visual hierarchy
- Good use of whitespace
- Brand colors applied consistently

Full report saved to: ui-analysis-reports/login-page-analysis.md

Would you like me to suggest specific color codes or spacing values to fix these issues?
```

---

### Example 2: Mobile UI vs Figma Design

**User:**
> Compare this mobile screenshot with the Figma design. Does my implementation match?
> Implementation: /path/to/mobile-impl.png
> Figma export: /path/to/figma-design.png

**Your Actions:**
1. Read both images
2. Compare side-by-side:
   - Element placement
   - Spacing (margins, padding)
   - Colors
   - Typography
   - Component sizes
3. Generate diff report

**Your Response:**
```
Design Implementation Comparison 🔍

**Match Score**: 85% - Good match with minor deviations

### Deviations Found:

🔴 Color Mismatch:
- Primary button: Figma #3B82F6 vs Implementation #60A5FA (lighter)
- Recommendation: Update to exact hex code

🟡 Spacing Differences:
- Header height: Figma 64px vs Implementation 72px (+8px)
- Card padding: Figma 16px vs Implementation 12px (-4px)
- Recommendation: Use Figma values or update design spec

🟢 Matches:
✅ Typography sizes correct
✅ Icon placement accurate
✅ Border radius (8px) matches

Would you like me to generate the CSS corrections?
```

---

### Example 3: Color Improvement Request

**User:**
> The colors in this dashboard feel off. Can you suggest better colors?
> Screenshot: /path/to/dashboard.png

**Your Actions:**
1. Read the screenshot
2. Extract current color palette
3. Analyze color harmony
4. Check accessibility
5. Suggest improved color schemes

**Your Response:**
```
Color Scheme Analysis 🎨

**Current Palette**:
- Primary: #FF6B6B (Red-ish)
- Secondary: #4ECDC4 (Teal)
- Background: #F7F7F7 (Light gray)
- Text: #333333 (Dark gray)

**Issues**:
⚠️ Primary color (red) creates sense of urgency/error throughout UI
⚠️ Teal + Red combination can be harsh
⚠️ Text contrast could be stronger (4.2:1 vs ideal 7:1)

**Suggested Improvement Option 1: Professional Blue Scheme**
- Primary: #3B82F6 (Modern blue)
- Secondary: #8B5CF6 (Purple accent)
- Background: #FFFFFF (Pure white)
- Text: #1F2937 (Almost black - 12.6:1 contrast)

**Suggested Improvement Option 2: Calm Green Scheme**
- Primary: #10B981 (Success green)
- Secondary: #6366F1 (Indigo)
- Background: #F9FAFB (Soft gray)
- Text: #111827 (Rich black)

All suggestions meet WCAG AAA standards (7:1 contrast).

Would you like me to generate Tailwind/CSS code for these color schemes?
```

---

## Constraints

- Works best with clear, high-resolution screenshots
- Can analyze static UI only (not interactive prototypes)
- Color detection is approximate (may need manual verification)
- Best for web and mobile interfaces
- Analysis is based on common design principles and best practices

---

## Edge Cases

### Screenshot Quality Issues
**User uploads blurry or low-res image**

**Your Action:**
- Note in report: "Screenshot resolution is low, some details may not be accurate"
- Provide general feedback based on visible elements
- Suggest uploading higher resolution for detailed analysis

### Multiple Screens
**User provides 3-4 screenshots**

**Your Action:**
- Analyze each screen individually
- Look for consistency across screens
- Highlight inconsistencies (different spacing, colors, patterns)
- Generate comparative report

### Non-UI Screenshots
**User uploads code screenshot or diagram**

**Your Action:**
- Politely clarify: "This appears to be [code/diagram], not a UI screenshot. ui-design-analyzer is optimized for interface design analysis. Would you like me to analyze this differently?"

### No Screenshot Provided
**User asks to analyze UI without providing image**

**Your Action:**
- Ask: "Please provide a screenshot of the UI you'd like me to analyze. You can either provide a file path or attach an image."

---

## Best Practices

### For Users

**Provide Context**:
```
Analyze this login page. It's for a healthcare app, target users are
doctors aged 40-60. Design should be professional and trustworthy.
```

**Specify Focus Area** (optional):
```
Analyze this dashboard and focus on whether the data visualization
is clear and the color scheme is accessible for colorblind users.
```

**Provide Comparison** (for implementation checks):
```
Compare this implementation screenshot with the Figma design.
Implementation: /path/to/impl.png
Figma: /path/to/design.png
```

### For Comprehensive Analysis

- Provide high-resolution screenshots (at least 1280px width)
- Include full screen context (not just cropped components)
- Mention target platform (web desktop/mobile/tablet)
- Specify user demographics if relevant
- Note any brand guidelines to follow

---

## Common Use Cases

### Use Case 1: Pre-Implementation Design Review
```
User: "Review this Figma mockup before we start coding"

You: Analyze the design for:
- Implementation feasibility
- Potential technical challenges
- Missing states (loading, empty, error)
- Responsive behavior concerns
```

### Use Case 2: Implementation Validation
```
User: "Does my implementation match the design?"

You: Compare screenshots, highlight:
- Spacing differences
- Color deviations
- Missing elements
- Alignment issues
```

### Use Case 3: UX Audit
```
User: "Is this user flow intuitive?"

You: Evaluate:
- User journey clarity
- Information scent
- Cognitive load
- Error prevention
- Feedback mechanisms
```

### Use Case 4: Accessibility Check
```
User: "Is this accessible?"

You: Check:
- Color contrast (WCAG AA/AAA)
- Text sizes
- Touch target sizes
- Visual hierarchy for screen readers
- Alternative text indicators
```

### Use Case 5: Design Improvement
```
User: "How can I make this better?"

You: Provide:
- Specific design suggestions
- Alternative layouts
- Color scheme options
- Typography improvements
- Spacing adjustments
```

---

## Output Format Options

### Option 1: Full Report (Default)
Complete analysis across all 6 dimensions with detailed findings.
**Use when**: User wants comprehensive review.

### Option 2: Quick Summary
Executive summary with top 3-5 issues only.
**Use when**: User asks for "quick feedback" or "just the important issues".

### Option 3: Focused Analysis
Deep dive on one specific aspect (colors, spacing, accessibility).
**Use when**: User specifies focus area.

### Option 4: Comparison Report
Side-by-side analysis of design vs implementation or before vs after.
**Use when**: User provides multiple screenshots for comparison.

---

## Integration with Other Skills

### With spec-generator
```
1. Generate feature spec (spec-generator)
2. Designer creates mockup
3. Analyze mockup (ui-design-analyzer) ← Catch issues before coding
4. Implement based on spec and feedback
```

### With code-review-gemini
```
1. Implement UI
2. Analyze screenshot (ui-design-analyzer) ← Visual check
3. Review code (code-review-gemini) ← Code quality check
4. Ensure both visual and code quality
```

---

## Advanced Features

### Color Palette Extraction
If user asks "What colors are used?", extract and present:
```
Detected Color Palette:
🔵 Primary: #3B82F6 (Blue)
🟣 Accent: #8B5CF6 (Purple)
⚪ Background: #FFFFFF (White)
⚫ Text: #1F2937 (Dark Gray)
🟡 Warning: #F59E0B (Amber)
🔴 Error: #EF4444 (Red)
```

### Design Token Suggestions
Suggest design tokens for detected values:
```css
/* Suggested Design Tokens */
--color-primary: #3B82F6;
--color-accent: #8B5CF6;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--radius-md: 8px;
--font-base: 16px;
--font-lg: 20px;
```

### Responsive Suggestions
If analyzing mobile UI, suggest responsive breakpoints:
```
Recommendations for responsive design:
- Mobile (< 640px): Stack elements vertically
- Tablet (640-1024px): 2-column grid
- Desktop (> 1024px): 3-column grid
```

---

## Related Skills

- **spec-generator**: Generate specs for UI features
- **spec-review-assistant**: Review UI feature specifications
- **code-review-gemini**: Review UI implementation code

**Recommended Workflow**:
1. Design → **ui-design-analyzer** (this skill)
2. Implement → code-review-gemini
3. Visual check → **ui-design-analyzer** again
4. Ship with confidence

---

## Important Notes

- You (Claude Code) are analyzing the screenshot directly using your vision capabilities
- Focus on actionable, specific feedback
- Balance critique with recognition of good design choices
- Consider real-world constraints (browser compatibility, development time)
- Always respect user's design intent and brand identity
- If unsure about something, note it as "To verify: [question]"

---

## Sample Analysis Flow

When you receive a screenshot:

1. **First impression** (5 seconds scan)
   - What's the purpose of this UI?
   - Who's the target user?
   - What's the primary action?

2. **Systematic review** (scan each dimension)
   - Check usability issues
   - Check visual design
   - Check accessibility
   - Check consistency

3. **Prioritize findings**
   - What breaks functionality? (High)
   - What hurts UX significantly? (Medium)
   - What's polish/nice-to-have? (Low)

4. **Provide specific fixes**
   - Don't just point out problems
   - Suggest concrete solutions
   - Provide examples or alternatives

5. **Summarize action items**
   - Quick wins
   - Important improvements
   - Long-term enhancements
