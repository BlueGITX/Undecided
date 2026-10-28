
INSERT INTO skills (skill_name, category)
VALUES
    ('Python Programming', 'Technology'),
    ('Web Development', 'Technology'),
    ('Graphic Design', 'Design'),
    ('English', 'Languages'),
    ('Photography', 'Creative Arts'),
    ('Mathematics', 'Academics')
ON CONFLICT (skill_name) DO NOTHING;
