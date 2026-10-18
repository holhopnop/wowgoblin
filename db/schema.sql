-- Phase 0 schema. Prices are in copper (10,000 copper = 1 gold).
CREATE TABLE IF NOT EXISTS price_snapshot (
  market        text        NOT NULL,           -- dotted id, e.g. forever.pvp.horde.us
  item_id       integer     NOT NULL,
  observed_at   timestamptz NOT NULL,           -- table timestamp from AHledger header
  median        bigint,
  min_buyout    bigint,
  quantity      bigint,
  median_7d     bigint,
  median_30d    bigint,
  low_30d       bigint,
  high_30d      bigint,
  sales_per_day numeric(10,1),                  -- estimate; NULL when unknown
  PRIMARY KEY (market, item_id, observed_at)
);
CREATE INDEX IF NOT EXISTS price_snapshot_item ON price_snapshot (market, item_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS sync_state (
  market      text PRIMARY KEY,
  etag        text,
  last_table_at timestamptz,
  last_checked_at timestamptz
);

CREATE TABLE IF NOT EXISTS item (
  item_id      integer PRIMARY KEY,
  name         text,
  quality      text,
  vendor_value integer,                          -- copper a vendor pays; NULL until fetched
  fetched_at   timestamptz
);

CREATE TABLE IF NOT EXISTS app_user (
  id            serial PRIMARY KEY,
  username      text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  discord_id    text
);

CREATE TABLE IF NOT EXISTS character (
  id         serial PRIMARY KEY,
  user_id    integer NOT NULL REFERENCES app_user(id),
  name       text NOT NULL,
  level      integer,
  UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS character_profession (
  character_id integer NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  profession   text NOT NULL,
  skill        integer NOT NULL,
  PRIMARY KEY (character_id, profession)
);

CREATE TABLE IF NOT EXISTS character_recipe (
  character_id integer NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  spell_id     integer NOT NULL,
  PRIMARY KEY (character_id, spell_id)
);

CREATE TABLE IF NOT EXISTS alert_rule (
  id         serial PRIMARY KEY,
  user_id    integer NOT NULL REFERENCES app_user(id),
  rule       jsonb NOT NULL,                     -- structured rule produced by the AI layer
  confirmed  boolean NOT NULL DEFAULT false,     -- only confirmed rules fire
  paused     boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
