CREATE TABLE IF NOT EXISTS tags
(
    name      TEXT PRIMARY KEY,
    color     TEXT,
    last_used TIMESTAMP
);

CREATE TABLE IF NOT EXISTS members
(
    member_name TEXT,
    tag_name    TEXT REFERENCES tags (name) ON DELETE CASCADE,
    PRIMARY KEY (member_name, tag_name)
);

INSERT OR IGNORE INTO tags (name, color, last_used)
VALUES ('red', '#ff0000', '2019-01-01');
INSERT OR IGNORE INTO tags (name, color, last_used)
VALUES ('green', '#00ff00', '2019-01-01');
INSERT OR IGNORE INTO tags (name, color, last_used)
VALUES ('blue', '#0000ff', '2019-01-01');


INSERT OR IGNORE INTO members (member_name, tag_name)
VALUES ('Alice', 'red');
INSERT OR IGNORE INTO members (member_name, tag_name)
VALUES ('Bob', 'red');
INSERT OR IGNORE INTO members (member_name, tag_name)
VALUES ('Charlie', 'green');
INSERT OR IGNORE INTO members (member_name, tag_name)
VALUES ('David', 'blue');

SELECT *
FROM members
WHERE tag_name = 'red';

UPDATE tags
SET last_used = '2022-01-01'
WHERE name = 'red';