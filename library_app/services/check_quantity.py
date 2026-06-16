
SELECT
    a.CategoryShortName,
    a.ModelShortName,
    a.qty_on_shelf,
    ISNULL(r.requested_qty, 0) AS requested_qty,
    a.qty_on_shelf - ISNULL(r.requested_qty, 0) AS real_qty_available
FROM
(
    /* Active assets in library with no open jobs */
    SELECT
        va.CategoryShortName,
        va.ModelShortName,
        COUNT(*) AS qty_on_shelf
    FROM dbo.vbAsset AS va
    WHERE va.EquipmentStatusClassId    = 'Active'
      AND va.EquipmentLibraryStatusId  = 'WWW2'
      AND NOT EXISTS
      (
          SELECT 1
          FROM dbo.vbJob AS vj
          WHERE vj.EquipmentCode = va.EquipmentCode
            AND vj.JobStatusClassId IN ('INPROGRESS', 'NOTSTARTED', 'MISC')
      )
    GROUP BY
        va.CategoryShortName,
        va.ModelShortName
) AS a
LEFT JOIN
(
    /* Outstanding requests */
    SELECT
        vlr.CategoryShortName,
        vlr.ModelShortName,
        COUNT(*) AS requested_qty
    FROM dbo.vbLoanRequest AS vlr
    WHERE (vlr.LoanRequestStatusClassId IN ('INPROGRESS', 'UNFULFILLED')
           OR vlr.LoanRequestStatusClassId IS NULL)
    GROUP BY
        vlr.CategoryShortName,
        vlr.ModelShortName
) AS r
    ON  r.CategoryShortName = a.CategoryShortName
    AND r.ModelShortName    = a.ModelShortName
ORDER BY
    a.CategoryShortName,
    a.ModelShortName;


