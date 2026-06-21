with staged as (
    select * from {{ ref('stg_wiki_pageviews') }}
),

with_baseline as (
    select
        article,
        pageview_date,
        views,
        page_rank,

        -- TODO: each article's average `views` over its own previous 7 rows,
        -- NOT including today.
        -- Use: AVG(views) OVER (PARTITION BY <the article column> ORDER BY
        -- <the date column> ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING)
        AVG(views) OVER (PARTITION BY article ORDER BY pageview_date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) as baseline_avg_views

    from staged
)

select
    article,
    pageview_date,
    views,
    page_rank,
    baseline_avg_views,
    case
        when baseline_avg_views is null then null
        else round((views - baseline_avg_views) / baseline_avg_views * 100, 1)
    end as pct_change_vs_baseline
from with_baseline
order by pageview_date desc, views desc