## Test Document: English to Japanese

This is a test technical document.

### Feature Description

Handle requests using REST API:

```python
def get_user(user_id):
    response = requests.get(f'/api/users/{user_id}')
    return response.json()
```

Key features:
- Uses `requests` library
- Supports JSON format
- Includes error handling

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | User identifier |
| `timeout` | int | Request timeout |

> **Note:** Ensure the API endpoint uses HTTPS.
