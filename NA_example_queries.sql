USE data605_final_project;

SELECT *
FROM recruiters
ORDER BY recruiter_id;

SELECT *
FROM candidates
ORDER BY candidate_id;

SELECT COUNT(*) AS total_candidates
FROM candidates;

SELECT
    candidate_id,
    COUNT(*) AS duplicate_count
FROM candidates
GROUP BY candidate_id
HAVING COUNT(*) > 1;

SELECT DISTINCT month
FROM candidates
ORDER BY FIELD(
    month,
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
);

SELECT
    c.candidate_id,
    c.name,
    c.gender,
    c.date_of_birth,
    c.email,
    c.city,
    c.address,
    c.postcode,
    c.phone_number,
    c.university,
    c.degree,
    c.month,
    c.invited_by_recruiter_id,
    r.recruiter_name
FROM candidates AS c
LEFT JOIN recruiters AS r
    ON c.invited_by_recruiter_id = r.recruiter_id
ORDER BY c.candidate_id;

SELECT
    candidate_id,
    name,
    invited_by_recruiter_id
FROM candidates
WHERE invited_by_recruiter_id IS NULL;

SELECT
    r.recruiter_id,
    r.recruiter_name,
    COUNT(c.candidate_id) AS total_candidates
FROM recruiters AS r
LEFT JOIN candidates AS c
    ON r.recruiter_id = c.invited_by_recruiter_id
GROUP BY
    r.recruiter_id,
    r.recruiter_name
ORDER BY r.recruiter_id;
