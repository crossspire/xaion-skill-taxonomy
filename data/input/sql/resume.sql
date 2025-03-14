SELECT DISTINCT
    a.name,
    a.integration_id,
    a.linkedin_id,
    a.integrated_platforms,
    a.resume,
    a.last_resume_updated
FROM
    dashboard.integrated_resume a
    LEFT JOIN dashboard.candidate_occupations co ON a.integration_id = co.integration_id
WHERE
    a.linkedin_id IS NOT NULL
    AND a.integrated_platforms = 'linkedin'
    AND co.occupation_id IN (
        '040102',
        '040103',
        '040104',
        '040105',
        '040106',
        '040107',
        '040108',
        '040201',
        '040202',
        '040301',
        '040401',
        '040402',
        '040403',
        '040404',
        '040405',
        '040501',
        '040502',
        '040503',
        '040504',
        '040505',
        '040506',
        '040601',
        '040602',
        '040603',
        '040604'
    )
ORDER BY
    a.last_resume_updated DESC
LIMIT
    10000;