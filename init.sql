-- PostgreSQL FTS extensions (built-in, just ensure they're available)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Auto-update tsvector on document_chunks insert/update
CREATE OR REPLACE FUNCTION update_chunk_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', NEW.chunk_text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
