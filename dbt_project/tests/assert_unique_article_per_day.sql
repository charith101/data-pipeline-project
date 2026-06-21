select
    article,
    pageview_date,
    count(*) as occurrences
from {{ ref('mart_trending_articles') }}
group by article, pageview_date
having count(*) > 1