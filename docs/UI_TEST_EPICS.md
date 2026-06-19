# Elitea UI Testing - EPIC Level Feature Map

Based on analysis of https://elitea.ai/docs documentation

---

## EPIC 1: Chat & Conversations

**Core Functionality:** Central hub for interacting with AI agents, managing conversations, and collaboration.

### Features to Test:

1. **Conversation Management**
   - Create new conversation
   - Create conversation folders
   - Move conversations between folders
   - Rename conversations
   - Delete conversations
   - Duplicate/copy conversations
   - Share conversations (private/public/team)

2. **Conversation Visibility & Permissions**
   - Private conversations (user-only)
   - Team project conversations (shared within project)
   - Public conversations
   - Folder visibility controls

3. **Participants Management**
   - Add/remove human users to conversations
   - Add/remove AI agents as participants
   - Add/remove pipelines as participants
   - Add/remove toolkits/MCPs as participants
   - View active participants list

4. **Chat Interface Features**
   - Send messages
   - Receive AI responses
   - Message formatting (markdown support)
   - Attachments (upload files to conversation)
   - Message actions (edit, delete, regenerate)
   - Message history/scroll

5. **Canvas Feature**
   - Open canvas for code blocks
   - Open canvas for tables
   - Open canvas for Mermaid diagrams
   - Edit content in canvas
   - Copy content from canvas
   - Export/download from canvas
   - Undo/redo in canvas
   - Save canvas changes

6. **Internal Tools**
   - Access and use conversation-level tools
   - Tool execution and output display

7. **LLM Configuration**
   - Select LLM model for conversation
   - Configure context budget
   - Adjust generation parameters

8. **Conversation Starters**
   - Display configured starter prompts
   - Use starter prompts to initiate conversation

---

## EPIC 2: Agents

**Core Functionality:** Create, configure, and manage AI agents with specific instructions and toolkits.

### Features to Test:

1. **Agents Dashboard**
   - View list of all agents
   - Filter agents (my agents, public, shared)
   - Search agents by name/description
   - Sort agents

2. **Create Agent**
   - Set agent name and description
   - Configure agent icon/avatar
   - Write agent instructions/system prompt
   - Set welcome message
   - Configure conversation starters
   - Save agent configuration

3. **Toolkit Selection for Agents**
   - Browse available toolkits
   - Add toolkits to agent
   - Remove toolkits from agent
   - Configure toolkit parameters
   - Enable/disable internal tools

4. **Agent Visibility**
   - Set agent as private
   - Set agent as public (shareable)
   - Set agent as team/project level

5. **Agent Actions**
   - Edit agent configuration
   - Duplicate/fork agent
   - Delete agent
   - Start conversation with agent
   - View agent usage history

6. **Agents Studio**
   - Browse public agents catalog
   - View agent details (description, toolkits, rating)
   - Search and filter agents
   - Start conversation from agent card
   - Fork/copy public agents

---

## EPIC 3: Pipelines

**Core Functionality:** Create and manage multi-step workflows that chain multiple AI operations.

### Features to Test:

1. **Pipelines Dashboard**
   - View list of all pipelines
   - Filter pipelines (my pipelines, public, shared)
   - Search pipelines
   - Sort pipelines

2. **Create Pipeline**
   - Set pipeline name and description
   - Configure pipeline icon
   - Define pipeline structure/flow
   - Add steps/nodes to pipeline
   - Configure node connections
   - Set welcome message
   - Configure conversation starters

3. **Pipeline Canvas Interface**
   - Visual pipeline builder
   - Drag-and-drop nodes
   - Connect nodes
   - Edit node configuration
   - Delete nodes
   - Validate pipeline flow

4. **Toolkit Configuration in Pipelines**
   - Select toolkits for pipeline steps
   - Configure toolkit parameters per step
   - Test toolkit connections

5. **Pipeline Execution**
   - Run pipeline in conversation
   - Monitor pipeline execution status
   - View step-by-step results
   - Handle pipeline errors

6. **Pipeline History**
   - View execution history
   - Review past run results
   - Debug failed executions

7. **Pipeline Management**
   - Edit pipeline configuration
   - Duplicate pipeline
   - Delete pipeline
   - Share pipeline (visibility settings)

