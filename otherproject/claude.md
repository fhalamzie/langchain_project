# Claude AI Instructions for Online Mietvertrag Project

## Core Development Principles

### Test-Driven Development (TDD)
- **CRITICAL**: Write tests based on expected input/output pairs FIRST
- Do NOT create mock implementations or mock tests
- Only write code that passes the defined tests
- Do NOT modify tests to bypass faulty implementation
- Use real data for testing, not synthetic/mock data
- Tests must define clear expected behaviors before any implementation

### Documentation Updates
When instructed to "update docs":
1. First examine claude.md to identify which documents require updates
2. Review the referenced .md files in /docs folder to understand current state
3. Update ONLY the identified documents in /docs folder
4. Keep updates short, clean, and neutral
5. Never create new .md files - only update existing ones

### Documentation Editing Standards
**STRICT RULES for document updates:**
1. **Content-Only Updates**: Make ONLY the requested changes
2. **No Editorial Commentary**: Never add excitement, breakthrough announcements, or personal commentary
3. **No Scope Creep**: Don't fix unrelated issues or add "improvements" not requested
4. **Preserve Formatting**: Maintain existing markdown structure and tone
5. **No Version Comments**: Don't add timestamps, version notes, or "updated by" comments

**FORBIDDEN in documentation:**
- "BREAKTHROUGH:", "FIXED:", "AMAZING:", excitement language
- Unrelated improvements or optimizations
- Personal opinions or commentary
- Implementation excitement or celebration
- Cross-references not specifically requested

### Architecture Compliance
- ALL documentation must be in /docs folder only
- Follow multi-tenant design patterns
- Maintain separation of concerns (UI/API/Core/DB)
- Implement proper role-based access control
- Follow security-by-design principles

## Token Efficiency Strategy

### Context Loading Strategy
**Document Classification:**
- **Critical Detail Documents** (Load full): Development Guidelines.md, api_specification.md, testing.md
- **Template-Friendly Documents** (Use TL;DR + details): software_architecture.md, requirements.md, ui.md
- **Reference Documents** (Smart references): deployment.md, environment_configuration.md, modules.md

**Query Classification:**
- **Development questions** → Load full Development Guidelines.md + relevant code sections
- **API questions** → Load api_specification.md (full) + architecture summary
- **Architecture questions** → Load software_architecture.md summary, details on request
- **Testing questions** → Load testing.md (full) + specific test files
- **Deployment questions** → Reference deployment.md sections, load on request

**Smart References Pattern:**
When possible, use: "See docs/[file].md#[section]" instead of full content.
Load full content only when:
1. User explicitly requests details
2. Implementation/coding questions require exact specifications
3. Working with Development Guidelines or API specs

### Conversation State Management
- **ALWAYS start by checking /docs/conversation_state.md** for previous context
- Update conversation_state.md with key decisions and loaded context
- Reference previous discussions instead of re-loading same information
- Track loaded documents to avoid redundant loading
- Build on previous discussions, don't restart from zero

### Documentation Index Maintenance
When updating any .md file in /docs:
1. **Auto-update /docs/doc_index.md** with section headers and line ranges
2. Include key topics per section and last update timestamp
3. Pattern: After any doc modification, update the index

### Document Sync Management
**Accept that docs may be temporarily out of sync**
- Note discrepancies clearly when found
- Ask which source is authoritative
- Update conflicting documents as needed
- Mark sync status in documentation_summary.md

**Sync Priority:**
1. Development Guidelines.md (highest)
2. api_specification.md
3. software_architecture.md
4. Other docs (as needed)

## Referenced Documentation Files

Required for context and updates:
- /docs/requirements.md
- /docs/software_architecture.md  
- /docs/information_architecture.md
- /docs/Development Guidelines.md
- /docs/ui.md
- /docs/api_specification.md
- /docs/testing.md
- /docs/environment_configuration.md
- /docs/deployment.md
- /docs/modules.md
- /docs/tasks.md
- /docs/status.md
- /docs/documentation_summary.md
- /docs/conversation_state.md (for context tracking)
- /docs/doc_index.md (for efficient context loading)

## Code Quality Standards
- Type hints required for all functions
- Pydantic models for data validation
- Comprehensive error handling
- Security-first implementation
- Multi-tenant data isolation

## Update Discipline Enforcement

**Before ANY document update:**
1. State exactly what will be changed
2. Confirm exact scope of modification
3. Make only the requested change
4. Use neutral, professional language
5. No editorial commentary or excitement

**Quality check before responding:**
- Does my response contain ANY commentary beyond the requested change?
- Am I adding anything not specifically requested?
- Am I maintaining the document's existing tone?
- Am I staying within the exact scope requested?

**If uncertain about scope:** Ask for clarification rather than assuming
