# Interactive Presentation Generator

Generate professional, styled interactive presentations from outlines or briefs.

## Overview

This skill creates standalone HTML presentations (reveal.js) or markdown-based presentations (Marp/Slidev) with:
- **19 professionally designed styles** from various categories
- **Customizable assets**: cover images, ending images, logos
- **Dynamic footers** with template variables
- **Full YAML style integration** for colors, fonts, and visual motifs

## Quick Start

Trigger phrases:
- "Create a presentation about [topic]"
- "Generate slides for [purpose]"
- "Make an interactive presentation with [style] style"
- "Turn this outline into a deck"

## Features

### Style System

The skill integrates with a rich collection of 19 professional styles. The style directory is configurable:
- Set `$STYLE_YAML_DIR` environment variable to point to your style directory
- Or place styles in `./styles/` within the skill directory
- Or provide path when prompted

**Categories:**
- Editorial (3): fashion-layout, red-editorial, kinfolk-editorial
- Minimalist (3): blue-mono, japanese-minimal, swiss-clean
- Technical (2): blueprint, cyber-neon
- Traditional (4): byobu, kabuki-gold, ukiyo-e, japonism-flow
- Creative, Energetic, Material, Artistic, Experimental, Avant-garde, Product, Futuristic

Each style includes:
- Color palette (7 colors: base, primary, text, background, 2 accents, highlight)
- Typography (heading and body fonts with sizes, weights, line heights)
- Visual motifs (grids, lines, patterns, decorative elements)
- Layout variations (title, content, data, summary slides)

### Asset Management

**Cover Image**: Title slide background
- User-provided (file path or URL)
- Unsplash placeholder with relevant keywords
- Style default (if specified in YAML)

**Ending Image**: Final slide background
- User-provided (file path or URL)
- Unsplash placeholder
- Style default

**Logo**: Optional branding element
- Positioned: top-right, bottom-right, or bottom-left
- Max 60px height
- Hidden on title and ending slides

### Footer System

**Template Variables:**
- `{{PAGE_NUMBER}}` - Current slide number
- `{{TOTAL_PAGES}}` - Total slides
- `{{COMPANY_NAME}}` - Company/organization
- `{{AUTHOR}}` - Presentation author
- `{{DATE}}` - Presentation date
- Custom text

**Layout Zones:**
- **Left**: Company name or event
- **Center**: Author or title
- **Right**: Date and page numbers (e.g., "2026-01-15 | 5 / 20")

**Visibility:**
- Title slide: No footer
- Content slides: Full footer
- Ending slide: No footer or simplified

## Output Formats

### Primary: reveal.js HTML (Recommended)

Standalone HTML file with:
- Full style YAML integration
- Custom CSS from color palette and typography
- Visual motifs (grids, patterns, decorative elements)
- Dynamic footer with template variables
- Background images for title and ending slides
- Speaker notes support
- Interactive features (zoom, search, overview)
- PDF export capability

**Advantages:**
- No build tools required
- Works offline
- Self-contained single file
- Full browser compatibility
- Rich interactivity

### Alternative: Marp / Slidev

Markdown-based with limited style support:
- Marp: Simple, PDF export, basic YAML styling
- Slidev: Vue-powered, live coding, advanced features

## Workflow

1. **Gather requirements**: Content, purpose, audience, duration
2. **Choose style**: Present 19 available styles with descriptions
3. **Select format**: Recommend reveal.js HTML
4. **Configure assets**: Cover, ending, logo images
5. **Set footer**: Company, author, custom text
6. **Generate content**: Develop slide plan following style layouts
7. **Apply styling**: Extract YAML and generate custom CSS
8. **Create files**: Complete HTML with all features
9. **Provide instructions**: Usage guide for the user

## Style YAML Structure

```yaml
template_metadata:
  id: "style-id"
  category: "minimalist"
  name:
    en: "English Name"
    zh_tw: "繁體中文名稱"
    ja: "日本語名"
  description:
    en: "Description in English"
  tags:
    en: ["tag1", "tag2", "tag3"]

overall_design_settings:
  color_palette:
    base: "#FAFAFA"
    primary: "#000000"
    text: "#1A1A1A"
    background: "#FFFFFF"
    accent_1: "#E63946"
    accent_2: "#CCCCCC"
    highlight: "#F1F1F1"

  typography:
    heading:
      font_family: "Helvetica Neue, sans-serif"
      font_size: "48pt"
      font_weight: 700
      line_height: 1.1
    body:
      font_family: "Helvetica Neue, sans-serif"
      font_size: "16pt"
      font_weight: 400
      line_height: 1.5

  visual_motifs:
    decorative_elements:
      - type: "grid"
        description: "8pt baseline grid"
        color: "#CCCCCC"

layout_variations:
  - type: "Title Slide"
    safe_area: {top: "96px", bottom: "64px", left: "96px", right: "96px"}
```

