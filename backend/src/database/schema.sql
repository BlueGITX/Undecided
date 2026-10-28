
CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    skill_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100)
);

CREATE TABLE user_skills (
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    skill_id BIGINT NOT NULL REFERENCES skills(skill_id),
    skill_type VARCHAR(10) NOT NULL
        CHECK (skill_type IN ('teach', 'learn')),
    PRIMARY KEY (user_id, skill_id, skill_type)
);
