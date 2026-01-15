---
name: interactive-presentation-generator
description: Generate interactive presentation from an outline or brief. Creates markdown-based presentations (Marp/Slidev/reveal.js) or standalone HTML presentations. Use when user asks to create slides, make a presentation, or generate a deck from an outline.
---

# Interactive Presentation Generator

Generate professional interactive presentations with customizable styles, supporting markdown or standalone HTML formats.

## Supported Formats

**Primary Format (Recommended):**
- **reveal.js HTML**: Standalone, full-featured HTML presentation with custom styling, themes, transitions, and interactive elements. Works in any browser, no build required.

**Alternative Formats:**
- **Marp**: Simple markdown with YAML frontmatter, PDF export capability
- **Slidev**: Vue-powered presentations with interactive components and live coding

## Available Styles

This skill integrates with a rich collection of professionally designed styles from:
`/Users/tom_wang/Development/tools/notebooklm-design/src/templates/yaml-templates/`

### Style Categories:
- **Editorial** (3 styles): fashion-layout, red-editorial, kinfolk-editorial
- **Minimalist** (3 styles): blue-mono, japanese-minimal, swiss-clean
- **Technical** (2 styles): blueprint, cyber-neon
- **Traditional** (4 styles): byobu, kabuki-gold, ukiyo-e, japonism-flow
- **Creative** (1 style): digital-pop
- **Energetic** (1 style): sports-active
- **Material** (1 style): stone-glass
- **Artistic** (1 style): oneline-chic
- **Experimental** (1 style): sculpture-pop
- **Avant-garde** (1 style): neon-collage
- **Product** (1 style): premium-mockup
- **Futuristic** (1 style): digital-twin

## Workflow

### Step 1: Gather Requirements

Ask the user (using AskUserQuestion if needed):
- **Content source**: Direct text, outline, or topic to develop
- **Presentation purpose**: Conference talk, internal meeting, educational, product launch, etc.
- **Target audience**: Technical, business, general public, creative professionals
- **Estimated duration**: 5min, 15min, 30min, 1hour
- **Visual assets**:
  - **Cover image**: URL, file path, or use style default
  - **Ending image**: URL, file path, or use style default
  - **Logo**: Optional, URL or file path
- **Footer settings**:
  - Company name
  - Author name
  - Custom text
  - Enable/disable footer

### Step 2: Choose Style

1. **List available styles** by reading YAML files from style directory
2. **Present style options** grouped by category, showing:
   - Style name (English, Traditional Chinese, Japanese)
   - Description
   - Tags (to help user understand the aesthetic)
   - Recommended use cases (if available)
3. **Allow user to select** or provide custom style YAML path
4. **Load style YAML** and extract design settings:
   - Color palette
   - Typography (fonts, sizes, weights)
   - Layout rules and safe areas
   - Visual motifs and decorative elements

### Step 3: Choose Output Format

**Recommend reveal.js HTML** for best results with style customization.

Alternative formats available:
- **Marp**: For simple presentations with PDF export needs
- **Slidev**: For technical presentations with live coding

If user chooses reveal.js HTML (recommended), the style YAML will be fully applied with:
- Custom CSS for colors, fonts, and layouts
- Background images for cover and ending slides
- Footer with template variables
- Decorative elements from visual motifs

### Step 4: Generate Content Structure

Develop a complete slide plan based on the selected style's layout variations:

