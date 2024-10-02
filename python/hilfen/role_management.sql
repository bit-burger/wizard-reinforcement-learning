drop table if exists tags;
drop table if exists tag_members;
drop table if exists roles;
drop table if exists role_members;

-- Tags: Rollen die nicht in Discord, sondern nur in der Datenbank sind
CREATE TABLE IF NOT EXISTS tags
(
    name  TEXT PRIMARY KEY,
    color TEXT
);

-- Members: 'n zu m'-Beziehung zwischen Usern und Tags
CREATE TABLE IF NOT EXISTS tag_members
(
    dc_userid INT,
    tag_name  TEXT REFERENCES tags (name) ON DELETE CASCADE,
    PRIMARY KEY (dc_userid, tag_name)
);

-- Roles: Rollen die in Discord sind und wann sie zuletzt verwendet wurden
CREATE TABLE IF NOT EXISTS roles
(
    name      TEXT PRIMARY KEY,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO tags (name, color)
VALUES ('red', '#ff0000');
INSERT OR IGNORE INTO tags (name, color)
VALUES ('green', '#00ff00');
INSERT OR IGNORE INTO tags (name, color)
VALUES ('blue', '#0000ff');

INSERT OR IGNORE INTO tag_members (dc_userid, tag_name)
VALUES (1, 'red');
INSERT OR IGNORE INTO tag_members (dc_userid, tag_name)
VALUES (2, 'red');
INSERT OR IGNORE INTO tag_members (dc_userid, tag_name)
VALUES (3, 'green');
INSERT OR IGNORE INTO tag_members (dc_userid, tag_name)
VALUES (4, 'blue');

INSERT OR IGNORE INTO roles (name, last_used)
VALUES ('yellow', '2018-01-01');
INSERT OR IGNORE INTO roles (name, last_used)
VALUES ('magenta', '2018-01-01');
INSERT OR IGNORE INTO roles (name, last_used)
VALUES ('black', '2018-01-01');