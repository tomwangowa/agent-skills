---
theme: default
background: https://source.unsplash.com/collection/94734566/1920x1080
class: text-center
highlighter: shiki
lineNumbers: false
info: |
  ## {{TITLE}}
  {{DESCRIPTION}}
drawings:
  persist: false
transition: slide-left
title: {{TITLE}}
mdc: true
---

# {{TITLE}}

{{SUBTITLE}}

<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-2 py-1 rounded cursor-pointer" hover="bg-white bg-opacity-10">
    Press Space for next page <carbon:arrow-right class="inline"/>
  </span>
</div>

<div class="abs-br m-6 flex gap-2">
  <button @click="$slidev.nav.openInEditor()" title="Open in Editor" class="text-xl slidev-icon-btn opacity-50 !border-none !hover:text-white">
    <carbon:edit />
  </button>
  <a href="https://github.com/{{GITHUB_USERNAME}}" target="_blank" alt="GitHub"
    class="text-xl slidev-icon-btn opacity-50 !border-none !hover:text-white">
    <carbon-logo-github />
  </a>
</div>

<!--
Speaker notes go here
-->

---
transition: fade-out
---

# Agenda

<Toc minDepth="1" maxDepth="1"></Toc>

---
layout: default
---

# {{SECTION_TITLE}}

Key points:

- 📝 **Point 1** - Description
- 🎨 **Point 2** - Description
- 🧑‍💻 **Point 3** - Description
- 🤹 **Point 4** - Description
- 🎥 **Point 5** - Description

<br>
<br>

Read more about [Topic](https://example.com)

<!--
Speaker notes for this slide
-->

---
layout: two-cols
---

# Left Column

Content for the left side

- Item 1
- Item 2
- Item 3

::right::

# Right Column

Content for the right side

```javascript
// Code example
const greeting = 'Hello World';
console.log(greeting);
```

---
layout: center
class: text-center
---

# Code Examples

---

# TypeScript Example

```ts {all|2|3-5|all}
interface User {
  id: number
  name: string
  email: string
}

function greet(user: User) {
  console.log(`Hello, ${user.name}!`)
}
```

<arrow v-click="3" x1="400" y1="420" x2="230" y2="330" color="#564" width="3" arrowSize="1" />

[^1]: Line highlighting example

<!--
This demonstrates line-by-line code highlighting
-->

---
layout: image-right
image: https://source.unsplash.com/collection/94734566/1920x1080
---

# Image Background

- Point with background image
- Another point
- Final point

---
layout: center
class: text-center
---

# Learn More

[Documentation](https://sli.dev) · [GitHub](https://github.com/slidevjs/slidev) · [Showcases](https://sli.dev/showcases.html)

---
layout: end
class: text-center
---

# Thank You!

Questions?

{{CONTACT_INFO}}
