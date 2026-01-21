## Security Considerations

### Input Sanitization

**For skills that handle user input:**

1. **HTML Entity Escaping** (if generating HTML/web content)
   - Escape special characters before injection: `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`, `"` → `&quot;`, `'` → `&#39;`
   - Never allow raw `<script>` tags from user input
   - Sanitize all user-provided content: titles, descriptions, names, custom text

2. **URL Validation** (if accepting URLs)
   - Validate URL format before using
   - Allow only safe protocols: `http:`, `https:`, `file:` (for local files only)
   - Reject dangerous protocols: `javascript:`, `data:`, `vbscript:`, `blob:`
   - Example validation: URL must match pattern `^(https?|file):\/\/.+`

3. **File Path Safety** (if reading/writing files)
   - Prevent directory traversal attacks
   - Reject paths containing `../` or `..\`
   - Validate paths are within expected directories
   - Never execute or eval file contents
   - Use absolute paths or properly validated relative paths

### Content Safety

1. **External Resources**
   - Validate YAML/JSON/XML before parsing
   - Check file extensions match actual content type
   - Scan for malicious content patterns
   - Limit file sizes to prevent DoS

2. **Generated Output**
   - If generating HTML: Consider adding CSP meta tag
   - If generating scripts: Validate no code injection
   - If generating config: Validate syntax

**Example CSP (for HTML generation):**
```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self' https://cdn.jsdelivr.net;
               style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
               script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
               img-src 'self' https: data:;">
```

### External Dependencies

1. **CDN Resources**
   - Use HTTPS only
   - Consider Subresource Integrity (SRI) hashes
   - Example: `<script src="..." integrity="sha384-..." crossorigin="anonymous"></script>`
   - Have fallback options if CDN fails

2. **Third-party APIs**
   - Document API risks and rate limits
   - Implement error handling for API failures
   - Never expose API keys in skill code
   - Use environment variables for credentials

3. **External Tools**
   - Verify tool is installed before running
   - Validate tool version compatibility
   - Handle tool execution failures
   - Provide installation instructions

### Sensitive Information

1. **Speaker Notes / Private Content**
   - Warn users that content may be visible in output
   - Recommend not including passwords, API keys, or confidential data
   - Consider adding "sanitize sensitive info" option

2. **Personal Information**
   - No personal email addresses in examples
   - No real names in sample data
   - No actual API keys or tokens (use placeholders like `YOUR_API_KEY`)

### Best Practices

- **Principle of Least Privilege**: Request minimum permissions needed
- **Defense in Depth**: Multiple layers of validation
- **Fail Securely**: On error, fail to safe state (don't expose data)
- **Security by Default**: Secure settings as defaults, not opt-in

---

## Example: Secure vs Insecure

### ❌ Insecure
```javascript
// Directly inject user input
document.innerHTML = userInput;  // XSS vulnerability!

// No URL validation
const img = `<img src="${userUrl}">`;  // Can inject javascript:

// No path validation
fs.readFile(userPath);  // Directory traversal!
```

### ✅ Secure
```javascript
// Escape HTML entities
const escaped = userInput
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
document.innerHTML = escaped;

// Validate URL
const urlPattern = /^https?:\/\/.+/;
if (urlPattern.test(userUrl)) {
    const img = `<img src="${userUrl}">`;
}

// Validate and normalize path
const safePath = path.resolve(basePath, userPath);
if (safePath.startsWith(basePath)) {
    fs.readFile(safePath);
}
```
