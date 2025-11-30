# API Reference Overview

This section provides documentation for all Nexus agent APIs. Each agent exposes a RESTful API following OpenAPI 3.0 specifications.

## Base URLs

| Service | Development | Production |
|---------|-------------|------------|
| Orchestrator | `http://localhost:8080` | `https://nexus.example.com/api` |
| Jira Agent | `http://localhost:8081` | Internal only |
| Git/CI Agent | `http://localhost:8082` | Internal only |
| Reporting Agent | `http://localhost:8083` | Internal only |
| Slack Agent | `http://localhost:8084` | `https://nexus.example.com/slack` |

## Authentication

### JWT Bearer Token

All inter-service communication uses JWT Bearer tokens:

```bash
curl -X GET http://localhost:8080/health \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Development Mode

In development, authentication can be disabled by setting:
```
NEXUS_REQUIRE_AUTH=false
```

## Common Response Format

All agents return responses in a standardized format:

```json
{
  "task_id": "task-20240115-abc123",
  "status": "success",
  "data": { ... },
  "error_message": null,
  "execution_time_ms": 145.5,
  "agent_type": "jira"
}
```

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Error |

## Rate Limiting

Default rate limits (configurable):
- **100 requests/minute** per client
- Headers returned:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`

## Pagination

For endpoints returning lists:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

Query parameters:
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

## Error Response Format

```json
{
  "task_id": "task-20240115-abc123",
  "status": "failed",
  "data": null,
  "error_message": "Ticket PROJ-999 not found",
  "error_code": "TICKET_NOT_FOUND",
  "agent_type": "jira"
}
```

## OpenAPI Specifications

Interactive API documentation is available at:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

Example:
```
http://localhost:8080/docs
```

