WITH monthly_yield AS (
    SELECT
        EXTRACT(year FROM MAX(sample)) AS year,
        EXTRACT(month FROM MAX(sample)) AS month,
        MAX(yield_total) - MIN(yield_total) AS yield
    FROM
        sems_fixed AS sems
    GROUP BY to_char(sems.sample, 'YYYY-MM')
    ),
    yearly_yield AS (
    SELECT
        EXTRACT(year FROM sample) AS year,
        MAX(yield_total) - MIN(yield_total) AS yield
    FROM sems_fixed AS sems
    GROUP BY EXTRACT(year FROM sample)
    )


SELECT 
    y_2021.month AS month,
    CONCAT(y_2021.yield,'(', ROUND(y_2021.yield/9.495,1),')') AS "2021",
    CONCAT(y_2022.yield,'(', ROUND(y_2022.yield/9.495,1),')') AS "2022"
FROM 
    monthly_yield AS y_2021
LEFT JOIN 
    monthly_yield AS y_2022 ON y_2022.month = y_2021.month AND y_2022.year=2022
WHERE 
    y_2021.year=2021

UNION
SELECT
    null AS month,
    CONCAT(yy_2021.yield, '(',ROUND(yy_2021.yield/9.495,2),')') AS "2021",
    CONCAT(yy_2022.yield, '(',ROUND(yy_2022.yield/9.495,2),')') AS "2022"
FROM yearly_yield as yy_2021
JOIN yearly_yield as yy_2022 ON yy_2022.year=2022
WHERE yy_2021.year=2021
ORDER BY month asc

