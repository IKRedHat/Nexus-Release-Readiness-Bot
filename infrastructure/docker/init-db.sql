-- ============================================================================
-- Nexus PostgreSQL Initialization Script
-- Supports: LangGraph State Persistence + Vector Memory (pgvector)
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- LANGGRAPH CHECKPOINTS TABLE
-- Stores state snapshots for LangGraph workflows
-- ============================================================================

CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
    thread_id VARCHAR(255) NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL,
    parent_checkpoint_id VARCHAR(255),
    checkpoint_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON langgraph_checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON langgraph_checkpoints(created_at);
CREATE INDEX IF NOT EXISTS idx_checkpoints_parent ON langgraph_checkpoints(parent_checkpoint_id);

-- ============================================================================
-- VECTOR MEMORY TABLE
-- Stores embeddings for RAG-enhanced context retrieval
-- ============================================================================

CREATE TABLE IF NOT EXISTS vector_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vector_memory_doc_id ON vector_memory(doc_id);
CREATE INDEX IF NOT EXISTS idx_vector_memory_embedding ON vector_memory USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- CONVERSATION MEMORY TABLE
-- Stores conversation history per session
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversation_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_created ON conversation_memory(created_at);

-- ============================================================================
-- TOOL EXECUTION LOG TABLE
-- Audit trail for MCP tool executions
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_execution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id VARCHAR(255),
    tool_name VARCHAR(255) NOT NULL,
    tool_server VARCHAR(255),
    input_args JSONB,
    output_result JSONB,
    status VARCHAR(50) NOT NULL,  -- 'success', 'error', 'timeout'
    execution_time_ms FLOAT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tool_log_thread ON tool_execution_log(thread_id);
CREATE INDEX IF NOT EXISTS idx_tool_log_tool ON tool_execution_log(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_log_status ON tool_execution_log(status);
CREATE INDEX IF NOT EXISTS idx_tool_log_created ON tool_execution_log(created_at);

-- ============================================================================
-- RELEASE DECISION LOG TABLE
-- Historical record of Go/No-Go decisions
-- ============================================================================

CREATE TABLE IF NOT EXISTS release_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    release_version VARCHAR(100) NOT NULL,
    decision VARCHAR(50) NOT NULL,  -- 'GO', 'NO_GO', 'CONDITIONAL'
    rationale TEXT,
    checklist JSONB,
    blockers JSONB DEFAULT '[]',
    risks JSONB DEFAULT '[]',
    requested_by VARCHAR(255),
    approved_by VARCHAR(255),
    confluence_page_id VARCHAR(255),
    confluence_page_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_release_version ON release_decisions(release_version);
CREATE INDEX IF NOT EXISTS idx_release_decision ON release_decisions(decision);
CREATE INDEX IF NOT EXISTS idx_release_created ON release_decisions(created_at);

-- ============================================================================
-- RCA ANALYSIS LOG TABLE
-- Root Cause Analysis records
-- ============================================================================

CREATE TABLE IF NOT EXISTS rca_analysis_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(255) NOT NULL,
    build_number INTEGER NOT NULL,
    build_url TEXT,
    repo_name VARCHAR(255),
    branch VARCHAR(255),
    commit_sha VARCHAR(100),
    pr_id INTEGER,
    root_cause_summary TEXT,
    root_cause_category VARCHAR(100),
    suspected_files JSONB DEFAULT '[]',
    suggested_fix TEXT,
    confidence_score FLOAT,
    analysis_time_ms FLOAT,
    trigger VARCHAR(50),  -- 'webhook', 'manual', 'mcp_tool'
    slack_notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rca_job ON rca_analysis_log(job_name);
CREATE INDEX IF NOT EXISTS idx_rca_repo ON rca_analysis_log(repo_name);
CREATE INDEX IF NOT EXISTS idx_rca_created ON rca_analysis_log(created_at);

-- ============================================================================
-- HYGIENE CHECK LOG TABLE
-- Jira data quality check records
-- ============================================================================

CREATE TABLE IF NOT EXISTS hygiene_check_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    check_id VARCHAR(255) UNIQUE NOT NULL,
    project_key VARCHAR(50) NOT NULL,
    total_tickets_checked INTEGER DEFAULT 0,
    compliant_tickets INTEGER DEFAULT 0,
    non_compliant_tickets INTEGER DEFAULT 0,
    hygiene_score FLOAT,
    violation_summary JSONB DEFAULT '{}',
    violations_by_assignee JSONB DEFAULT '[]',
    trigger_type VARCHAR(50),  -- 'scheduled', 'manual', 'mcp_tool'
    notifications_sent INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hygiene_project ON hygiene_check_log(project_key);
CREATE INDEX IF NOT EXISTS idx_hygiene_score ON hygiene_check_log(hygiene_score);
CREATE INDEX IF NOT EXISTS idx_hygiene_created ON hygiene_check_log(created_at);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for vector_memory
CREATE TRIGGER update_vector_memory_updated_at
    BEFORE UPDATE ON vector_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert a system configuration record (for testing)
INSERT INTO vector_memory (doc_id, content, metadata)
VALUES (
    'system-info',
    'Nexus is a Release Automation System that uses LangGraph for orchestration and MCP for tool connectivity. It supports multiple LLM providers including OpenAI, Google Gemini, and Ollama.',
    '{"type": "system", "version": "3.0.0"}'
) ON CONFLICT (doc_id) DO NOTHING;

-- ============================================================================
-- GRANTS (for application user)
-- ============================================================================

-- Grant all privileges to nexus user (already owner, but explicit for clarity)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nexus;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nexus;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO nexus;

