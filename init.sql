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

-- Apply trigger to document_chunks table (safe to re-run)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_chunks') THEN
        DROP TRIGGER IF EXISTS trg_chunk_search_vector ON document_chunks;
        CREATE TRIGGER trg_chunk_search_vector
        BEFORE INSERT OR UPDATE ON document_chunks
        FOR EACH ROW EXECUTE FUNCTION update_chunk_search_vector();
    END IF;
END $$;
