# Development Guidelines# Development Guidelines# Development Guidelines




































- **Update Workflow**: Keep summaries current when source documents change- **Selective Content**: Send only relevant documentation sections per query to avoid token limits- **Documentation Summaries**: Maintain concise outlines of each documentation file for quick LLM context- **Context Efficiency**: Reference section titles or IDs instead of pasting full document content- **Token Management**: Split large documents into smaller chunks (500–1000 tokens) when prompting LLMs## LLM Interaction Guidelines- Anonymized real data for development and testing environments- Use production-like data for comprehensive testing### 5. Real Data Testing- Least privilege access control- Input validation and output encoding- Multi-tenant isolation and secure authentication### 4. Security by Design- Dependency injection for easier testing and maintenance- Use of design patterns where applicable- Separation of UI, business logic, and data layers### 3. Clean Architecture- End-to-end tests for critical user journeys- Integration tests for external API interactions- Unit tests for all core functionalities- All features require upfront test case definition### 2. Test-Driven Development- Architecture decisions must be recorded in status.md- **No new documentation .md files should be created** - extend existing documents- Changes require updates to relevant documentation files- Technical documentation only - no marketing language- All features must be documented before implementation### 1. Documentation-Driven Development## Core Principles


































































- Record any architecture decisions in status.md- Mark task as complete in tasks.md- **Git commit and `git push` changes** to remote- **Update relevant documentation files**- Confirm no placeholder code exists- Verify all tests pass with real data### After Implementation6. **Test against actual project scenarios continuously**5. Clean up temporary files immediately4. Update modules.md for new files3. Commit frequently with descriptive messages2. Implement complete functionality - no stubs or placeholders1. Follow TDD: write tests with real data first### During Implementation- **Verify no placeholder implementations will be created**- **Set up GitHub Project board** and link tasks to issues/columns- Review existing code for reusability- Update architecture documentation if needed- Define test cases with real data scenarios- Create task entry in tasks.md### Before Implementation## Workflow Requirements- **Update Workflow**: Keep summaries current when source documents change- **Selective Content**: Send only relevant documentation sections per query to avoid token limits- **Documentation Summaries**: Maintain concise outlines of each documentation file for quick LLM context- **Context Efficiency**: Reference section titles or IDs instead of pasting full document content- **Token Management**: Split large documents into smaller chunks (500–1000 tokens) when prompting LLMs## LLM Interaction Guidelines- Never fallbacks for missing functionality - implement the feature completely- Fallbacks only for system stability (network failures, service unavailability)- **No "TODO" or "FIXME" comments in production code**- **All features must be fully functional upon implementation**- **No placeholder implementations, dummy functions, or mock business logic**### 5. Real Implementation Standards- File creation, modification, and deletion must be tracked- Mandatory cleanup of temporary files after use- Temporary files in designated folders: `temp/`, `test_cases/`, `scratch/`- New files must be registered in modules.md with ID and description### 4. File Management Standards- Task status tracking required- No implementation without corresponding task documentation- Tasks must be actionable and measurable- All work (features, bugs, refactoring) must have entries in tasks.md### 3. Task-Driven Implementation- **Testing against real project data and scenarios - no mock business logic**- Unit, integration, and edge case testing required- Test cases defined upfront in testing.md- Minimum 75% code coverage for new modules### 2. Test-Driven Development- Architecture decisions must be recorded in status.md- **No new documentation .md files should be created** - extend existing documents- Changes require updates to relevant documentation files- Technical documentation only - no marketing language- All features must be documented before implementation### 1. Documentation-Driven Development## Core Principles
## Documentation Guidelines
- All project documentation must be placed in `/docs` and follow the existing structure.
- **Do not create new `.md` documentation files.** Update or extend existing documents as needed.

## LLM Interaction Guidelines
- Summarize each documentation file into concise outlines before prompting the LLM.
- Split large documents into smaller chunks (e.g., 500–1000 tokens) and feed only the relevant chunk per query.
- Use a document index (vector store or simple TOC) to retrieve and send only the necessary sections.
- Maintain and update summaries whenever source documents change to keep context current.
- When prompting, reference section titles or IDs instead of pasting full content.