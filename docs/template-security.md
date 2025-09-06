# Larapy Template Security Features

Larapy provides comprehensive template security features inspired by Laravel Blade, ensuring your applications are protected against common web security vulnerabilities.

## 🔒 Security Overview

Larapy's template engine includes the following security features:

- **Automatic XSS Protection** - All output is escaped by default
- **CSRF Protection** - Built-in CSRF token generation and validation
- **Content Security Policy (CSP)** - Nonce-based CSP for inline scripts/styles
- **Input Sanitization** - Multiple sanitization filters available
- **Authentication Directives** - `@auth`, `@guest` directives
- **Authorization Directives** - `@can`, `@cannot` directives
- **Environment Security** - Environment-based content rendering
- **Asset Security** - Versioned and secure asset URLs

## 🛡️ XSS Protection

### Automatic Escaping (Default)
All template output is automatically escaped by default:

```html
<!-- Auto-escaped (safe) -->
{{ user.name }}           <!-- Outputs: &lt;script&gt; if user.name is "<script>" -->
{{ user_input|e }}        <!-- Explicit escaping -->

<!-- Laravel equivalent: {{ $user->name }} -->
```

### Raw Output (Use with Caution)
For trusted content that should not be escaped:

```html
<!-- Unescaped output (dangerous!) -->
{!! trusted_html !!}     <!-- Only use for trusted content -->

<!-- Laravel equivalent: {!! $trusted_html !!} -->
```

### HTML Sanitization
Clean user-generated HTML while allowing safe tags:

```html
<!-- Sanitized HTML -->
{{ user_content|clean_html|safe }}

<!-- With custom allowed tags -->
{{ user_content|clean_html(['p', 'strong', 'em'])|safe }}
```

## 🔐 CSRF Protection

### CSRF Token Generation
```html
<!-- CSRF token field -->
@csrf
<!-- Outputs: <input type="hidden" name="_token" value="abc123..."> -->

<!-- Manual token -->
{{ csrf_token() }}

<!-- Meta tag for AJAX -->
{{ csrf_meta|safe }}
<!-- Outputs: <meta name="csrf-token" content="abc123..."> -->
```

### HTTP Method Spoofing
```html
<!-- Method spoofing for PUT/PATCH/DELETE -->
@method('PUT')
<!-- Outputs: <input type="hidden" name="_method" value="PUT"> -->
```

### Complete Form Example
```html
<form method="POST" action="/users/1">
    @csrf
    @method('PUT')
    
    <input type="text" name="name" value="{{ old('name', user.name|e) }}">
    
    @error('name')
    <div class="alert alert-danger">
        {{ errors.first('name')|e }}
    </div>
    @enderror
    
    <button type="submit">Update</button>
</form>
```

## 🛡️ Content Security Policy

### CSP Nonce Generation
```html
<!-- Inline script with nonce -->
<script nonce="{{ csp_nonce }}">
    console.log('This script is allowed by CSP');
</script>

<!-- Inline style with nonce -->
<style nonce="{{ csp_nonce }}">
    .secure-style { color: blue; }
</style>

<!-- CSP Meta tag -->
{{ csp_meta|safe }}
```

### CSP Configuration
The default CSP policy includes:
- `default-src 'self'`
- `script-src 'self' 'nonce-{random}'`
- `style-src 'self' 'nonce-{random}'`
- `img-src 'self' data: https:`
- `object-src 'none'`

## 🔐 Authentication & Authorization

### Authentication Directives
```html
@auth
    <p>Welcome, {{ auth.name|e }}!</p>
    <a href="/logout">Logout</a>
@endauth

@guest
    <p>Please <a href="/login">login</a></p>
@endguest

<!-- With guard specification -->
@auth('admin')
    <p>Admin panel access</p>
@endauth
```

### Authorization Directives
```html
@can('edit', post)
    <a href="/posts/{{ post.id }}/edit">Edit Post</a>
@endcan

@cannot('delete', post)
    <p>You cannot delete this post</p>
@endcannot

<!-- Multiple permissions -->
@can('create', 'App\\Models\\Post')
    <a href="/posts/create">Create Post</a>
@endcan
```

## 🌍 Environment Security

### Environment-based Content
```html
@production
    <!-- Only shown in production -->
    <script src="https://cdn.example.com/analytics.js"></script>
@endproduction

@env('local', 'development')
    <!-- Only shown in development -->
    <div class="debug-info">Debug mode enabled</div>
@endenv

<!-- Environment variable -->
{{ config('app.env')|e }}
```

## 📦 Asset Security

