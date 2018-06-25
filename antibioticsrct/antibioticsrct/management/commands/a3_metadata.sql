-- Allocation SQL designed by RCT author - see discussion here
-- https://github.com/ebmdatalab/antibiotics-rct/issues/6 and later
-- rethinking here
-- https://github.com/ebmdatalab/antibiotics-rct/issues/23

-- Find the measure, measure savings, and total savings for each
-- practice in a sample table of practices, compared to 10th centile,
-- for all of the measures where we have calculated potential savings.
-- The date range is hard coded for the third intervention, Nov-April.

WITH savings AS (

SELECT p.practice_id AS practice, s.measure AS measure, s.cost_savings, s.spend, SUM(s.cost_savings) OVER (PARTITION BY p.practice_id) AS total_savings,
ROW_NUMBER() OVER (PARTITION BY p.practice_id ORDER BY s.cost_savings DESC) AS savings_rank -- use row number so there will only be a single row per practice numbered "1"

FROM tmp_eu.{allocation_table} p

LEFT JOIN
(SELECT 'ace' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_ace`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id

UNION ALL
SELECT  'arb' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_arb`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id

UNION ALL
SELECT  'quetiapine' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_quetiapine`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id

UNION ALL
SELECT  'keppra' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_keppra`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id

UNION ALL
SELECT  'desogestrel' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_desogestrel`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id

UNION ALL
SELECT  'ppi' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_ppi`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id


UNION ALL
SELECT  'lyrica' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_lyrica`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id) s
ON p.practice_id = s.practice_id AND cost_savings > 50
WHERE allocation="I" ),

--- lp measures --------------------------------------------------------------------------------

lp AS (
SELECT  'low-priority' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, AVG(calc_value) AS calc_value FROM `ebmdatalab.measures.practice_data_lpzomnibus`
WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
GROUP BY practice_id)

---------------------------------------------------------------------------

SELECT s.*, lp.numerator AS lp_spend, lp.calc_value/1000 AS lp_cost_per_person, prac.total_list_size,
s.cost_savings/prac.total_list_size AS measures_savings_per_person, total_savings/prac.total_list_size AS total_savings_per_person,
CASE WHEN  s.total_savings/prac.total_list_size > 0.05 AND total_savings > 250  THEN s.cost_measure
ELSE "low-priority" END AS selected_measure,
CASE WHEN  s.total_savings/prac.total_list_size > 0.05 AND total_savings > 250  THEN "cost_measure"
ELSE "low-priority" END AS selected_measure_type
FROM savings s
LEFT JOIN lp ON s.practice_id = lp.practice_id
LEFT JOIN `ebmdatalab.hscic.practice_statistics` prac ON s.practice_id = prac.practice AND CAST(prac.month AS DATE) =   '2018-01-01'
WHERE savings_rank =1


ORDER BY total_savings
