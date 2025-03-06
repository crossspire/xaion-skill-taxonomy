select
    name,
    integration_id,
    linkedin_id,
    integrated_platforms,
    resume
from
    dashboard.integrated_resume
where
    linkedin_id is not null
    and integrated_platforms = 'linkedin'
order by
    last_resume_updated desc
limit
    10000