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
- **Marp**: Lightweight markdown with YAML frontmatter, PDF export capability (best for text-heavy slides)
- **Slidev**: Vue-powered presentations with interactive components and live coding (best for technical talks)

## Available Styles

This skill integrates with a rich collection of professionally designed styles. The style directory can be configured via:
- Environment variable: `$STYLE_YAML_DIR`
- Default location: `./styles/` (within skill directory)
- External path: Specified by user at runtime

**Default style directory structure:**
```
styles/
├── editorial/
├── minimalist/
├── technical/
├── traditional/
├── creative/
└── ...
```

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
- **Marp**: For straightforward presentations (5-15 slides) with PDF export needs
- **Slidev**: For technical presentations with code examples and live coding demos

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
background: https://picsum.photos/collection/94734566/1920x1080
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
- Color variables from YAML (with fallbacks)
- Font variables from YAML (with fallbacks)
- Safe area variables (default to `60px` if not specified)

**Critical: Provide Default Values**
- All CSS variables must have fallback values to prevent invalid CSS
- If YAML is missing a color key (e.g., `accent_2`), use sensible default (e.g., `#999999`)
- If safe area values are missing, default to `60px` for all sides
- If font family is missing, fallback to web-safe fonts (e.g., `Arial, sans-serif`)
- Example: `{{COLOR_PRIMARY}}` → if missing, use `#000000`

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
- Use short, punchy sentences (max 15 words per bullet)
- Avoid paragraphs (use 3-6 bullets per slide)
- Action-oriented titles (verbs, not nouns)
- Include transitions between major sections
- Add speaker notes for points that require >30 seconds to explain

### Technical Content
- Show code in focused snippets (max 15 lines per slide)
- Explain each code block's purpose
- Use syntax highlighting with language tags
- Consider live coding for demos (Slidev only)

## Example Prompts

- "Create a 15-minute presentation on microservices architecture"
- "Generate slides for my product launch in reveal.js"
- "Make a Marp presentation about Python best practices"
- "Turn this outline into an interactive HTML presentation"

## Style YAML Integration

### Loading Style YAML

1. **Locate style directory**:
   - Check environment variable `$STYLE_YAML_DIR`
   - If not set, use `./styles/` within skill directory
   - If not found, ask user for style directory path
2. **List available styles** by using Glob tool on `${STYLE_DIR}/**/*.yaml`
3. **Present options** grouped by category directory (editorial, minimalist, technical, etc.)
4. **Read selected YAML** using Read tool
5. **Parse YAML** and extract:
   - `template_metadata`: id, name, description, tags
   - `overall_design_settings.color_palette`: All color variables
   - `overall_design_settings.typography`: Fonts, sizes, weights, line heights
   - `overall_design_settings.visual_motifs`: Decorative elements, grids, patterns
   - `layout_variations`: Specific layouts for different slide types

### Applying Style to HTML

**CSS Variables with Fallbacks:**
```css
:root {
  --color-base: /* from color_palette.base, fallback: #FAFAFA */;
  --color-primary: /* from color_palette.primary, fallback: #000000 */;
  --color-text: /* from color_palette.text, fallback: #1A1A1A */;
  --color-background: /* from color_palette.background, fallback: #FFFFFF */;
  --color-accent-1: /* from color_palette.accent_1, fallback: #E63946 */;
  --color-accent-2: /* from color_palette.accent_2, fallback: #999999 */;
  --color-highlight: /* from color_palette.highlight, fallback: #F1F1F1 */;

  --font-heading: /* from typography.heading.font_family, fallback: Arial, sans-serif */;
  --font-body: /* from typography.body.font_family, fallback: Arial, sans-serif */;
  /* ... other typography settings with fallbacks */
}
```

**CRITICAL: Handle Missing YAML Keys**
When extracting values from YAML:
1. **Check for key existence** before accessing
2. **Provide sensible defaults** for all missing values:
   - Colors: Use neutral grays or high-contrast defaults
   - Fonts: Use web-safe font stacks
   - Sizes: Use standard values (16pt body, 40-48pt heading, 12pt footer)
   - Spacing: Use 60px as standard safe area
3. **Log warnings** (mentally note) when using fallbacks
4. **Never generate empty CSS values** (e.g., `color: ;`)

**Visual Motifs Implementation:**
- If `grid` type: Add CSS background grid pattern
- If `line` type: Add decorative borders or dividers
- If `pattern` type: Add SVG or CSS patterns as backgrounds
- Use specified colors and opacity from YAML

### Image Assets Management

**Default Image Sources:**
- Unsplash collections for placeholder images
- Use relevant keywords based on style category
- Example: Technical styles → `https://picsum.photos/1920x1080/?technology,blueprint`

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

