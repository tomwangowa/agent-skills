# Pre-Dev Review Checklist

Run every category against the spec + wireframe. For each item, produce a concrete question if the spec/wireframe is silent or ambiguous. Mark "N/A" if the category clearly does not apply to this feature.

## 1. Error States

- What happens when the API call fails (network error, 4xx, 5xx)?
- Is there a retry mechanism? How many times? What does the user see while retrying?
- What does the error message say? Who writes the copy?
- Can the user recover from the error without leaving the page?
- Are there field-level validation errors? What triggers them? What do they look like?
- What happens on timeout?

## 2. Loading States

- What does the user see while data is loading?
- Is there a skeleton screen, spinner, or shimmer? Which one?
- What if loading takes > 3 seconds? > 10 seconds?
- Are there multiple independent data sources? Do they load independently or together?
- What is the initial state before any data arrives?

## 3. Empty States

- What does the page look like with zero items / no data?
- Is there a CTA or guidance for first-time users?
- What if data was previously present but got deleted — same empty state or different?
- What if a search/filter returns zero results?

## 4. Responsive / Mobile Behavior

- How does the layout adapt at tablet and mobile breakpoints?
- Are there touch-specific interactions (swipe, long press)?
- How do hover-dependent interactions work on touch devices?
- Does the content order change on smaller screens?
- Are there components that hide/show at different breakpoints?
- Is landscape orientation considered?

## 5. Accessibility (a11y)

- What is the keyboard navigation flow (tab order)?
- Are there ARIA labels for interactive elements?
- Do color choices meet contrast requirements (WCAG AA)?
- Are there screen reader announcements for dynamic content changes?
- Can all actions be completed without a mouse?
- Are focus states defined for interactive elements?

## 6. API Contract / Data Assumptions

- What are the exact API endpoints involved?
- What does the request payload look like? What does the response look like?
- Are there pagination requirements? What page size?
- What are the rate limits?
- Is there optimistic UI update or wait-for-server confirmation?
- What is the caching strategy? When does data go stale?
- Are there race conditions (e.g., user submits twice quickly)?

## 7. Edge Cases

- What are the character limits for text inputs?
- What happens with extremely long content (names, descriptions, URLs)?
- What happens with special characters, emoji, or RTL text?
- What if the user navigates away mid-action (unsaved changes warning)?
- What if the user opens the same page in two tabs?
- What happens with concurrent edits by multiple users?
- What are the max/min values for numeric inputs?

## 8. Copy / i18n

- Who provides the final copy for labels, tooltips, and messages?
- Are there strings that need translation?
- Do translated strings fit the UI layout (German/Chinese can be 30-50% longer)?
- Are date/time/number formats locale-aware?
- Are there pluralization rules to handle?

## 9. Animation / Transition Specs

- Are there entry/exit animations for modals, drawers, or toasts?
- What are the transition durations and easing curves?
- Is there a loading-to-content transition defined?
- Are animations disabled for prefers-reduced-motion?
- Are there micro-interactions (button press, toggle, etc.)?

## 10. Data Validation

- Where does validation happen — client-side, server-side, or both?
- What are the validation rules for each input field?
- When does validation trigger — on blur, on submit, or real-time?
- Are there cross-field validations (e.g., end date > start date)?
- What does the valid vs. invalid state look like visually?
