# UI Design Analysis Report

**Screenshot**: [filename or description]
**Analysis Date**: YYYY-MM-DD
**Platform**: [Web Desktop / Mobile / Tablet / Web Mobile]
**Analyzer**: UI Design Analyzer (Claude Code Skill)

---

## Overall Assessment

**Design Quality Score**: [X]/10

**Rating**: ⭐⭐⭐⭐☆ ([X]/5 stars)

**Executive Summary**: [2-3 sentences summarizing the overall design quality, main strengths, and top concerns]

**Recommendation**: [Ready to implement / Needs minor fixes / Requires significant improvements]

---

## 1. Usability & User Experience

### ✅ Strengths

- [Positive observation with specific example]
- [Another strength]
- [More strengths...]

### ⚠️ Issues Found

1. **[Issue Title]** - Priority: [🔴 High / 🟡 Medium / 🟢 Low]
   - **Description**: [What's the problem?]
   - **Location**: [Where in the UI?]
   - **Impact**: [How does this affect users?]
   - **Recommendation**: [Specific fix with examples]

2. **[Another Issue]**
   - **Description**: [Details]
   - **Impact**: [User impact]
   - **Recommendation**: [How to fix]

### 💡 Improvement Suggestions

- [Actionable suggestion #1]
- [Actionable suggestion #2]
- [Actionable suggestion #3]

---

## 2. Visual Design & Aesthetics

### Color Scheme

**Detected Primary Colors**:
- Primary: [#HEXCODE] ([Color name])
- Secondary: [#HEXCODE] ([Color name])
- Background: [#HEXCODE] ([Color name])
- Text: [#HEXCODE] ([Color name])

**Harmony Assessment**: [Harmonious / Needs improvement]
- **Current**: [Complementary / Analogous / Monochromatic / Triadic / Discord]
- **Mood**: [Professional / Playful / Calm / Energetic / Serious]

**Issues**:
- [Color-related issue if any]

**Suggestions**:
- [Color improvement suggestion with specific hex codes]

### Typography

**Detected Hierarchy**:
- Heading (H1): [Size] ([Too large / Appropriate / Too small])
- Subheading (H2): [Size] ([Assessment])
- Body: [Size] ([Assessment])
- Caption: [Size] ([Assessment])

**Readability**: [Excellent / Good / Needs improvement / Poor]

**Issues**:
- [Typography issue if any]

**Suggestions**:
- [Typography improvement]

### Spacing & Layout

**Grid System**: [8px grid / 4px grid / Custom / Inconsistent]

**Spacing Analysis**:
- Consistent: [Yes / No]
- Detected values: [8px, 16px, 24px, etc.]
- Non-standard values: [14px, 18px, etc.]

**Alignment**: [Well-aligned / Some misalignment / Poor alignment]

**Issues**:
- [Spacing/layout issue]

**Suggestions**:
- [Spacing improvement with specific values]

---

## 3. Accessibility (WCAG 2.1)

### Overall Accessibility Score

**WCAG 2.1 Compliance**: [Pass / Partial / Fail] ([Level AA / AAA])

### Color Contrast

**Text Contrast**:
- Body text on background: [X.X:1] ([✅ Pass / ❌ Fail] WCAG AA 4.5:1)
- Heading text: [X.X:1] ([✅ Pass / ❌ Fail])
- Secondary text: [X.X:1] ([✅ Pass / ❌ Fail])

**Interactive Elements**:
- Primary button: [X.X:1] ([✅ Pass / ❌ Fail] WCAG AA 3:1 for large text)
- Links: [X.X:1] ([✅ Pass / ❌ Fail])

### Touch Target Sizes (Mobile)

- Primary button: [XXx XX px] ([✅ Pass / ❌ Fail] 44x44px minimum)
- Form inputs: [XXx XX px] ([Assessment])
- Tab navigation: [XXx XX px] ([Assessment])

### Text Readability

- **Base font size**: [XXpx] ([✅ ≥16px / ❌ <16px])
- **Line height**: [X.X] ([✅ 1.5+ / ❌ <1.5])
- **Line length**: [XX characters] ([✅ 50-75 / ⚠️ Too long/short])

### Visual Indicators

- Relying on color alone? [Yes (problematic) / No (good)]
- Error states clearly visible? [Yes / No]
- Focus indicators present? [Yes / No]

### Accessibility Issues Summary

🔴 **Critical** (Must fix for compliance):
- [Issue with WCAG reference]

🟡 **Important** (Should fix):
- [Issue]

🟢 **Recommended** (Nice to have):
- [Issue]

---

## 4. Design System Compliance

[This section applies if a design system is in use]

### Component Usage

**Standard Components**: [X used correctly / Y deviations found]

**Deviations**:
- [Component variant not in design system]
- [Hardcoded styles instead of tokens]

### Spacing System

**Compliance**: [High / Medium / Low]

**Non-standard spacing detected**:
- [14px (should be 16px)]
- [20px (should be 24px)]

### Color Tokens

**Token Usage**: [X% of colors use tokens]

**Hardcoded colors found**:
- [#3B82F6 (should use --color-primary)]
- [#888888 (should use --color-text-secondary)]

---

## 5. Mobile/Responsive Considerations

[Applicable for mobile UIs or responsive designs]

### Mobile Optimization

**Mobile-Friendly**: [Yes / Partial / No]

**Checks**:
- ✅/❌ Single column layout
- ✅/❌ Touch-friendly targets (44x44px+)
- ✅/❌ Readable text without zoom (16px+)
- ✅/❌ No horizontal scrolling
- ✅/❌ Thumb-zone optimization

### Responsive Behavior

**Concerns**:
- [Responsive issue if detected]

**Suggestions**:
- [Responsive improvement suggestion]

---

## 6. Detailed Findings by Priority

### 🔴 High Priority (Must Fix)

#### 1. [Issue Title]
- **Category**: [Accessibility / Usability / Visual Design]
- **Location**: [Where in the UI]
- **Current State**: [What's wrong now]
- **Impact**: [How this hurts users]
- **Recommendation**: [Specific fix]
- **Example**:
  ```
  Before: color: #888888; /* 2.9:1 contrast */
  After:  color: #5F5F5F; /* 4.6:1 contrast ✅ */
  ```

#### 2. [Another High Priority Issue]
[Same format]

---

### 🟡 Medium Priority (Should Fix)

#### 1. [Issue Title]
[Same format as high priority]

---

### 🟢 Low Priority (Nice to Have)

#### 1. [Issue Title]
[Same format]

---

## 7. Color Recommendations

[If user requested color improvements or issues detected]

### Current Color Palette

| Use | Hex Code | Appearance | Issues |
|-----|----------|------------|--------|
| Primary | #FF5733 | 🔴 Red-Orange | Too aggressive |
| Secondary | #3498DB | 🔵 Blue | OK |
| Background | #FFFFFF | ⚪ White | OK |
| Text | #333333 | ⚫ Dark Gray | Contrast OK |

### Suggested Color Palette Option 1: Professional Blue

| Use | Hex Code | Appearance | Benefit |
|-----|----------|------------|---------|
| Primary | #3B82F6 | 🔵 Modern Blue | Trustworthy |
| Accent | #8B5CF6 | 🟣 Purple | Modern |
| Background | #F9FAFB | ⚪ Soft Gray | Reduces eye strain |
| Text | #111827 | ⚫ Rich Black | 12.6:1 contrast ✅ |

**Mood**: Professional, trustworthy, modern
**Best for**: SaaS, B2B, productivity tools

### Suggested Color Palette Option 2: Calm Green

| Use | Hex Code | Appearance | Benefit |
|-----|----------|------------|---------|
| Primary | #10B981 | 🟢 Success Green | Positive |
| Accent | #6366F1 | 🔵 Indigo | Balance |
| Background | #FFFFFF | ⚪ Pure White | Clean |
| Text | #1F2937 | ⚫ Dark Gray | 10.5:1 contrast ✅ |

**Mood**: Growth, success, calm
**Best for**: Health, finance, productivity

---

## 8. Recommendations Summary

### Quick Wins (Easy to implement, high impact)

1. **[Recommendation]**
   - Effort: [5 minutes / 30 minutes / 1 hour]
   - Impact: [High / Medium / Low]
   - Action: [Specific steps]

2. **[Another quick win]**

### Important Improvements (Medium effort, good impact)

1. **[Recommendation]**
2. **[Recommendation]**

### Long-term Enhancements (Nice-to-have)

1. **[Recommendation]**
2. **[Recommendation]**

---

## 9. Specific Code Suggestions

[If applicable, provide CSS/Tailwind code]

### Fix Color Contrast

```css
/* Before */
.secondary-text {
  color: #888888; /* 2.9:1 - Fails WCAG */
}

/* After */
.secondary-text {
  color: #5F5F5F; /* 4.6:1 - Passes WCAG AA ✅ */
}
```

### Fix Spacing

```css
/* Before */
.card {
  padding: 14px; /* Non-standard */
}

/* After */
.card {
  padding: 16px; /* Standard 8px grid ✅ */
}
```

---

## 10. Next Steps

1. **Immediate Actions** (Fix high priority issues):
   - [ ] [Action item 1]
   - [ ] [Action item 2]

2. **Short-term** (Fix medium priority):
   - [ ] [Action item]

3. **Review & Validate**:
   - [ ] Review fixes with team
   - [ ] Test on actual devices
   - [ ] Run automated accessibility tools (axe, Pa11y)
   - [ ] Get user feedback

4. **Iterate**:
   - [ ] Implement improvements
   - [ ] Analyze again (ui-design-analyzer)
   - [ ] Repeat until score > 8/10

---

**Generated by**: UI Design Analyzer (Claude Code Skill)
**Version**: 1.0