---

## EPIC 4: Toolkits & MCPs

**Core Functionality:** Manage integrations with external tools and services.

### Features to Test:

1. **Toolkits Dashboard**
   - View all available toolkits
   - Filter by category (Jira, GitHub, Confluence, etc.)
   - Search toolkits
   - View toolkit details

2. **Create Toolkit**
   - Configure toolkit name and description
   - Select toolkit type/category
   - Set toolkit icon
   - Configure toolkit parameters
   - Add credentials/authentication
   - Test toolkit connection

3. **Toolkit Categories**
   - Integration toolkits (Jira, GitHub, Confluence, TestRail, Figma, Rally, Xray)
   - Artifact toolkit
   - Data analysis toolkits
   - Custom OpenAPI toolkits
   - Python/code execution toolkits

4. **Toolkit Configuration**
   - Edit toolkit settings
   - Update credentials
   - Enable/disable tools within toolkit
   - Configure tool parameters
   - Set default values

5. **MCPs Management**
   - View MCPs dashboard
   - Create new MCP (Local/Remote)
   - Configure MCP client (stdio)
   - Configure remote MCP (URL + auth)
   - Test MCP connection
   - Add MCP to conversations

6. **MCP Types**
   - Local MCP (stdio client)
   - Remote MCP (HTTP endpoint)
   - Bearer token authentication
   - OAuth 2.0 client credentials
   - Custom authentication headers

7. **Toolkit History**
   - View toolkit usage history
   - Review tool execution logs
   - Debug toolkit issues

8. **Individual User Credentials**
   - Allow users to provide their own toolkit credentials
   - Manage personal credentials vs shared

---

## EPIC 5: Credentials & Secrets

**Core Functionality:** Securely manage authentication credentials and secrets for integrations.

### Features to Test:

1. **Credentials Dashboard**
   - View all credentials
   - Filter credentials by type
   - Search credentials
   - View credential details

2. **Create Credential**
   - Set credential name and description
   - Select credential type
   - Enter credential data (API keys, tokens, username/password)
   - Associate with specific toolkit
   - Save credential

3. **Supported Credential Types**
   - API keys
   - Bearer tokens
   - OAuth tokens
   - Username/password
   - SSH keys
   - Custom credential types

4. **Credential Actions**
   - Edit credential
   - Update credential values
   - Delete credential
   - Test credential validity

5. **Secrets Management**
   - Create project-level secrets
   - Create user-level secrets
   - Reference secrets in credentials
   - View secrets list (masked values)
   - Update secrets
   - Delete secrets

6. **Default Secrets**
   - View default system secrets
   - Override default secrets
   - Restore default secrets

7. **Security Features**
   - Masked secret display
   - Secret encryption
   - Access control (who can view/edit)

---

## EPIC 6: Artifacts & Indexing

**Core Functionality:** Store files, create knowledge bases, and enable RAG (Retrieval Augmented Generation).

### Features to Test:

1. **Artifacts Dashboard**
   - View all artifact buckets
   - Filter buckets
   - Search buckets
   - View bucket details

2. **Bucket Management**
   - Create new bucket
   - Edit bucket name/description
   - Delete bucket
   - Set bucket permissions

3. **File Operations**
   - Upload files to bucket
   - Download files from bucket
   - Delete files
   - View file details
   - Search files within bucket

4. **Artifact Toolkit Integration**
   - Add artifact toolkit to agent
   - Generate artifacts via conversation
   - Save artifacts automatically
   - Retrieve artifacts in conversation

5. **Indexing**
   - Access indexes tab
   - Create new index
   - Configure index parameters (embedding model, chunk size, etc.)
   - Upload documents to index
   - Delete index
   - Update index

6. **Index Configuration**
   - Select embedding model
   - Set chunk size
   - Set chunk overlap
   - Configure retrieval settings
   - Test index search

7. **RAG Integration**
   - Use indexed data in conversations
   - Query knowledge base
   - Cite sources in responses

---

## EPIC 7: Settings & Configuration

**Core Functionality:** System-wide and project-level configuration.

### Features to Test:

1. **AI Configuration**
   - View available LLM models
   - Add custom LLM models
   - Create LLM provider credentials
   - Configure default models
   - Set model parameters (temperature, max tokens, etc.)
   - Test model connectivity

