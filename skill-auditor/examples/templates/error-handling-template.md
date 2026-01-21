## Error Handling

### File Operations

1. **File Existence Checks**
   ```markdown
   Before reading/writing files:
   - Check if file exists
   - Verify file is readable/writable
   - Provide clear error message with file path
   ```

   **Example error messages:**
   - ✅ Good: "File not found at /path/to/file.yaml. Please check the path exists."
   - ❌ Bad: "Error reading file"

2. **File Read Errors**
   - Handle permission denied errors
   - Handle file format errors (invalid YAML, JSON, etc.)
   - Provide fallback options when possible

   **Example:**
   ```
   If style YAML cannot be read:
   - Error: "Failed to read style file: [error details]"
   - Fallback: "Using default style instead"
   ```

3. **File Write Errors**
   - Check disk space before writing
   - Verify parent directory exists
   - Handle write permission errors
   - Don't leave partial/corrupted files

### User Input Validation

1. **Required Fields**
   - Validate all required inputs are provided
   - Check inputs are not empty strings
   - Validate data types match expectations

   **Example:**
   ```
   If presentation title is missing:
   - Error: "Presentation title is required. Please provide a title."
   - Action: Ask user for input via AskUserQuestion
   ```

2. **Format Validation**
   - URLs: Must match valid URL pattern
   - File paths: Must be valid absolute or relative paths
   - Email addresses: Must match email format
   - Dates: Must be valid date format

   **Example:**
   ```
   If image URL is invalid:
   - Error: "Invalid image URL: [url]. Expected http:// or https://"
   - Fallback: "Using placeholder image instead"
   ```

3. **Range Validation**
   - Numbers within expected range
   - String length limits
   - Array size limits

### External Dependency Failures

1. **Command Not Found**
   ```markdown
   If required tool is not installed:
   - Error: "Tool 'jq' not found. Please install: brew install jq"
   - Alternative: "Or install via: apt-get install jq (Linux)"
   - Action: Provide installation link/instructions
   ```

2. **API/Network Failures**
   ```markdown
   If external API fails:
   - Error: "Failed to fetch data from [API]. Error: [details]"
   - Retry: Attempt 2-3 times with exponential backoff
   - Fallback: Use cached data or default values
   - Timeout: Set reasonable timeout (30s for API calls)
   ```

3. **Tool Execution Errors**
   ```markdown
   If external tool fails:
   - Capture stderr output
   - Parse error message
   - Provide context-specific guidance
   - Example: "Gemini CLI failed: [error]. Check API key is set."
   ```

### Generation Errors

1. **Template Processing**
   ```markdown
   If template variable is undefined:
   - Warning: "Variable {{UNDEFINED}} not provided, using default: [value]"
   - Fallback: Use empty string or sensible default
   - Never leave unreplaced {{VARIABLES}} in output
   ```

2. **Syntax Validation**
   ```markdown
   If generating code/config:
   - Validate syntax before saving (YAML, JSON, HTML, etc.)
   - Check for unclosed tags, brackets, quotes
   - Provide specific syntax error location
   ```

3. **Output Validation**
   ```markdown
   Before returning generated content:
   - Verify output is not empty
   - Check required elements are present
   - Validate format matches expectations
   ```

### Graceful Degradation

When errors occur, follow this pattern:

1. **Detect**: Identify the specific error
2. **Log**: Record error details (for debugging)
3. **Inform**: Tell user what went wrong
4. **Fallback**: Provide alternative if possible
5. **Guide**: Suggest how to fix or work around

**Example flow:**
```
Error detected: Style YAML file not found
↓
Log: "Style file missing: blueprint.yaml at /expected/path"
↓
Inform user: "Style 'blueprint' not found. Available styles: swiss-clean, blue-mono"
↓
Fallback: "Using default style 'swiss-clean' instead"
↓
Guide: "To use custom styles, set $STYLE_DIR environment variable"
```

### Error Message Best Practices

**Good Error Messages:**
- ✅ Specific: Tell exactly what failed
- ✅ Contextual: Include relevant details (file path, line number)
- ✅ Actionable: Suggest how to fix
- ✅ Friendly: Professional tone, no blame

**Examples:**

✅ **Good:**
```
"Image file not found at '/path/to/image.jpg'.
 Please check:
 1. File path is correct
 2. File exists and is readable
 3. Image format is supported (jpg, png, svg, gif)
 Using placeholder image instead."
```

❌ **Bad:**
```
"Error: img not found"
```

### Testing Error Handling

When designing your skill, test these scenarios:

- [ ] What if required file doesn't exist?
- [ ] What if user provides empty input?
- [ ] What if network is unavailable?
- [ ] What if external tool is not installed?
- [ ] What if YAML/JSON is malformed?
- [ ] What if user cancels operation?
- [ ] What if disk is full?
- [ ] What if permissions are denied?

---

## Template Usage

Copy relevant sections from this template into your SKILL.md, customizing for your specific skill's needs.

Remove sections that don't apply to your skill (e.g., if no network operations, remove API failure handling).
