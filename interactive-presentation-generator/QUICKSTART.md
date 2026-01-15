# Interactive Presentation Generator - Quick Start

## 🚀 Quick Start (5 minutes)

### Step 1: Set Up Style Directory (Optional)

If you want to use custom styles, set the environment variable:

```bash
export STYLE_YAML_DIR="/path/to/your/styles"
```

Or place your style YAML files in `./styles/` within the skill directory.

### Step 2: Trigger the Skill

Simply tell Claude:

```
"Create a 10-minute presentation about cloud architecture"
```

Or use the `/` command:

```
/interactive-presentation-generator
```

### Step 3: Answer the Questions

Claude will ask you:
1. **Content**: What's your presentation about?
2. **Purpose**: Conference talk? Internal meeting? Educational?
3. **Audience**: Technical? Business? General public?
4. **Duration**: 5min, 15min, 30min, 1hour?
5. **Style**: Choose from 19 professional styles
6. **Format**: reveal.js HTML (recommended), Marp, or Slidev
7. **Assets**:
   - Cover image (URL, path, or use placeholder)
   - Ending image (URL, path, or use placeholder)
   - Logo (optional)
8. **Footer**:
   - Company name
   - Author name
   - Custom text

### Step 4: Get Your Presentation

Claude will generate a complete presentation file (HTML, Markdown) ready to use!

---

## 📝 Example 1: Quick Technical Presentation

### User Input:
```
Create a 15-minute presentation about microservices architecture
for a technical audience. Use the "blueprint" style.
```

### Claude Will Generate:

**Output File:** `microservices-presentation.html`

**Content Structure:**
1. Title Slide: "Microservices Architecture"
2. Agenda Slide: Overview of topics
3. What Are Microservices? (Definition)
4. Key Principles (Independence, Scalability, Resilience)
5. Architecture Diagram (Visual)
6. Communication Patterns (REST, gRPC, Message Queues)
7. Data Management (Database per Service)
8. Deployment Strategies (Containers, Kubernetes)
9. Challenges (Distributed Systems Complexity)
10. Best Practices (Monitoring, CI/CD, API Gateway)
11. Summary
12. Q&A

**Style Applied:**
- Blueprint blue color scheme
- Technical grid background
- Monospace headings
- Engineering aesthetic

**How to Use:**
```bash
# Open in browser
open microservices-presentation.html

# Press 'F' for fullscreen
# Press 'S' for speaker view
# Press 'O' for overview
```

---

## 📝 Example 2: Business Presentation

### User Input:
```
Generate slides for a product launch presentation.
Use "swiss-clean" style. I need a cover image and company logo.

Cover image: https://example.com/product-hero.jpg
Logo: ./assets/company-logo.png
Company: Acme Corporation
```

### Claude Will Generate:

**Output File:** `product-launch-presentation.html`

**Content Structure:**
1. Title Slide: "Introducing [Product Name]"
   - Cover image background
2. The Problem (Market need)
3. Our Solution (Product overview)
4. Key Features (3-4 main features with icons)
5. How It Works (Step-by-step process)
6. Benefits (Value propositions)
7. Pricing & Plans
8. Customer Testimonials (Optional)
9. Demo/Screenshots
10. Call to Action (Try it now, Sign up)
11. Thank You + Contact Info

**Style Applied:**
- Swiss minimalist design
- Helvetica typography
- Clean grid system
- High contrast black/white
- Red accent color

**Footer:**
```
Left: Acme Corporation
Center: Product Launch 2026
Right: 2026-01-15 | 5 / 11
```

---

## 📝 Example 3: From Existing Outline

### User Input:
```
Turn this outline into an interactive presentation with ukiyo-e style:

# Japanese Garden Design Workshop

## Introduction
- History of Japanese gardens
- Principles of design

## Elements
- Rocks and stones
- Water features
- Plants and trees
- Pathways

## Creating Your Garden
- Planning
- Budget
- Maintenance

## Conclusion
```

### Claude Will Generate:

**Output File:** `japanese-garden-workshop.html`

**Content Expanded:**
1. Title Slide: "Japanese Garden Design Workshop"
   - Traditional wave pattern overlay
2. Journey Through Time (History)
   - Origins in Heian period
   - Evolution through centuries
   - Modern interpretations
3. Principles of Design
   - Asymmetry and balance
   - Borrowed scenery (shakkei)
   - Symbolism in elements
4. Rocks & Stones (Ishi)
   - Types of stones
   - Placement principles
   - Symbolic meanings
5. Water Features (Mizu)
   - Ponds and streams
   - Waterfalls
   - Dry gardens (karesansui)
6. Plants & Trees (Shokubutsu)
   - Cherry blossoms
   - Maple trees
   - Moss and ground cover
7. Pathways (Komichi)
   - Stepping stones
   - Gravel paths
   - Winding design
8. Planning Your Garden
   - Site assessment
   - Design sketch
   - Seasonal considerations
9. Budget Considerations
   - Materials cost
   - Labor vs DIY
   - Long-term investment
10. Maintenance Tips
    - Seasonal care
    - Pruning techniques
    - Water management
11. Summary: Creating Harmony
12. Thank You + Resources

