# Security Policy: CareSync AI

CareSync AI takes healthcare data integrity, senior user safety, and enterprise platform security seriously.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Defensive Security Architecture

1. **Strict CORS Policy**: Restricted strictly to authorized frontend origins and regex-verified preview environments. Wildcard origins (`*`) are prohibited.
2. **Rate Limiting**: Sliding-window rate limiter enforcing 30 requests/minute per client IP across all `/api/*` routes with automatic `Retry-After` headers.
3. **Payload Sanitization & Size Constraints**: Hard-enforced 5MB file payload limit (HTTP 413) and strict MIME validation (`image/jpeg`, `image/png`, `image/webp` -> HTTP 415).
4. **Spoofing & File Integrity Verification**: All binary image streams undergo internal PIL header integrity analysis via `PIL.Image.verify()` prior to inference.
5. **Security Headers**:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: camera=(self), microphone=()`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Reporting a Vulnerability

If you discover a security vulnerability within CareSync AI, please DO NOT open a public GitHub issue.

Instead, please send an encrypted or direct email to `security@caresync-ai.dev` or reach out to the project maintainers directly. We commit to acknowledging receipt within 24 hours and providing an evaluation or patch plan within 72 hours.
