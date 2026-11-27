"""Check that both newly bootstrapped lanes have no work before starting workers."""

from contextlib import closing
from pathlib import Path

from bootstrap_database import validate_local_dsn
from lane_bootstrap import LOCAL_AWS, local_environment_settings
from lane_database import validate_database_layout
from lanes import ENDPOINTS, need

QUEUE_COUNTS = (
    "ApproximateNumberOfMessages",
    "ApproximateNumberOfMessagesDelayed",
    "ApproximateNumberOfMessagesNotVisible",
)
PROOF_TABLES_ARE_EMPTY = """
SELECT NOT EXISTS (SELECT 1 FROM public.proof_requests)
   AND NOT EXISTS (SELECT 1 FROM public.proof_jobs)
   AND NOT EXISTS (SELECT 1 FROM public.proof_explanations)
   AND NOT EXISTS (SELECT 1 FROM public.proof_request_outbox)
   AND NOT EXISTS (SELECT 1 FROM public.proof_job_dispatch_outbox)
   AND NOT EXISTS (SELECT 1 FROM public.proof_clarification_dispatch_outbox)
"""


def check_database(role, url, connect):
    validate_local_dsn(url, lane=role)
    with connect(
        url,
        connect_timeout=5,
        options="-c default_transaction_read_only=on -c statement_timeout=5000",
    ) as connection:
        identity = connection.execute(
            "SELECT current_database(), current_user, inet_server_port(), pg_is_in_recovery()"
        ).fetchone()
        need(identity == ("pals", f"pals_qual_{role}", 5432, False), "local_lane_database_connection_identity_differs")
        empty = connection.execute(PROOF_TABLES_ARE_EMPTY).fetchone()
        need(empty == (True,), "lane_proof_work_must_be_empty")


def check_queues(role, client_factory):
    from botocore.config import Config

    # Use only the exact loopback LocalStack endpoint and disposable credentials.
    endpoint = f"http://127.0.0.1:{ENDPOINTS[role]['localstack']}"
    region = LOCAL_AWS["AWS_REGION"]
    names = [f"pals-local-{role}-{suffix}" for suffix in (
        "proof-jobs", "proof-jobs-dlq", "proof-requests", "proof-requests-dlq",
    )]
    with closing(client_factory(
        "sqs",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=LOCAL_AWS["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=LOCAL_AWS["AWS_SECRET_ACCESS_KEY"],
        config=Config(connect_timeout=5, read_timeout=5, proxies={}, retries={"total_max_attempts": 1}),
    )) as client:
        for queue in names:
            attrs = client.get_queue_attributes(
                QueueUrl=f"{endpoint}/000000000000/{queue}",
                AttributeNames=["QueueArn", *QUEUE_COUNTS],
            ).get("Attributes", {})
            need(
                attrs.get("QueueArn") == f"arn:aws:sqs:{region}:000000000000:{queue}",
                "exact_lane_proof_queue_required",
            )
            need(all(attrs.get(count) == "0" for count in QUEUE_COUNTS), "lane_proof_queue_must_be_empty")


def require_empty_lanes(database_layout):
    """Run after the launcher matches the two live databases and dependency containers."""
    try:
        import boto3
        import psycopg
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        raise ValueError("lane_proof_readiness_dependencies_required") from None

    layout = validate_database_layout(database_layout)
    try:
        for role, lane in layout["lanes"].items():
            environment = local_environment_settings(
                lane["local_env"], Path(lane["runtime_directory"]), role,
            )
            check_database(role, environment["PALS_HOST_DATABASE_URL"], psycopg.connect)
            check_queues(role, boto3.client)
    except (psycopg.Error, BotoCoreError, ClientError):
        raise ValueError("lane_proof_readiness_unavailable") from None
