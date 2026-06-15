-- StartupperUZ Bot — PostgreSQL schema (Railway)
-- Idempotent: safe to run on every startup.
-- Flags are SMALLINT (0/1) to match the bot's toggle logic (e.g. 1 - is_active).

CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    telegram_id     BIGINT NOT NULL UNIQUE,
    username        TEXT,
    first_name      TEXT NOT NULL,
    last_name       TEXT,
    full_name       TEXT,
    age             INTEGER,
    city            TEXT,
    profession      TEXT,
    company_name    TEXT,
    bio             TEXT,
    linkedin_url    TEXT,
    is_admin        SMALLINT DEFAULT 0,
    is_banned       SMALLINT DEFAULT 0,
    is_registered   SMALLINT DEFAULT 0,
    language_code   TEXT DEFAULT 'new',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id);

CREATE TABLE IF NOT EXISTS teammate_categories (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,
    icon        TEXT,
    description TEXT,
    is_active   SMALLINT DEFAULT 1,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teammate_requests (
    id                   BIGSERIAL PRIMARY KEY,
    user_id              BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id          BIGINT NOT NULL REFERENCES teammate_categories(id),
    custom_category      TEXT,
    title                TEXT NOT NULL,
    description          TEXT NOT NULL,
    requirements         TEXT,
    compensation_type    TEXT DEFAULT 'negotiable',
    compensation_details TEXT,
    location_type        TEXT DEFAULT 'remote',
    location_city        TEXT,
    status               TEXT DEFAULT 'pending',
    rejection_reason     TEXT,
    approved_by          BIGINT,
    approved_at          TIMESTAMP,
    channel_message_id   BIGINT,
    posted_at            TIMESTAMP,
    views_count          INTEGER DEFAULT 0,
    responses_count      INTEGER DEFAULT 0,
    expires_at           TIMESTAMP,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_requests_status ON teammate_requests (status);
CREATE INDEX IF NOT EXISTS idx_requests_created ON teammate_requests (created_at);

CREATE TABLE IF NOT EXISTS request_responses (
    id          BIGSERIAL PRIMARY KEY,
    request_id  BIGINT NOT NULL REFERENCES teammate_requests(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message     TEXT,
    status      TEXT DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (request_id, user_id)
);

CREATE TABLE IF NOT EXISTS resource_categories (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,
    icon        TEXT,
    description TEXT,
    is_active   SMALLINT DEFAULT 1,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resources (
    id            BIGSERIAL PRIMARY KEY,
    category_id   BIGINT NOT NULL REFERENCES resource_categories(id),
    title         TEXT NOT NULL,
    description   TEXT,
    content       TEXT,
    url           TEXT,
    resource_type TEXT DEFAULT 'article',
    is_featured   SMALLINT DEFAULT 0,
    is_active     SMALLINT DEFAULT 1,
    views_count   INTEGER DEFAULT 0,
    created_by    BIGINT,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS settings (
    id            BIGSERIAL PRIMARY KEY,
    setting_key   TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type  TEXT DEFAULT 'string',
    description   TEXT,
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversation_states (
    id           BIGSERIAL PRIMARY KEY,
    telegram_id  BIGINT NOT NULL UNIQUE,
    state        TEXT NOT NULL DEFAULT 'idle',
    data         JSONB,
    updated_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id               BIGSERIAL PRIMARY KEY,
    title            TEXT NOT NULL,
    description      TEXT NOT NULL,
    image_file_id    TEXT,
    event_date       TIMESTAMP NOT NULL,
    location         TEXT,
    registration_url TEXT,
    is_active        SMALLINT DEFAULT 1,
    created_by       BIGINT,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_events_date ON events (event_date);

-- ---------- Seed data ----------
INSERT INTO teammate_categories (name, slug, icon, sort_order) VALUES
    ('Designer', 'designer', '🎨', 1),
    ('Developer', 'developer', '💻', 2),
    ('Marketer', 'marketer', '📈', 3),
    ('Co-founder', 'cofounder', '🤝', 4),
    ('Other', 'other', '📝', 99)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO resource_categories (name, slug, icon, sort_order) VALUES
    ('Fundraising', 'fundraising', '💰', 1),
    ('Legal', 'legal', '⚖️', 2),
    ('Marketing', 'marketing', '📢', 3),
    ('Product', 'product', '🚀', 4),
    ('Hiring', 'hiring', '👥', 5),
    ('Tools', 'tools', '🛠️', 6)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO settings (setting_key, setting_value, setting_type, description) VALUES
    ('require_subscription', '1', 'boolean', 'Force channel subscription'),
    ('max_active_requests', '3', 'number', 'Max active requests per user'),
    ('request_expiry_days', '30', 'number', 'Days until a request expires'),
    ('admin_chat_id', '', 'string', 'Admin notification chat ID')
ON CONFLICT (setting_key) DO NOTHING;

-- ---------- Applications (/apply flow) ----------
CREATE TABLE IF NOT EXISTS applications (
    id             BIGSERIAL PRIMARY KEY,
    telegram_id    BIGINT NOT NULL,
    username       TEXT,
    q1_team        TEXT,
    q2_project     TEXT,
    q3_problem     TEXT,
    q4_why_you     TEXT,
    q5_trello      TEXT,
    q6_commitment  TEXT,
    created_at     TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_applications_created ON applications (created_at);
