DROP TABLE IF EXISTS TOPICS;
DROP TABLE IF EXISTS PAPERS;
DROP TABLE IF EXISTS QUESTIONS;
DROP TABLE IF EXISTS MARKSCHEMES;
DROP TABLE IF EXISTS QUESTIONTOPICS;

CREATE TABLE TOPICS (
    topic_id            INTEGER PRIMARY KEY AUTOINCREMENT
                                UNIQUE
                                NOT NULL,
    main_topic_name     TEXT    NOT NULL,
    sub_topic_name      TEXT    NOT NULL,
    AS_or_A2            BOOLEAN NOT NULL -- 0: AS, 1: A2
);

CREATE TABLE PAPERS (
    paper_id TEXT    PRIMARY KEY
                     UNIQUE
                     NOT NULL,
    year     INTEGER NOT NULL
                     CHECK (year >= 21 AND
                            year <= 99),
    series   TEXT    CHECK (series = 's' OR
                            series = 'w' OR
                            series = 'm') 
                     NOT NULL,
    paper    INTEGER CHECK (paper <= 4 AND
                            paper >= 1) 
                     NOT NULL,
    variant  INTEGER CHECK (variant >= 1 AND
                            variant <= 3) 
                     NOT NULL
);

CREATE TABLE QUESTIONS (
    question_id     INTEGER PRIMARY KEY
                            UNIQUE
                            NOT NULL,
    paper_id        TEXT    REFERENCES PAPERS (paper_id) 
                            NOT NULL,
    image           BLOB    NOT NULL,
    primary_index   INTEGER NOT NULL,
    secondary_index INTEGER NOT NULL
);

CREATE TABLE MARKSCHEMES (
    ms_id       INTEGER PRIMARY KEY AUTOINCREMENT
                        NOT NULL
                        UNIQUE,
    question_id INTEGER REFERENCES QUESTIONS (question_id),
    image       BLOB    NOT NULL
);

CREATE TABLE QUESTIONTOPICS (
    question_id INTEGER REFERENCES QUESTIONS (question_id) 
                        NOT NULL,
    topic_id    INTEGER REFERENCES TOPICS (topic_id) 
                        NOT NULL,
    PRIMARY KEY (
        question_id,
        topic_id
    )
);
