-- Find the measure, measure savings, and total savings for each
-- practice in a sample table of practices, compared to 10th centile,
-- for all of the measures where we have calculated potential savings.
-- The date range is hard coded for the third intervention, Nov-April.

SELECT
  *
FROM (
  SELECT
    practice,
    measure,
    cost_savings,
    spend,
    SUM(cost_savings) OVER (PARTITION BY practice) AS total_savings,
    ROW_NUMBER() OVER (PARTITION BY practice ORDER BY cost_savings DESC) AS measure_rank -- use row number so there will only be a single row per practice numbered "1"
  FROM
    tmp_eu.{allocation_table} p
  LEFT JOIN (
    SELECT
      'ace' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_ace`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
    UNION ALL
    SELECT
      'arb' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_arb`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
    UNION ALL
    SELECT
      'quetiapine' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_quetiapine`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
    UNION ALL
    SELECT
      'keppra' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_keppra`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
    UNION ALL
    SELECT
      'desogestrel' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_desogestrel`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
    UNION ALL
    SELECT
      'ppi' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_ppi`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
    UNION ALL
    SELECT
      'statins' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_statins`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
    UNION ALL
    SELECT
      'lyrica' AS measure,
      practice_id,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,
          0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_lyrica`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id ) m
  ON
    p.practice = m.practice_id
  WHERE
    cost_savings >0 )
WHERE
  measure_rank =1
-- p [row for row in client.list_rows(table)]
