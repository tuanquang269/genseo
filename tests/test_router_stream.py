"""Streamed writer reply parser (run_store.read_stream). Offline."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
from run_store import read_stream, RouterRetry


def sse(*events):
    out = []
    for e in events:
        out += [b'event: x\n', ('data: ' + e + '\n').encode(), b'\n']
    return out


class RouterStreamTests(unittest.TestCase):
    def test_text_and_stop_reason(self):
        lines = sse('{"type":"message_start","message":{}}', '{"type":"ping"}',
                    '{"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"x"}}',
                    '{"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"{\\"a\\":"}}',
                    '{"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":" 1}"}}',
                    '{"type":"message_delta","delta":{"stop_reason":"end_turn"}}', '{"type":"message_stop"}', '[DONE]')
        self.assertEqual(read_stream(lines), ('{"a": 1}', 'end_turn'))

    def test_cut_stream_and_error_event_retry(self):
        with self.assertRaises(RouterRetry):
            read_stream(sse('{"type":"content_block_delta","delta":{"type":"text_delta","text":"half"}}'))
        with self.assertRaises(RouterRetry):
            read_stream(sse('{"type":"error","error":{"type":"overloaded_error"}}'))


if __name__ == '__main__':
    unittest.main()
