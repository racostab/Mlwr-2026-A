
CREATE TABLE IF NOT EXISTS samples (
    sha256      TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    size        BIGINT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
    sha256     TEXT REFERENCES samples(sha256) ON DELETE CASCADE,
    kind       TEXT NOT NULL,
    payload    JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (sha256, kind)
);
