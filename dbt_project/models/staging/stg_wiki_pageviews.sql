with source as (
    select * from {{ source('raw_pipeline', 'wiki_top_pageviews') }}
),

deduped as (
    select
        article,
        views,
        rank,
        pageview_date,
        loaded_at,

        -- TODO: number rows so the most-recently-loaded record per
        -- (article, pageview_date) gets row_num = 1.
        -- Use: ROW_NUMBER() OVER (PARTITION BY <the 2 columns that
        -- together identify a unique article-day> ORDER BY <the column
        -- showing when each row was loaded, newest first>)
        ROW_NUMBER() OVER (PARTITION BY article, pageview_date ORDER BY loaded_at desc) as row_num

    from source
)

select
    article,
    views,
    rank as page_rank,  -- renamed: `rank` is a reserved SQL keyword in BigQuery
    pageview_date,
    loaded_at
from deduped
where row_num = 1