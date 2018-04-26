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
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_ace`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'arb' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_arb`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'quetiapine' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_quetiapine`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'keppra' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_keppra`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'desogestrel' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_desogestrel`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'ppi' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_ppi`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id
      --UNION ALL
      --SELECT  'statins' as measure, practice_id, AVG(percentile) AS avg_percentile, SUM(numerator) as numerator, SUM(denominator) AS denominator, SUM(cost_savings_10) AS cost_savings, SUM(COALESCE(num_cost,0)) AS spend FROM `ebmdatalab.measures.practice_data_statins`
      --WHERE month BETWEEN '2017-11-01' AND '2018-04-01'
      --GROUP BY practice_id
      UNION ALL
    SELECT
      'lyrica' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator,
      SUM(cost_savings_10) AS cost_savings,
      SUM(COALESCE(num_cost,0)) AS spend
    FROM
      `ebmdatalab.measures.practice_data_lyrica`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id) s
  ON
    p.practice_id = s.practice_id
    AND cost_savings > 300 ),
  -- non-cost measures ----------------------------------------------------------------------------
  measures AS (
  SELECT
    p.practice_id,
    m.measure AS non_cost_measure,
    m.avg_percentile,
    m.numerator,
    m.denominator,
    m.measure,
    ROW_NUMBER() OVER (PARTITION BY p.practice_id ORDER BY m.avg_percentile DESC) AS percentile_rank
  FROM
    ebmdatalab.helen.allocated_pracs_for_cephs_test p
  LEFT JOIN (
    SELECT
      'ciclosporin' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_ciclosporin`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'coproxamol' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_coproxamol`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'desogestrel' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_desogestrel`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'diltiazem' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_diltiazem`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'dipyridamole' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_dipyridamole`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'fungal' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_fungal`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'glaucoma' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_glaucoma`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'icsdose' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_icsdose`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'ktt12_diabetes_insulin' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_ktt12_diabetes_insulin`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'ktt13_nsaids_ibuprofen' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_ktt13_nsaids_ibuprofen`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'lipid_modifying_drugs' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_ktt3_lipid_modifying_drugs`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'methotrexate' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_methotrexate`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'nebivolol' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_nebivolol`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'opioidome' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_opioidome`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'opioidper1000' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_opioidper1000`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'opioidspercent' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_opioidspercent`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'ppidose' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_ppidose`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'saba' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_saba`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'silver' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_silver`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'solublepara' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_solublepara`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'statinintensity' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_statinintensity`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'tramadol' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_tramadol`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id UNION ALL
    SELECT
      'vitb' AS measure,
      practice_id,
      AVG(percentile) AS avg_percentile,
      SUM(numerator) AS numerator,
      SUM(denominator) AS denominator
    FROM
      `ebmdatalab.measures.practice_data_vitb`
    WHERE
      month BETWEEN '2017-11-01'
      AND '2018-04-01'
    GROUP BY
      practice_id ) m
  ON
    p.practice_id = m.practice_id
  WHERE
    numerator > 6 )
