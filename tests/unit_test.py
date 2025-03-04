import unittest
import tempfile
import os
import json
import re
import pandas as pd
import sys
import time
from unittest.mock import patch, MagicMock
from google.protobuf import empty_pb2
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from log_parser import (
    load_log_file,
    get_clock_rate,
    parse_machine_log,
    main,
    TIMESTAMP_PATTERN
)
import system_pb2
from machine import Machine

class TestLogParser(unittest.TestCase):

    def test_timestamp_pattern_normal(self):
        """Test the timestamp regex on a valid timestamp."""
        line = "2025-03-04 00:20:34 - [INIT] with clock rate 3"
        match = TIMESTAMP_PATTERN.search(line)
        self.assertIsNotNone(match, "Should match a valid timestamp.")
        self.assertEqual(match.group(0), "2025-03-04 00:20:34")

    def test_timestamp_pattern_fail(self):
        """Test the timestamp regex on an invalid timestamp."""
        line = "InvalidTimestamp - [INIT] with clock rate 3"
        match = TIMESTAMP_PATTERN.search(line)
        self.assertIsNone(match, "Should not match an invalid timestamp format.")

    # -------------------------------------------------------------------------
    # Tests for load_log_file
    # -------------------------------------------------------------------------
    def test_load_log_file_normal(self):
        """Test loading a file with expected lines."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            temp.write("line1\nline2\n")
            temp_path = temp.name

        try:
            lines = load_log_file(temp_path)
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0].strip(), "line1")
            self.assertEqual(lines[1].strip(), "line2")
        finally:
            os.remove(temp_path)

    def test_load_log_file_empty(self):
        """Test loading an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            temp_path = temp.name

        try:
            lines = load_log_file(temp_path)
            self.assertEqual(len(lines), 0)
        finally:
            os.remove(temp_path)

    def test_load_log_file_non_existent(self):
        """Test loading a file that doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            load_log_file("non_existent.log")

    # -------------------------------------------------------------------------
    # Tests for get_clock_rate
    # -------------------------------------------------------------------------
    def test_get_clock_rate_normal(self):
        """Test extracting a valid clock rate from an INIT line."""
        line = "2025-03-04 00:20:34 - [INIT] with clock rate 3 and peers..."
        match = get_clock_rate(line)
        self.assertIsNotNone(match, "Should match clock rate pattern.")
        self.assertEqual(match.group(1), "3")

    def test_get_clock_rate_no_match(self):
        """Test with an INIT line that doesn't contain clock rate info."""
        line = "2025-03-04 00:20:34 - [INIT] no clock rate here"
        match = get_clock_rate(line)
        self.assertIsNone(match, "Should return None if pattern not found.")

    def test_get_clock_rate_boundary(self):
        """Test with an edge clock rate (e.g., 0)."""
        line = "2025-03-04 00:20:34 - [INIT] with clock rate 0 and peers..."
        match = get_clock_rate(line)
        self.assertIsNotNone(match, "Should match even if rate is 0.")
        self.assertEqual(match.group(1), "0")

    # -------------------------------------------------------------------------
    # Tests for parse_machine_log
    # -------------------------------------------------------------------------
    def test_parse_machine_log_normal(self):
        """Test parsing a normal machine log with SENT, RECEIVED, INTERNAL ops."""
        lines = [
            "2025-03-04 00:20:34 - [SENT] to Machine 2, Logical clock: 0",
            "2025-03-04 00:20:35 - [RECEIVED] from Machine 1, Logical clock: 2, Queue length: 1",
            "2025-03-04 00:20:36 - [INTERNAL], Logical clock: 3"
        ]
        df = parse_machine_log(lines)
        self.assertEqual(len(df), 3)

        # Check row 0
        self.assertEqual(df.loc[0, "timestamp"], "2025-03-04 00:20:34")
        self.assertEqual(df.loc[0, "operation"], "SENT")
        self.assertEqual(df.loc[0, "logical_clock"], 0)
        self.assertEqual(df.loc[0, "queue_length"], 0)

        # Check row 1
        self.assertEqual(df.loc[1, "timestamp"], "2025-03-04 00:20:35")
        self.assertEqual(df.loc[1, "operation"], "RECEIVED")
        self.assertEqual(df.loc[1, "logical_clock"], 2)
        self.assertEqual(df.loc[1, "queue_length"], 1)

    def test_parse_machine_log_bad_timestamp(self):
        """Test parsing a log with a bad/invalid timestamp."""
        lines = ["bad_timestamp - [SENT] to Machine 2, Logical clock: 0"]
        with self.assertRaises(AttributeError):
            # TIMESTAMP_PATTERN.search(l).group(0) will fail.
            parse_machine_log(lines)

    # -------------------------------------------------------------------------
    # Tests for main
    # -------------------------------------------------------------------------
    def test_main_normal(self):
        """
        End-to-end test for the 'main' function:
        Creates temporary log files for 3 machines, calls 'main', 
        then checks if CSV and JSON outputs are as expected.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample log files
            m0_log = os.path.join(temp_dir, "machine_0.log")
            m1_log = os.path.join(temp_dir, "machine_1.log")
            m2_log = os.path.join(temp_dir, "machine_2.log")

            # Write sample logs
            with open(m0_log, "w") as f:
                f.write("2025-03-04 00:20:34 - [INIT] with clock rate 3 and peers...\n")
                f.write("2025-03-04 00:20:35 - [SENT] to Machine 2, Logical clock: 1\n")

            with open(m1_log, "w") as f:
                f.write("2025-03-04 00:20:34 - [INIT] with clock rate 4 and peers...\n")
                f.write("2025-03-04 00:20:36 - [RECEIVED] from Machine 2, Logical clock: 2, Queue length: 1\n")

            with open(m2_log, "w") as f:
                f.write("2025-03-04 00:20:34 - [INIT] with clock rate 5 and peers...\n")
                f.write("2025-03-04 00:20:37 - [INTERNAL], Logical clock: 3\n")

            # Invoke main
            main(temp_dir)

            # Check clock_rates.json
            clock_rate_file = os.path.join(temp_dir, "clock_rates.json")
            self.assertTrue(os.path.exists(clock_rate_file), "clock_rates.json should be created.")

            with open(clock_rate_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data["machine_0"], 3)
            self.assertEqual(data["machine_1"], 4)
            self.assertEqual(data["machine_2"], 5)

            # Check generated CSVs
            for i in range(3):
                csv_file = os.path.join(temp_dir, f"machine_{i}.csv")
                self.assertTrue(os.path.exists(csv_file), f"machine_{i}.csv should be created.")
                df = pd.read_csv(csv_file)
                # For a quick sanity check, ensure it's not empty
                self.assertFalse(df.empty, f"CSV for machine_{i} should not be empty.")

    def test_main_missing_file(self):
        """
        Test that 'main' fails if one of the log files is missing.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create only machine_0.log and machine_1.log
            m0_log = os.path.join(temp_dir, "machine_0.log")
            m1_log = os.path.join(temp_dir, "machine_1.log")

            # Write sample logs (missing machine_2.log on purpose)
            with open(m0_log, "w") as f:
                f.write("2025-03-04 00:20:34 - [INIT] with clock rate 3\n")

            with open(m1_log, "w") as f:
                f.write("2025-03-04 00:20:34 - [INIT] with clock rate 4\n")

            # Expect FileNotFoundError for machine_2.log
            with self.assertRaises(FileNotFoundError):
                main(temp_dir)

