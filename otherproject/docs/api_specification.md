# API Specification

## Overview

RESTful API for the Digital Rental Contract Management System. All endpoints require authentication except login/registration.

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://your-domain.com/api/v1
```

## Authentication

### Bearer Token Authentication
```http
Authorization: Bearer <jwt_token>
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/login
Login user and obtain access token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "tenant_id": 1
  }
}
```

#### POST /auth/logout
Invalidate current session.

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

### User Management

#### GET /users/profile
Get current user profile.

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+49123456789",
  "street": "Musterstraße 1",
  "postal_code": "12345",
  "city": "Berlin",
  "role": "user",
  "tenant_id": 1
}
```

#### PUT /users/profile
Update user profile.

**Request:**
```json
{
  "name": "John Doe",
  "phone": "+49123456789",
  "street": "Musterstraße 1",
  "postal_code": "12345",
  "city": "Berlin"
}
```

### Contract Management

#### POST /contracts
Create new contract.

**Request:**
```json
{
  "mieter1_vorname": "Max",
  "mieter1_nachname": "Mustermann",
  "mieter1_geburtstag": "1990-01-01",
  "mieter1_email": "max@example.com",
  "mieter1_telefon": "+49123456789",
  "liegenschaft": "Musterhaus",
  "lage": "Musterstraße 1, 12345 Berlin",
  "mietbeginn": "2024-01-01",
  "kaltmiete": 800.00,
  "betriebskosten": 150.00,
  "heizkosten": 100.00,
  "kaution": 2400.00,
  "empfaenger_name": "Vermieter GmbH",
  "empfaenger_email": "vermieter@example.com",
  "versand_kanal": "email",
  "signatur_kanal": "email"
}
```

**Response (201):**
```json
{
  "id": 1,
  "status": "Entwurf",
  "created_at": "2024-01-01T10:00:00Z",
  "message": "Contract created successfully"
}
```

#### GET /contracts/{id}
Get contract details.

**Response (200):**
```json
{
  "id": 1,
  "status": "Gesendet",
  "mieter1_vorname": "Max",
  "mieter1_nachname": "Mustermann",
  "liegenschaft": "Musterhaus",
  "kaltmiete": 800.00,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T11:00:00Z"
}
```

#### PUT /contracts/{id}
Update contract (only in "Entwurf" status).

#### DELETE /contracts/{id}
Delete contract (only in "Entwurf" status).

#### POST /contracts/{id}/sign
Send contract for signature via eSignatures.com.

**Response (200):**
```json
{
  "message": "Contract sent for signature",
  "signature_id": "esig_12345",
  "status": "Gesendet"
}
```

#### GET /contracts/{id}/status
Get current contract status.

**Response (200):**
```json
{
  "id": 1,
  "status": "Teilweise signiert",
  "signature_progress": {
    "total_signers": 2,
    "signed_count": 1,
    "pending_signers": ["max@example.com"]
  },
  "last_updated": "2024-01-01T14:30:00Z"
}
```

### Document Management

#### POST /documents/generate
Generate PDF document from contract data.

**Request:**
```json
{
  "contract_id": 1,
  "template": "standard",
  "include_attachments": true
}
```

**Response (200):**
```json
{
  "document_id": "doc_12345",
  "filename": "MV_Musterhaus_2024-01-01.pdf",
  "size_bytes": 245760,
  "generated_at": "2024-01-01T10:00:00Z"
}
```

#### GET /documents/{id}/pdf
Download PDF document.

**Response (200):**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="contract.pdf"
[PDF binary data]
```

### Administration (Admin/Master Admin only)

#### GET /admin/tenants
List all tenants (master_admin only).

**Response (200):**
```json
{
  "tenants": [
    {
      "id": 1,
      "tenant_name": "Property Management GmbH",
      "email": "admin@property.com",
      "city": "Berlin",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /admin/tenants
Create new tenant (master_admin only).

**Request:**
```json
{
  "tenant_name": "New Property Co",
  "street": "Business Str. 1",
  "postal_code": "10115",
  "city": "Berlin",
  "phone": "+49301234567",
  "email": "contact@newproperty.com",
  "default_signature_channel": "email"
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Contract validation failed",
    "details": {
      "field": "mieter1_email",
      "reason": "Invalid email format"
    },
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (resource already exists)
- `422` - Unprocessable Entity (business logic error)
- `500` - Internal Server Error

### Error Codes
- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_ERROR` - Invalid credentials
- `AUTHORIZATION_ERROR` - Insufficient permissions
- `BUSINESS_LOGIC_ERROR` - Business rule violation
- `EXTERNAL_SERVICE_ERROR` - eSignatures.com API error
- `DATABASE_ERROR` - Database operation failed

## Rate Limiting

- Authentication endpoints: 5 requests per minute per IP
- Contract creation: 10 requests per minute per user
- Document generation: 20 requests per minute per user
- General API: 100 requests per minute per user

## Webhooks (Future)

### Contract Status Updates
```json
{
  "event": "contract.status_changed",
  "contract_id": 1,
  "old_status": "Gesendet",
  "new_status": "Signiert (Alle)",
  "timestamp": "2024-01-01T15:00:00Z"
}
```