### Versioned Assets
```html
<!-- Versioned asset URLs -->
@asset('css/app.css')      <!-- /assets/css/app.css?v=abc123 -->
@asset('js/app.js')        <!-- /assets/js/app.js?v=def456 -->

<!-- Manual asset URL -->
{{ asset('images/logo.png') }}
```

### Secure URLs
```html
<!-- Secure HTTPS URLs -->
{{ secure_url('login') }}  <!-- https://example.com/login -->

<!-- Regular URLs -->
@url('home')               <!-- /home -->

<!-- Named routes -->
@route('user.profile', user.id)  <!-- /users/123/profile -->
```

## 📄 JSON Security

### Safe JSON Embedding
```html
<script nonce="{{ csp_nonce }}">
    // Safe JSON data embedding
    var appData = @json({
        'user': user,
        'config': config('app'),
        'csrf_token': csrf_token()
    });
</script>

<!-- Manual JSON encoding -->
{{ data|json_encode|safe }}
```

## 🔧 Security Filters

### Available Filters
```html
<!-- HTML escaping -->
{{ content|e }}

<!-- Raw output -->
{{ content|raw }}

<!-- HTML cleaning -->
{{ content|clean_html }}

<!-- URL encoding -->
{{ url_param|url_encode }}

<!-- Attribute encoding -->
<div class="{{ css_class|attr }}">

<!-- CSS safety -->
<div style="color: {{ user_color|css }};">

<!-- JSON encoding -->
{{ data|json_encode }}
```

## 🔄 Conditional Security

### Unless Directive
```html
@unless(user.is_admin)
    <p>You don't have admin access</p>
@endunless

<!-- Equivalent to -->
@if(not user.is_admin)
    <p>You don't have admin access</p>
@endif
```

### Empty Checks
```html
@empty(posts)
    <p>No posts available</p>
@endempty

@forelse(post in posts)
    <div>{{ post.title|e }}</div>
@empty
    <p>No posts found</p>
@endforelse
```

## 📝 Verbatim Content

### Preventing Template Processing
```html
@verbatim
    This content won't be processed:
    {{ $variable }}
    {!! $raw_content !!}
    @directive
@endverbatim
```

## ⚙️ Configuration

### Template Engine Configuration
```python
# In your application bootstrap
from larapy.view import Jinja2Engine

engine = Jinja2Engine(
    secret_key='your-secret-key',
    autoescape=True,
    auto_reload=True
)
```

### Custom Security Middleware
```python
from larapy.view.security import TemplateSecurityMiddleware

# Create middleware
middleware = TemplateSecurityMiddleware(
    csrf_protection=csrf_instance,
    csp=csp_instance
)

# Get security headers
headers = middleware.get_security_headers()
```

## 🚨 Security Best Practices

### DO:
- ✅ Always escape user input: `{{ user_input|e }}`
- ✅ Use CSRF protection on all forms: `@csrf`
- ✅ Use CSP nonces for inline scripts: `<script nonce="{{ csp_nonce }}">`
- ✅ Validate and sanitize user content: `{{ content|clean_html }}`
- ✅ Use authorization directives: `@can('action', model)`
- ✅ Use secure URLs in production: `{{ secure_url('path') }}`

### DON'T:
- ❌ Don't use raw output for user content: `{!! user_input !!}`
- ❌ Don't disable CSRF protection
- ❌ Don't include sensitive data in templates
- ❌ Don't use `'unsafe-inline'` in CSP without nonces
- ❌ Don't trust user input without sanitization

### Security Headers
The template security system automatically adds these headers:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{random}'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## 🔍 Security Debugging

### Development Mode Features
In development mode, you get additional security debugging:

```html
@env('local')
    <div class="security-debug">
        <h3>Security Debug Info</h3>
        <p>CSRF Token: {{ csrf_token() }}</p>
        <p>CSP Nonce: {{ csp_nonce }}</p>
        <p>Auth Status: {{ auth ? 'Authenticated' : 'Guest' }}</p>
    </div>
@endenv
```

## 📚 Laravel Compatibility

Larapy's template security features provide Laravel Blade equivalents:

| Laravel Blade | Larapy Template | Description |
|---------------|-----------------|-------------|
| `{{ $var }}` | `{{ var\|e }}` | Escaped output |
| `{!! $var !!}` | `{!! var !!}` | Raw output |
| `@csrf` | `@csrf` | CSRF token field |
| `@method('PUT')` | `@method('PUT')` | Method spoofing |
| `@auth` | `@auth` | Authentication check |
| `@can('edit', $post)` | `@can('edit', post)` | Authorization check |
| `@json($data)` | `@json(data)` | Safe JSON output |
| `@env('production')` | `@env('production')` | Environment check |

This comprehensive security system ensures your Larapy applications are as secure as their Laravel counterparts while providing the flexibility and power of Python!