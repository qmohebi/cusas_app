import json
import logging

from django.db import connections

# logger = logging.getLogger(__name__)

# qJobPostProcessing stored procedure for eQuip job cleanup

def get_child_assets(parent_id: str, *, connection=None) -> list[dict]:
    """Fetchs the children of an asset,
    handles None where no child, handles bad json format
    params: parent_id"""

    conn = connection or connections["equip"]

    with conn.cursor() as cursor:
        cursor.execute("EXEC US_GetChildAssets @Parentid =%s", [parent_id])

        result = cursor.fetchone()

        if not result:
            logging.error(
                "US_GetChildAssets returned no row for ParentId=%r", parent_id
            )
            return []

        raw_json = result[0]

        if raw_json is None:
            logging.info("No child asset for pareintId=%r", parent_id)
            return []

        text = str(raw_json).strip()

        if not text.startswith("["):
            text = f"[{text}]"

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logging.error(
                "JSON decode error from US_GetChildAssets for ParentId=%r: %s; raw=%r",
                parent_id,
                e,
                raw_json,
            )
            return []

        if not isinstance(data, list):
            logging.warning(
                "Expected list from US_GetChildAssets for ParentId=%r, got %r",
                parent_id,
                type(data),
            )
            return []
        return data


def create_repair_job(
    equipment_id: str,
    reported_fault: str,
    caller_fullname: str = None,
    *,
    connection=None,
) -> str:
    """
    This creates a job number for a given asset
    and returns the job that is created on eQuip

    :param equipment_id: of the device
    :type asset_number: str
    :param reported_fault: what needs to be reported
    :type reported_fault: str
    :param caller: Caller's full name
    :type: Authenticated user instance
    :return: eQuip job number
    :rtype: str
    """

    conn = connection or connections["equip"]

    with conn.cursor() as cursor:
        cursor.execute(
            "EXEC CUSAS_APP_create_job @EquipmentId=%s, @ReportedFault=%s, @caller=%s",
            [equipment_id, reported_fault, caller_fullname],
        )
        row = cursor.fetchone()
    return row[0] if row else None


def get_job_details(job_no: str, connection=None) -> list:
    """
    gets the job details from the equip database for
    a given job.

    :param job_no:equip job number
    :type job_no: str
    :return: information about the job such as work done, job status
    :rtype: list
    """

    conn = connection or connections["equip"]

    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT 
                vbJob.JobStatusShortName, vbJob.WorkDone 
            FROM 
                vbJob 
            WHERE vbjob.JobCode =%s""",
            [job_no],
        )

        return cursor.fetchall()