## Error Handling

### File Operations
1. **Style YAML Loading**:
   - Check if style directory exists before globbing
   - Handle file read errors gracefully
   - Provide clear error message: "Style directory not found at [path]. Please set $STYLE_YAML_DIR or use default location."
   - If YAML parsing fails, inform user which file has syntax errors

2. **Image Assets**:
   - Validate image URLs/paths before using
   - Check file extensions: `.jpg`, `.jpeg`, `.png`, `.svg`, `.gif`, `.webp`
   - For URLs: Verify protocol is `http` or `https`
   - For file paths: Check file exists and is readable
   - **Fallback**: Use placeholder service if validation fails
   - **Error message**: "Image at [path] is invalid or inaccessible. Using placeholder instead."

3. **Template Variable Replacement**:
   - Never leave unreplaced variables (e.g., `{{UNDEFINED_VAR}}`)
   - If a required variable is missing, use sensible default or empty string
   - Log (mentally note) which variables were not provided

### User Input Validation
1. **Content Input**:
   - Check that outline/content is not empty
   - Minimum requirement: 1 slide title
   - If too vague, ask clarifying questions before generating

2. **File Paths**:
   - Validate absolute vs relative paths
   - Check for directory traversal attempts (`../`, `..\\`)
   - Normalize paths before use

3. **URLs**:
   - Validate URL format before using
   - Allow only `http`, `https`, `file` protocols
   - Reject `javascript:`, `data:`, or other potentially malicious schemes

### Generation Errors
1. **CSS Generation**:
   - Validate color hex codes (must start with `#` and be 3, 4, 6, or 8 characters)
   - Validate font family names (no special characters except hyphens, spaces, commas)
   - Ensure all CSS values have proper units (px, pt, em, rem, %)

2. **HTML Generation**:
   - Escape special HTML characters in user content (`<`, `>`, `&`, `"`, `'`)
   - Validate that generated HTML is well-formed (matching tags)
   - Check for unclosed tags or malformed attributes

## Security Considerations

### Input Sanitization
1. **XSS Prevention**:
   - **Critical**: Escape all user-provided content before injecting into HTML
   - Use HTML entity encoding for: `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`, `"` → `&quot;`, `'` → `&#39;`
   - Never allow raw `<script>` tags from user input
   - Sanitize slide titles, bullet points, speaker notes, footer text, company name, author name

2. **URL Safety**:
   - Validate all user-provided URLs
   - Reject dangerous protocols: `javascript:`, `data:`, `vbscript:`
   - Allow only: `http:`, `https:`, `file:` (for local images)
   - Example check: URL must match pattern `^(https?|file):\/\/.+`

3. **File Path Safety**:
   - Prevent directory traversal attacks
   - Reject paths containing `../` or `..\`
   - For local files, ensure paths are within expected directories
   - Never execute or eval file contents

### Content Safety
1. **Style YAML**:
   - YAML files are trusted (assumed to be from legitimate source)
   - However, validate extracted values before using:
     - Colors must be valid hex codes or CSS color names
     - Fonts must not contain executable code
     - URLs in visual motifs must be validated

2. **Generated HTML**:
   - The generated HTML is a local file, not served publicly
   - Risk of XSS is low (user would be attacking themselves)
   - However, still apply sanitization as best practice
   - Consider adding CSP (Content Security Policy) meta tag:
     ```html
     <meta http-equiv="Content-Security-Policy" content="default-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' https: data:;">
     ```

3. **Speaker Notes**:
   - Speaker notes may contain sensitive information
   - Remind user that speaker notes are visible in HTML source
   - Suggest not including passwords, API keys, or confidential data

### Dependencies
1. **CDN Integrity**:
   - Consider adding Subresource Integrity (SRI) hashes for CDN resources
   - Example: `<script src="..." integrity="sha384-..." crossorigin="anonymous"></script>`
   - This prevents tampering if CDN is compromised

2. **Google Fonts**:
   - Loading fonts from Google is generally safe
   - However, privacy-conscious users may prefer self-hosted fonts
   - Provide option to use system fonts only

## Notes

- Always ask for clarification if the outline is too vague
- Expand minimal outlines (< 3 bullet points per topic) into complete slides with 5-7 bullet points
- Suggest visual elements (charts, diagrams, images) for data-heavy or conceptual slides
- Include speaker notes for topics requiring >30 seconds to explain
- Provide both the presentation file and usage instructions
- For HTML presentations, ensure they're self-contained and work offline
- When applying YAML styles, respect the design philosophy and tone specified
- Test that all template variables are properly replaced before delivery
- Ensure generated HTML is valid and works across modern browsers
