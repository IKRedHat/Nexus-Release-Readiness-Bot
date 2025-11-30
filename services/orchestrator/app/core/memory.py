"""
Nexus Vector Memory
RAG-enabled memory system using ChromaDB or PostgreSQL with pgvector
"""
import os
import sys
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared")))

logger = logging.getLogger("nexus.memory")


@dataclass
class MemoryDocument:
    """A document stored in memory"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None


class VectorMemory:
    """
    Vector-based memory system for RAG (Retrieval Augmented Generation)
    Supports ChromaDB (local) and pgvector (PostgreSQL) backends
    """
    
    def __init__(
        self,
        backend: str = None,
        collection_name: str = "nexus_memory"
    ):
        self.backend = backend or os.environ.get("MEMORY_BACKEND", "mock")
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        # Initialize backend
        if self.backend == "chromadb":
            self._init_chromadb()
        elif self.backend == "pgvector":
            self._init_pgvector()
        else:
            logger.info("Memory running in MOCK mode")
            self.backend = "mock"
            self._mock_store: Dict[str, MemoryDocument] = {}
    
    def _init_chromadb(self):
        """Initialize ChromaDB backend"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_data")
            
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir,
                anonymized_telemetry=False
            ))
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Nexus agent memory store"}
            )
            
            logger.info(f"ChromaDB initialized with collection: {self.collection_name}")
            
        except ImportError:
            logger.warning("chromadb not installed, falling back to mock mode")
            self.backend = "mock"
            self._mock_store = {}
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.backend = "mock"
            self._mock_store = {}
    
    def _init_pgvector(self):
        """Initialize pgvector backend"""
        try:
            import asyncpg
            # Will be initialized on first use
            self._pg_pool = None
            logger.info("pgvector backend configured (lazy initialization)")
        except ImportError:
            logger.warning("asyncpg not installed, falling back to mock mode")
            self.backend = "mock"
            self._mock_store = {}
    
    async def _get_pg_pool(self):
        """Get or create PostgreSQL connection pool"""
        if self._pg_pool is None:
            import asyncpg
            self._pg_pool = await asyncpg.create_pool(
                host=os.environ.get("POSTGRES_HOST", "localhost"),
                port=int(os.environ.get("POSTGRES_PORT", 5432)),
                database=os.environ.get("POSTGRES_DB", "nexus"),
                user=os.environ.get("POSTGRES_USER", "nexus"),
                password=os.environ.get("POSTGRES_PASSWORD", "nexus")
            )
            
            # Ensure table exists
            async with self._pg_pool.acquire() as conn:
                await conn.execute("""
                    CREATE EXTENSION IF NOT EXISTS vector;
                    CREATE TABLE IF NOT EXISTS nexus_memory (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        metadata JSONB,
                        embedding vector(384),
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS nexus_memory_embedding_idx 
                    ON nexus_memory USING ivfflat (embedding vector_cosine_ops);
                """)
        
        return self._pg_pool
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        In production, use a proper embedding model like sentence-transformers
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            if not hasattr(self, '_embedding_model'):
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            embedding = self._embedding_model.encode(text)
            return embedding.tolist()
        except ImportError:
            # Fallback: simple hash-based pseudo-embedding
            hash_bytes = hashlib.sha256(text.encode()).digest()
            # Convert to 384-dimensional vector (to match all-MiniLM-L6-v2)
            embedding = []
            for i in range(0, len(hash_bytes), 1):
                # Normalize to [-1, 1]
                val = (hash_bytes[i % len(hash_bytes)] / 128.0) - 1.0
                embedding.append(val)
            # Pad to 384 dimensions
            while len(embedding) < 384:
                embedding.extend(embedding[:min(384 - len(embedding), len(embedding))])
            return embedding[:384]
    
    async def add_context(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a document to memory
        
        Args:
            doc_id: Unique document identifier
            text: Document content
            metadata: Optional metadata dict
        """
        metadata = metadata or {}
        metadata["added_at"] = datetime.utcnow().isoformat()
        
        if self.backend == "chromadb":
            try:
                self.collection.upsert(
                    ids=[doc_id],
                    documents=[text],
                    metadatas=[metadata]
                )
                logger.debug(f"Added document {doc_id} to ChromaDB")
            except Exception as e:
                logger.error(f"Failed to add to ChromaDB: {e}")
        
        elif self.backend == "pgvector":
            try:
                import json
                pool = await self._get_pg_pool()
                embedding = self._generate_embedding(text)
                
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO nexus_memory (id, content, metadata, embedding)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (id) DO UPDATE SET
                            content = $2,
                            metadata = $3,
                            embedding = $4
                    """, doc_id, text, json.dumps(metadata), embedding)
                
                logger.debug(f"Added document {doc_id} to pgvector")
            except Exception as e:
                logger.error(f"Failed to add to pgvector: {e}")
        
        else:  # mock mode
            self._mock_store[doc_id] = MemoryDocument(
                id=doc_id,
                content=text,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            logger.debug(f"Added document {doc_id} to mock store")
    
    async def retrieve(
        self,
        query: str,
        n_results: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Retrieve relevant context from memory
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
        
        Returns:
            Concatenated relevant context as string
        """
        if self.backend == "chromadb":
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=filter_metadata
                )
                
                documents = results.get("documents", [[]])[0]
                if documents:
                    context = "\n\n".join([
                        f"- {doc[:500]}..." if len(doc) > 500 else f"- {doc}"
                        for doc in documents
                    ])
                    return f"RELEVANT HISTORICAL CONTEXT:\n{context}"
                return ""
            except Exception as e:
                logger.error(f"ChromaDB retrieval failed: {e}")
                return ""
        
        elif self.backend == "pgvector":
            try:
                pool = await self._get_pg_pool()
                embedding = self._generate_embedding(query)
                
                async with pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT content, 1 - (embedding <=> $1) as similarity
                        FROM nexus_memory
                        ORDER BY embedding <=> $1
                        LIMIT $2
                    """, embedding, n_results)
                
                if rows:
                    context = "\n\n".join([
                        f"- {row['content'][:500]}..." if len(row['content']) > 500 else f"- {row['content']}"
                        for row in rows
                    ])
                    return f"RELEVANT HISTORICAL CONTEXT:\n{context}"
                return ""
            except Exception as e:
                logger.error(f"pgvector retrieval failed: {e}")
                return ""
        
        else:  # mock mode
            # Simple keyword matching for mock mode
            if not self._mock_store:
                return self._get_mock_context()
            
            query_lower = query.lower()
            matches = []
            
            for doc in self._mock_store.values():
                if any(word in doc.content.lower() for word in query_lower.split()):
                    matches.append(doc.content)
            
            if matches:
                context = "\n".join([f"- {m[:500]}" for m in matches[:n_results]])
                return f"RELEVANT HISTORICAL CONTEXT:\n{context}"
            
            return self._get_mock_context()
    
    def _get_mock_context(self) -> str:
        """Generate mock context for development"""
        return """RELEVANT HISTORICAL CONTEXT:
- Previous release v1.9.0 was delayed by 2 days due to unresolved security vulnerabilities in the authentication module.
- Sprint 41 achieved 95% completion rate with all critical stories completed.
- The PROJ-87 epic had blocking issues related to database migration that were resolved by the DBA team.
- Last successful production deployment was on 2024-01-15 with zero rollbacks."""
    
    async def delete(self, doc_id: str):
        """Delete a document from memory"""
        if self.backend == "chromadb":
            try:
                self.collection.delete(ids=[doc_id])
            except Exception as e:
                logger.error(f"ChromaDB delete failed: {e}")
        
        elif self.backend == "pgvector":
            try:
                pool = await self._get_pg_pool()
                async with pool.acquire() as conn:
                    await conn.execute("DELETE FROM nexus_memory WHERE id = $1", doc_id)
            except Exception as e:
                logger.error(f"pgvector delete failed: {e}")
        
        else:
            self._mock_store.pop(doc_id, None)
    
    async def clear(self):
        """Clear all documents from memory"""
        if self.backend == "chromadb":
            try:
                # Delete and recreate collection
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Nexus agent memory store"}
                )
            except Exception as e:
                logger.error(f"ChromaDB clear failed: {e}")
        
        elif self.backend == "pgvector":
            try:
                pool = await self._get_pg_pool()
                async with pool.acquire() as conn:
                    await conn.execute("DELETE FROM nexus_memory")
            except Exception as e:
                logger.error(f"pgvector clear failed: {e}")
        
        else:
            self._mock_store.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        stats = {"backend": self.backend}
        
        if self.backend == "chromadb":
            try:
                stats["count"] = self.collection.count()
            except:
                stats["count"] = 0
        
        elif self.backend == "pgvector":
            try:
                pool = await self._get_pg_pool()
                async with pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT COUNT(*) as count FROM nexus_memory")
                    stats["count"] = row["count"]
            except:
                stats["count"] = 0
        
        else:
            stats["count"] = len(self._mock_store)
        
        return stats


class ConversationMemory:
    """
    Short-term conversation memory for maintaining context within a session
    """
    
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.conversations: Dict[str, List[Dict]] = {}
    
    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add a conversation turn"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[session_id].append(turn)
        
        # Trim to max turns
        if len(self.conversations[session_id]) > self.max_turns:
            self.conversations[session_id] = self.conversations[session_id][-self.max_turns:]
    
    def get_context(self, session_id: str) -> str:
        """Get conversation context as string"""
        if session_id not in self.conversations:
            return ""
        
        turns = self.conversations[session_id]
        return "\n".join([
            f"{t['role']}: {t['content']}"
            for t in turns
        ])
    
    def clear_session(self, session_id: str):
        """Clear a session's conversation history"""
        self.conversations.pop(session_id, None)