2. **Personal Access Tokens**
   - Generate new API token
   - View existing tokens
   - Revoke token
   - Copy token to clipboard
   - Set token expiration

3. **Projects Management**
   - View project details
   - Create new project
   - Edit project settings
   - View project members/teammates
   - Manage project groups
   - Set user roles (admin, member, viewer)

4. **Monitoring**
   - View usage dashboards
   - Track token consumption
   - View execution metrics
   - Monitor agent/pipeline performance
   - Export monitoring data
   - Filter by project/group

5. **System Health**
   - Run system health check
   - View component status
   - Check integration connectivity

---

## EPIC 8: Profile & Personalization

**Core Functionality:** User-specific settings and preferences.

### Features to Test:

1. **Profile Settings**
   - View user profile
   - Update profile information
   - Change avatar/profile picture
   - Update email/contact info

2. **Personalization**
   - Configure UI theme (light/dark mode)
   - Set language preferences
   - Configure notification settings
   - Set default conversation settings

3. **Default Context Management**
   - Configure default context for new conversations
   - Set context length preferences
   - Manage context budget defaults

4. **Default Summarization**
   - Enable/disable auto-summarization
   - Configure summarization parameters
   - Set summarization triggers

---

## EPIC 9: Collaboration & Sharing

**Core Functionality:** Team collaboration and resource sharing.

### Features to Test:

1. **Sharing Conversations**
   - Share conversation link
   - Set conversation visibility (private/team/public)
   - Add teammates to conversation
   - Remove teammates from conversation
   - View conversation participants

2. **Sharing Agents**
   - Publish agent to team
   - Publish agent publicly
   - Fork/duplicate shared agent
   - View agent sharing permissions

3. **Sharing Pipelines**
   - Share pipeline with team
   - Publish pipeline publicly
   - Fork pipeline
   - View pipeline permissions

4. **Team Project Features**
   - View team resources
   - Access shared credentials
   - Use shared toolkits
   - Collaborate on conversations

---

## EPIC 10: Search & Discovery

**Core Functionality:** Find and discover resources across the platform.

### Features to Test:

1. **Global Search**
   - Search conversations
   - Search agents
   - Search pipelines
   - Search toolkits
   - Search artifacts

2. **Participant Search (# in chat)**
   - Search agents via #
   - Search pipelines via #
   - Add participant from search results

3. **Public Catalog**
   - Browse Agents Studio
   - Filter public agents
   - Search public resources
   - View resource ratings/reviews

4. **History & Activity**
   - View conversation history
   - View agent usage history
   - View pipeline execution history
   - View toolkit activity logs

---

## Test Priority Matrix

### P0 (Critical - Must Work)
- Create conversation
- Send/receive messages in chat
- Create and use agents
- Add toolkits to agents
- Basic authentication and login

### P1 (High - Core Features)
- Conversation sharing and permissions
- Pipeline creation and execution
- Canvas functionality
- Toolkit configuration
- Credentials management
- File upload to artifacts

### P2 (Medium - Important Features)
- Indexing and RAG
- MCPs configuration
- Advanced agent settings
- Monitoring dashboards
- Personalization settings

### P3 (Low - Nice to Have)
- UI theme customization
- Conversation starters
- Public catalog browsing
- Export features

---

## Integration Test Scenarios

1. **End-to-End Jira Workflow**
   - Configure Jira toolkit → Create agent with Jira tools → Query Jira issues in chat

2. **End-to-End Pipeline Workflow**
   - Create pipeline → Add steps → Execute via conversation → Verify results

3. **End-to-End RAG Workflow**
   - Create artifact bucket → Upload documents → Create index → Query in conversation

4. **End-to-End Collaboration Workflow**
   - Create conversation → Add teammate → Both users interact → Verify sync

---

## API Testing Scope

Based on documentation, the following should be testable via API:

- Conversation CRUD
- Agent CRUD
- Pipeline CRUD
- Toolkit configuration
- Message sending/receiving
- File upload to artifacts
- Index creation and management
- Token generation

---

**Document Generated:** 2026-02-18
**Source:** https://elitea.ai/docs/
**Method:** Automated documentation analysis via Playwright
