# Information Architecture

## Business Domain Model

- **Tenant**: Represents an individual rental entity, containing details like name, address, and contact information.
- **User**: System users with roles such as master_admin, admin, user, and internal, each with specific permissions.
- **Contract**: Rental agreements including details like parties involved, property information, rental terms, and status.
- **Document**: Represents generated documents like contracts and attachments.
- **Signature**: Details about the signing process, including channels and status.

## Business Logic

- **Tenant Management**: Handling tenant-specific data and configurations, ensuring isolation and security.
- **User Management**: Role-based access control, user authentication, and profile management.
- **Contract Lifecycle**: From creation, validation, and signing to archiving, including multi-signer workflows.
- **Document Handling**: Generation, storage, and retrieval of documents, ensuring compliance and security.
- **Signature Processing**: Integration with eSignature providers, managing the signing workflow and status tracking.

## Validation Rules

- **Email Format**: Must be a valid email structure.
- **Phone Number**: Must adhere to specified formatting rules.
- **Date Fields**: Proper date format and logical consistency (e.g., birth date in the past).
- **Required Fields**: Certain fields must be filled based on the context (e.g., tenant_id in user profile).

## Security Model

- **Authentication**: Secure login mechanisms, including password hashing and session management.
- **Authorization**: Role-based access control, ensuring users can only access data and functions permitted to their role.
- **Data Protection**: Encryption of sensitive data, secure storage of documents, and secure transmission channels.

## Business Workflow

1. **User Registration**: Collect and validate user details, create a new user profile, and send confirmation.
2. **Tenant Onboarding**: Capture tenant details, configure initial settings, and create default documents.
3. **Contract Creation**: Users create contracts by filling out forms, which are then validated and saved as drafts.
4. **Document Generation**: Generate PDF documents from contract data, applying templates and including signatures.
5. **Signature Process**: Send documents for signing via selected channels, track status, and handle completions.
6. **Contract Archiving**: Move completed contracts to an archive, making them read-only and removing from active lists.

<!-- Database schema moved to software_architecture.md for consolidation -->