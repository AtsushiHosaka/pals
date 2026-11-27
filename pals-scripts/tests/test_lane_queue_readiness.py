"""Keep worker startup behind empty, exact local proof queues and databases."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local-qualification"))

import lane_queue_readiness as subject


class LaneQueueReadinessTests(unittest.TestCase):
    def test_database_identity_and_pending_work_refuse_startup(self):
        dsn = "postgresql://pals_qual_primary:fixture@127.0.0.1:55434/pals"
        connection = MagicMock()
        connect = MagicMock()
        connect.return_value.__enter__.return_value = connection
        identity = ("pals", "pals_qual_primary", 5432, False)
        for report, expected in (
            ([("pals", "old_user", 5432, False)], "local_lane_database_connection_identity_differs"),
            ([identity, (False,)], "lane_proof_work_must_be_empty"),
        ):
            with self.subTest(expected=expected):
                connection.execute.return_value.fetchone.side_effect = report
                with self.assertRaisesRegex(ValueError, expected):
                    subject.check_database("primary", dsn, connect)

        connection.execute.return_value.fetchone.side_effect = [identity, (True,)]
        subject.check_database("primary", dsn, connect)
        self.assertIn("default_transaction_read_only=on", connect.call_args.kwargs["options"])

    def test_exact_loopback_queues_refuse_missing_or_inflight_counts(self):
        queue = MagicMock()
        factory = MagicMock()
        factory.return_value = queue
        region = subject.LOCAL_AWS["AWS_REGION"]

        def attributes(*, QueueUrl, AttributeNames):
            name = QueueUrl.rsplit("/", 1)[-1]
            return {"Attributes": {
                "QueueArn": f"arn:aws:sqs:{region}:000000000000:{name}",
                **dict.fromkeys(subject.QUEUE_COUNTS, "0"),
            }}

        queue.get_queue_attributes.side_effect = attributes
        subject.check_queues("standby", factory)
        self.assertEqual(factory.call_args.kwargs["endpoint_url"], "http://127.0.0.1:54567")
        self.assertEqual(len(queue.get_queue_attributes.call_args_list), 4)
        queue.close.assert_called_once_with()

        invisible = "ApproximateNumberOfMessagesNotVisible"
        for count in (None, "1"):
            with self.subTest(count=count):
                result = attributes(
                    QueueUrl="http://127.0.0.1:54567/000000000000/pals-local-standby-proof-jobs",
                    AttributeNames=[],
                )
                if count is None:
                    del result["Attributes"][invisible]
                else:
                    result["Attributes"][invisible] = count
                queue.get_queue_attributes.side_effect = None
                queue.get_queue_attributes.return_value = result
                with self.assertRaisesRegex(ValueError, "lane_proof_queue_must_be_empty"):
                    subject.check_queues("standby", factory)


if __name__ == "__main__":
    unittest.main()