## Template Variables Reference

In the HTML template, these placeholders are replaced:

**Content:**
- `{{TITLE}}` - Presentation title
- `{{SUBTITLE}}` - Subtitle
- `{{AUTHOR}}` - Author name
- `{{DATE}}` - Date
- `{{COMPANY_NAME}}` - Company name
- `{{CONTACT_INFO}}` - Contact details
- `{{SLIDES_CONTENT}}` - Generated slide HTML

**Assets:**
- `{{COVER_IMAGE}}` - Cover background URL/path
- `{{ENDING_IMAGE}}` - Ending background URL/path
- `{{LOGO_HTML}}` - Logo image HTML
- `{{LOGO_POSITION}}` - CSS position (top/bottom)

**Style from YAML:**
- `{{COLOR_*}}` - Color palette values
- `{{FONT_*}}` - Font settings
- `{{TEXT_TRANSFORM}}` - Typography transform
- `{{LETTER_SPACING}}` - Letter spacing
- `{{VISUAL_MOTIFS_CSS}}` - Generated CSS for decorative elements
- `{{SAFE_AREA_*}}` - Padding from layout safe areas

## Usage Examples

### Example 1: Technical Presentation

```
User: "Create a 15-minute presentation on microservices architecture"

Assistant will:
1. Suggest "blueprint" or "cyber-neon" style
2. Generate 10-12 slides with technical content
3. Include code examples with syntax highlighting
4. Add architectural diagrams
5. Apply technical aesthetic from YAML
```

### Example 2: Business Pitch

```
User: "Make a product launch presentation with swiss-clean style"

Assistant will:
1. Load swiss-clean YAML
2. Apply minimalist aesthetic
3. Create structured, grid-based layout
4. Use Helvetica typography
5. Add company branding
```

### Example 3: Creative Showcase

```
User: "Generate slides for my design portfolio using ukiyo-e style"

Assistant will:
1. Load ukiyo-e (woodblock print) aesthetic
2. Apply organic patterns and traditional colors
3. Create artistic, asymmetric layouts
4. Integrate visual motifs from YAML
```

## File Structure

```
interactive-presentation-generator/
├── SKILL.md                          # Skill definition and instructions
├── README.md                         # This file
└── scripts/
    ├── revealjs-template.html        # Main HTML template with all features
    ├── marp-template.md              # Marp markdown template
    └── slidev-template.md            # Slidev markdown template
```

## reveal.js Keyboard Shortcuts

When presenting the generated HTML:

- **F**: Fullscreen mode
- **S**: Speaker view with notes
- **O**: Overview mode (all slides)
- **Arrow keys**: Navigate slides
- **Space**: Next slide
- **Shift+Space**: Previous slide
- **Ctrl+Shift+F**: Search
- **?**: Show all shortcuts
- **Esc**: Exit special modes

## PDF Export

1. Open HTML in Chrome/Chromium
2. Add `?print-pdf` to URL: `file:///path/slides.html?print-pdf`
3. Print to PDF (Ctrl/Cmd+P)
4. Settings: Landscape, no margins, background graphics enabled

## Customization

After generation, users can:
- Edit HTML to modify content
- Change CSS variables to adjust colors
- Replace images by updating URLs
- Modify footer content
- Add/remove slides
- Customize transitions and animations

## Technical Details

**Dependencies (all via CDN):**
- reveal.js 5.0.4+
- Plugins: notes, markdown, highlight, zoom, search
- Google Fonts (if custom fonts used)

**Browser Support:**
- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

**File Size:**
- Typical: 50-100KB (HTML only, CDN links)
- With embedded images: Varies
- Offline mode: Embed libraries (~500KB)

## Limitations

- Marp/Slidev: Limited YAML style integration compared to HTML
- Complex visual motifs may require manual CSS refinement
- Some YAML design details are simplified for web rendering
- Embedded fonts require Google Fonts availability

## Future Enhancements

Potential additions:
- Style preview thumbnails
- More visual motif implementations
- Animation presets from YAML
- Multi-language content support
- Batch generation from multiple outlines
- Export to PowerPoint/Keynote

## Support

For issues or questions:
1. Check SKILL.md for detailed workflow
2. Review template files for structure
3. Test with different styles to find best fit
4. Modify generated HTML for specific needs

## License

This skill integrates with the notebooklm-design style system.
Refer to the style YAML files for individual style licenses.