class TestMachine(unittest.TestCase):
    def setUp(self):
        """
        Create a temporary directory for logs.
        Instantiate a Machine object in a 'normal' configuration.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # We'll use a normal clock rate of 2, one peer, etc.
        self.machine = Machine(
            machine_id=0,
            port="50051",
            clock_rate=2,
            peers=["localhost:50052"],
            peers_id=[1],
            log_path=self.temp_dir.name
        )

    def tearDown(self):
        """Clean up any temporary files/directories."""
        self.temp_dir.cleanup()
    
    # -------------------------------------------------------------------------
    # Test __init__ (normal, edge, and failing scenarios)
    # -------------------------------------------------------------------------
    def test_init_normal(self):
        """
        Test that Machine is initialized with expected properties (normal case).
        """
        self.assertEqual(self.machine.machine_id, 0)
        self.assertEqual(self.machine.port, "50051")
        self.assertEqual(self.machine.clock_rate, 2)
        self.assertEqual(self.machine.peers, ["localhost:50052"])
        self.assertEqual(self.machine.peers_id, [1])
        self.assertTrue(os.path.exists(self.temp_dir.name))
        self.assertIsNotNone(self.machine.logger)
        self.assertFalse(self.machine.running, "Machine should not be running at initialization.")
        self.assertEqual(self.machine.logical_clock, 0, "Logical clock should start at 0.")
    
    def test_init_edge_zero_clock_rate(self):
        """
        Edge case: Initialize with clock_rate = 0.
        That means cycle_time = 1 / 0 => Infinity or error.
        """
        # Expect a ZeroDivisionError or some similar problem if not handled.
        with self.assertRaises(ZeroDivisionError):
            _ = Machine(
                machine_id=1,
                port="50052",
                clock_rate=0,  # Edge
                peers=[],
                peers_id=[],
                log_path=self.temp_dir.name
            )

    def test_init_invalid_log_path(self):
        """
        Purposely failing scenario: Provide an invalid log_path (e.g., no write permission).
        Note: This test is tricky on certain OS setups. We'll simulate by mocking os.makedirs.
        """
        with patch("os.makedirs", side_effect=PermissionError("No permission")):
            with self.assertRaises(PermissionError):
                Machine(
                    machine_id=2,
                    port="50053",
                    clock_rate=2,
                    peers=[],
                    peers_id=[],
                    log_path="/root/forbidden_path"  # Usually restricted on Unix
                )

    # -------------------------------------------------------------------------
    # Test SendMessage (unary call handler)
    # -------------------------------------------------------------------------
    def test_SendMessage_normal(self):
        """
        Normal scenario: SendMessage should enqueue the message in message_queue.
        """
        request = system_pb2.Message(sender_id=1, logical_clock=10)
        context = MagicMock()
        self.machine.SendMessage(request, context)

        # The queue should now have 1 message
        self.assertFalse(self.machine.message_queue.empty())
        queued_msg = self.machine.message_queue.get()
        self.assertEqual(queued_msg.sender_id, 1)
        self.assertEqual(queued_msg.logical_clock, 10)

    def test_ReceiveMessages_no_message(self):
        """
        Edge case: If there is no last_sent_message, the generator should eventually yield nothing.
        We'll stop after a short time to avoid an infinite loop.
        """
        context = MagicMock()
        # We'll mock the _stop_event after a short wait to break the loop
        def stop_after_delay():
            time.sleep(0.1)
            self.machine._stop_event.set()

        t = unittest.mock.Mock()
        t.side_effect = stop_after_delay()
        
        # Start iteration
        generator = self.machine.ReceiveMessages(empty_pb2.Empty(), context)
        
        # Because we set the stop event quickly, we expect no messages
        responses = list(generator)
        self.assertEqual(len(responses), 0, "No messages should be yielded if last_sent_message is None.")

    # -------------------------------------------------------------------------
    # Test _start_server
    # -------------------------------------------------------------------------
    @patch("grpc.server")
    def test__start_server_normal(self, mock_grpc_server):
        """
        Normal scenario: _start_server should create a server, add servicer, 
        start server, connect to peers, etc.
        """
        mock_server_instance = MagicMock()
        mock_grpc_server.return_value = mock_server_instance
        
        with patch("grpc.insecure_channel") as mock_channel:
            stub_mock = MagicMock()
            # Return value for the stub
            mock_stub = MagicMock()
            stub_mock.PeerServiceStub.return_value = mock_stub
            
            # Actually patch the real "system_pb2_grpc.PeerServiceStub"
            with patch("system_pb2_grpc.PeerServiceStub", return_value=stub_mock):
                self.machine._start_server()

        # Check that a server was indeed created and started
        mock_grpc_server.assert_called_once()
        mock_server_instance.add_insecure_port.assert_called_with("[::]:50051")
        mock_server_instance.start.assert_called_once()

        # Check that we connected to peers
        mock_channel.assert_called_with("localhost:50052")
        self.assertTrue(self.machine.running, "Machine.running should be True after _start_server.")

    def test__send_message_out_of_range(self):
        """
        Purposely failing: if we call _send_message(5) but only 1 stub, it should raise an IndexError.
        """
        with self.assertRaises(IndexError):
            self.machine._send_message(5)

    # -------------------------------------------------------------------------
    # Test _receive_from_peer
    # -------------------------------------------------------------------------
    def test__receive_from_peer_normal(self):
        """
        Normal scenario: The stub yields messages, and we enqueue them.
        We'll stop after a short delay to avoid infinite loop.
        """
        stub = MagicMock()
        # Simulate a generator that yields 2 messages, then breaks
        stub.ReceiveMessages.return_value = [
            system_pb2.Message(sender_id=1, logical_clock=10),
            system_pb2.Message(sender_id=1, logical_clock=11),
        ]

        def stop_event_after_delay():
            time.sleep(0.01)
            self.machine._stop_event.set()
        
        with patch("time.sleep", side_effect=stop_event_after_delay):
            t = self.machine._receive_from_peer(stub)
            # This runs inline, but in real usage it's a thread
            # After the loop ends, message_queue should have 2 items
            self.assertFalse(self.machine.message_queue.empty())
            msg1 = self.machine.message_queue.get()
            msg2 = self.machine.message_queue.get()
            self.assertEqual(msg1.logical_clock, 10)
            self.assertEqual(msg2.logical_clock, 11)

    # -------------------------------------------------------------------------
    # Test stop
    # -------------------------------------------------------------------------
    def test_stop_normal(self):
        """
        Normal scenario: Calling stop() sets running=False, sets the event, and closes channels.
        """
        # Fake channels
        ch1 = MagicMock()
        self.machine._channels.append(ch1)
        # Start it “running”
        self.machine.running = True
        self.machine.stop()
        self.assertFalse(self.machine.running, "Machine.running should be False after stop.")
        self.assertTrue(self.machine._stop_event.is_set(), "_stop_event should be set.")
        ch1.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()