
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS user_skills (
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    skill_id BIGINT NOT NULL REFERENCES skills(skill_id),
    skill_type VARCHAR(10) NOT NULL
        CHECK (skill_type IN ('teach', 'learn')),
    PRIMARY KEY (user_id, skill_id, skill_type)
);


CREATE TABLE IF NOT EXISTS exchange_requests (
    request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    learner_id BIGINT NOT NULL REFERENCES users(user_id),
    teacher_id BIGINT NOT NULL REFERENCES users(user_id),
    skill_id BIGINT NOT NULL REFERENCES skills(skill_id),

    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'accepted',
            'rejected',
            'completed',
            'cancelled'
        )),

    request_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (learner_id <> teacher_id)
);