**Title Slide** (follows style's "Title Slide" layout)
- Presentation title
- Subtitle (optional)
- Author/date
- Cover image (user-provided or style default)
- No footer (as per requirement)

**Content Slides** (follows style's "Content Slide" layout)
For each main point:
- Clear, action-oriented title
- 3-6 bullet points (or visual content)
- Speaker notes
- Full footer with variables:
  - `{{PAGE_NUMBER}}` / `{{TOTAL_PAGES}}`
  - `{{COMPANY_NAME}}`
  - `{{AUTHOR}}`
  - `{{DATE}}`
  - Custom text

**Special Slides**
- Agenda/Overview (for longer presentations)
- Section dividers (follows style guidelines)
- Data slides (follows style's "Data Slide" layout if available)
- Summary/Key Takeaways (follows style's "Summary Slide" layout)
- Q&A/Contact slide (ending image, no footer or simplified)

**Ending Slide**
- Thank you message or final CTA
- Contact information
- Ending image (user-provided or style default)
- No footer or simplified version

### Step 5: Generate Files

Based on the chosen format, create:

#### For Marp:
```markdown
---
marp: true
theme: default
paginate: true
---

# Title
Subtitle

---

## Slide Title
- Point 1
- Point 2
```

#### For Slidev:
```markdown
---
theme: default
background: https://source.unsplash.com/collection/94734566/1920x1080
class: text-center
highlighter: shiki
---

# Title
Subtitle

---

## Slide Title
Content here
```

#### For reveal.js Markdown:
```markdown
# Title
Subtitle

---

## Slide Title
- Point 1
- Point 2

---
```

#### For reveal.js HTML (Primary Format):

Create a complete standalone HTML file with custom styling from YAML:

**1. HTML Head with Custom Styling:**
- Load reveal.js v5.0.4+ from CDN
- Extract and apply colors from `color_palette` in YAML
- Extract and apply typography from YAML (font families, sizes, weights)
- Add decorative elements from `visual_motifs` (grids, lines, patterns)
- Implement footer styling with template variables

**2. Slide Structure:**
- **Title slide**: `class="no-footer"`, background image, follows "Title Slide" layout from YAML
- **Content slides**: Full footer, follows "Content Slide" layout from YAML
- **Data slides**: If applicable, follows "Data Slide" layout from YAML
- **Summary slide**: Follows "Summary Slide" layout from YAML
- **Ending slide**: `class="no-footer"`, ending background image

**3. Footer Implementation:**
- Fixed position footer with three zones: left, center, right
- Template variables replaced: `{{COMPANY_NAME}}`, `{{AUTHOR}}`, `{{DATE}}`, `{{PAGE_NUMBER}}`, `{{TOTAL_PAGES}}`
- Hidden on title and ending slides via CSS class `.no-footer`
- Styled according to YAML or sensible defaults

**4. JavaScript Configuration:**
- Initialize reveal.js with plugins (notes, highlight, zoom, search)
- Custom slidechanged event to update page numbers in footer
- Respect safe areas from YAML layout variations

**Template Variables to Replace:**
- `{{TITLE}}`, `{{SUBTITLE}}`, `{{AUTHOR}}`, `{{DATE}}`
- `{{COMPANY_NAME}}`, `{{CONTACT_INFO}}`
- `{{COVER_IMAGE}}`, `{{ENDING_IMAGE}}`
- Color variables from YAML
- Font variables from YAML

### Step 6: Add Enhancements

Based on content type and style YAML, include:

**Code Examples** (if technical content)
- Syntax highlighting using reveal.js highlight plugin
- Line numbers
- Line highlighting for emphasis
- Use monospace fonts from YAML or defaults

**Visual Elements**
- Images (user-provided or Unsplash placeholders)
- Charts following style's color palette
- Diagrams respecting visual motifs from YAML
- Tables styled with YAML colors

**Interactive Features** (HTML only)
- Fragment animations (reveal items one by one)
- Vertical slides for detailed breakdowns
- Speaker notes for all major slides
- PDF export capability via print

**Styling from YAML**
- Apply decorative elements from `visual_motifs`
- Implement grid systems if specified
- Add patterns, lines, or other decorative elements
- Respect safe areas and content zones
- Follow spacing philosophy and alignment principles

### Step 7: Provide Instructions

Include a brief guide at the end of generation:

**For reveal.js HTML:**
- **Open**: Double-click the HTML file or open in any modern browser
- **Present**: Press 'F' for fullscreen, 'S' for speaker view with notes
- **Navigate**: Arrow keys, space bar, or on-screen controls
- **Overview**: Press 'O' to see all slides at once
- **Search**: Press Ctrl+Shift+F to search in slides
- **Export to PDF**:
  1. Open in Chrome/Chromium
  2. Add `?print-pdf` to the URL (e.g., `file:///path/slides.html?print-pdf`)
  3. Print to PDF (Ctrl/Cmd+P)
- **Customize**: Edit the HTML file to modify content, colors, or layout
- **Keyboard shortcuts**: Press '?' to see all available shortcuts

**For Alternative Formats:**
- Marp: `npx @marp-team/marp-cli@latest --preview slides.md` (preview), export to PDF/HTML
- Slidev: `npx slidev slides.md` (dev server), `npx slidev build` (production build)

## Content Guidelines

### Slide Design Principles
- **One idea per slide**: Don't overcrowd
- **Visual hierarchy**: Title → key point → details
- **Consistent style**: Same fonts, colors, spacing
- **Readable text**: Minimum 24pt font size
- **High contrast**: Dark text on light background or vice versa

### Writing Guidelines
- Use short, punchy sentences
- Avoid paragraphs (use bullets)
- Action-oriented titles (verbs, not nouns)
- Include transitions between major sections
- Add speaker notes for complex points

### Technical Content
- Show code in small, focused snippets
- Explain each code block's purpose
- Use syntax highlighting
- Consider live coding for demos (Slidev)

## Example Prompts

- "Create a 15-minute presentation on microservices architecture"
- "Generate slides for my product launch in reveal.js"
- "Make a Marp presentation about Python best practices"
- "Turn this outline into an interactive HTML presentation"

## Style YAML Integration

### Loading Style YAML

1. **List available styles** by using Glob tool on `/Users/tom_wang/Development/tools/notebooklm-design/src/templates/yaml-templates/**/*.yaml`
2. **Present options** grouped by category directory (editorial, minimalist, technical, etc.)
3. **Read selected YAML** using Read tool
4. **Parse YAML** and extract:
   - `template_metadata`: id, name, description, tags
   - `overall_design_settings.color_palette`: All color variables
   - `overall_design_settings.typography`: Fonts, sizes, weights, line heights
   - `overall_design_settings.visual_motifs`: Decorative elements, grids, patterns
   - `layout_variations`: Specific layouts for different slide types

### Applying Style to HTML

**CSS Variables:**
```css
:root {
  --color-base: /* from color_palette.base */;
  --color-primary: /* from color_palette.primary */;
  /* ... all other colors */

  --font-heading: /* from typography.heading.font_family */;
  --font-body: /* from typography.body.font_family */;
  /* ... other typography settings */
}
```

**Visual Motifs Implementation:**
- If `grid` type: Add CSS background grid pattern
- If `line` type: Add decorative borders or dividers
- If `pattern` type: Add SVG or CSS patterns as backgrounds
- Use specified colors and opacity from YAML

### Image Assets Management

**Default Image Sources:**
- Unsplash collections for placeholder images
- Use relevant keywords based on style category
- Example: Technical styles → `https://source.unsplash.com/1920x1080/?technology,blueprint`

**User-Provided Images:**
- Accept file paths (relative or absolute)
- Accept URLs (http/https)
- Validate image format (jpg, png, svg, gif)
- Apply as `data-background-image` in reveal.js

**Logo Placement:**
- Position based on user preference or style defaults
- Common positions: top-right, bottom-right, bottom-left
- Size constraints: max 100px height for balance

## Footer Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PAGE_NUMBER}}` | Current slide number | 5 |
| `{{TOTAL_PAGES}}` | Total number of slides | 20 |
| `{{COMPANY_NAME}}` | Company or organization name | Acme Corp |
| `{{AUTHOR}}` | Presentation author | John Doe |
| `{{DATE}}` | Presentation date | 2026-01-15 |
| Custom text | Any user-provided text | Confidential |

**Footer Layout Zones:**
- **Left**: Typically company name or event name
- **Center**: Author or presentation title
- **Right**: Date and page numbers

## Style Preview (Optional Feature)

When presenting style options, include:
- Style name in all supported languages
- Description highlighting key characteristics
- Tags showing aesthetic keywords
- Recommended use cases (if available in YAML)
- Example: "Blueprint - Technical drawing aesthetic with grid systems. Recommended for: engineering presentations, technical documentation."

This helps users make informed decisions without needing full previews.

## Notes

- Always ask for clarification if the outline is too vague
- Expand sparse outlines into complete slides with reasonable content
- Suggest visual elements and diagrams where appropriate
- Include speaker notes for complex topics
- Provide both the presentation file and usage instructions
- For HTML presentations, ensure they're self-contained and work offline
- When applying YAML styles, respect the design philosophy and tone specified
- Test that all template variables are properly replaced before delivery
- Ensure generated HTML is valid and works across modern browsers