**Style Applied:**
- Ukiyo-e aesthetic
- Organic patterns (seigaiha waves, sakura)
- Traditional color palette
- Japanese typography
- Natural, flowing layout

---

## 🎨 Available Styles Reference

### Technical Styles
- **blueprint**: Technical drawing, grid systems, engineering aesthetic
- **cyber-neon**: Futuristic, neon colors, digital theme

### Minimalist Styles
- **swiss-clean**: Grid-based, Helvetica, high contrast
- **blue-mono**: Monochrome blue, simple, elegant
- **japanese-minimal**: Zen aesthetics, subtle, refined

### Traditional Styles
- **ukiyo-e**: Woodblock prints, organic patterns
- **kabuki-gold**: Bold, dramatic, gold accents
- **byobu**: Folding screen aesthetic
- **japonism-flow**: Flowing Japanese aesthetics

### Editorial Styles
- **fashion-layout**: Magazine style, bold typography
- **red-editorial**: Editorial design with red accents
- **kinfolk-editorial**: Kinfolk magazine aesthetic

### Creative & Others
- **digital-pop**: Pop art, vibrant, playful
- **sports-active**: Dynamic, energetic, bold
- **stone-glass**: Material design, textures
- **oneline-chic**: Minimalist line art
- **sculpture-pop**: 3D, sculptural elements
- **neon-collage**: Avant-garde, collage style
- **premium-mockup**: Product showcase, high-end
- **digital-twin**: Futuristic, tech-forward

---

## 💡 Pro Tips

### 1. Choose the Right Style
- **Technical presentations** → blueprint, cyber-neon
- **Business presentations** → swiss-clean, premium-mockup
- **Creative presentations** → ukiyo-e, neon-collage, fashion-layout
- **Educational** → japanese-minimal, blue-mono

### 2. Optimize Content
- **5-min talk** → 5-7 slides max
- **15-min talk** → 10-15 slides
- **30-min talk** → 20-25 slides
- **1-hour talk** → 30-40 slides

### 3. Use Good Images
- High resolution (1920x1080 minimum)
- Relevant to content
- Consistent style across all images

### 4. Leverage Footer Variables
```
Company: {{COMPANY_NAME}}
Author: {{AUTHOR}}
Date: {{DATE}}
Page: {{PAGE_NUMBER}} / {{TOTAL_PAGES}}
```

### 5. Speaker Notes
- Add notes for complex topics
- Include timing reminders
- Note transition cues
- Reference data sources

---

## 🎯 Common Use Cases

### 1. Conference Talk
```
"Create a 20-minute conference talk about GraphQL best practices
for experienced developers. Use technical style with code examples."
```

### 2. Sales Pitch
```
"Generate a 10-minute sales presentation for our SaaS product.
Target audience: CTOs and VPs. Use swiss-clean style."
```

### 3. Team Training
```
"Make a 30-minute training presentation on Git workflows
for new developers. Include hands-on examples."
```

### 4. Investor Pitch
```
"Create a 15-minute investor pitch deck with financial projections.
Use premium-mockup style. Include our logo and product screenshots."
```

### 5. Educational Lecture
```
"Generate a 45-minute lecture on Renaissance art history
for university students. Use editorial style with many images."
```

### 6. Quick Team Update
```
"Create 5-minute sprint review slides with our accomplishments.
Simple format, just key points and metrics."
```

---

## 🔧 Customization After Generation

### Edit the HTML
Open the generated HTML file in any text editor:

```html
<!-- Find and modify -->
<h1>{{TITLE}}</h1>  →  <h1>Your New Title</h1>

<!-- Change colors -->
:root {
  --color-primary: #000000;  →  --color-primary: #FF5733;
}

<!-- Add a slide -->
<section>
  <h2>New Slide</h2>
  <ul>
    <li>Point 1</li>
    <li>Point 2</li>
  </ul>
</section>
```

### Export to PDF
1. Open HTML in Chrome
2. Add `?print-pdf` to URL
3. Print to PDF (Ctrl/Cmd+P)
4. Save

### Add Custom CSS
```html
<style>
  /* Your custom styles */
  .my-custom-class {
    color: red;
    font-size: 24px;
  }
</style>
```

---

## 🐛 Troubleshooting

### Issue: "Style directory not found"
**Solution:** Set `$STYLE_YAML_DIR` or place styles in `./styles/`

### Issue: Images not loading
**Solution:**
- Check file paths are correct (absolute or relative)
- Verify image URLs are accessible
- Use placeholder service as fallback

### Issue: Footer not showing
**Solution:**
- Check slide doesn't have `class="no-footer"`
- Verify footer content is not empty

### Issue: Fonts not loading
**Solution:**
- Check internet connection (Google Fonts require network)
- Use fallback fonts: `Arial, sans-serif`

---

## 📚 Next Steps

1. **Try it now**: Create your first presentation!
2. **Customize styles**: Modify YAML templates for your brand
3. **Share**: Export to PDF and share with your team
4. **Iterate**: Regenerate with different styles/formats

## 🆘 Need Help?

- Check `SKILL.md` for detailed workflow
- Review `README.md` for comprehensive documentation
- See template files in `scripts/` for structure examples

---

**Ready to create amazing presentations? Just ask Claude!** 🎉
