from query.common import extract_time_and_context, TimeContext
import unittest
import pendulum


class TestCommonModule(unittest.TestCase):
    def test_single_time_with_context_and_timezone(self):
        sentence = "Find a restaurant open at 8 AM"
        expected = {"context": TimeContext.at, "time": "08:00", "timezone": "America/Los_Angeles"}
        self.assertEqual(
            extract_time_and_context(sentence, pendulum.now(tz="America/Los_Angeles")),
            expected,
        )

    def test_single_time_with_context_no_timezone(self):
        sentence = "Find a place open before 9 PM"
        expected = {
            "context": TimeContext.before,
            "time": "21:00",
            "timezone": "America/Los_Angeles",
        }
        self.assertEqual(
            extract_time_and_context(sentence, pendulum.now(tz="America/Los_Angeles")),
            expected,
        )

    def test_open_now(self):
        sentence = "Find a place open now"
        now = pendulum.now(tz="America/Chicago")
        expected = {
            "context": TimeContext.by,
            "time": now.strftime("%H:%M"),
            "timezone": "America/Chicago",
        }
        self.assertEqual(
            extract_time_and_context(sentence, now),
            expected,
        )

    def test_open_soon(self):
        sentence = "Find a place open soon"
        now = pendulum.now(tz="America/Chicago")
        expected = {
            "context": TimeContext.after,
            "time": now.strftime("%H:%M"),
            "timezone": "America/Chicago",
        }
        self.assertEqual(
            extract_time_and_context(sentence, now),
            expected,
        )

    def test_invalid_time(self):
        sentence = "Find places open at 25:00"
        with self.assertRaises(ValueError):
            extract_time_and_context(sentence, pendulum.now())

    def test_no_context(self):
        sentence = "Find places open 8 PM"
        expected = {"context": TimeContext.by, "time": "20:00", "timezone": "UTC"}
        self.assertEqual(extract_time_and_context(sentence, pendulum.now(tz='UTC')), expected)

        sentence = "Find places open 8PM"
        expected = {"context": TimeContext.by, "time": "20:00", "timezone": "UTC"}
        self.assertEqual(extract_time_and_context(sentence, pendulum.now(tz='UTC')), expected)

    def test_no_context_no_space_between_time_and_pm_2(self):
        sentence = "Find places open 8:00PM"
        expected = {"context": TimeContext.by, "time": "20:00", "timezone": "UTC"}
        self.assertEqual(extract_time_and_context(sentence, pendulum.now(tz='UTC')), expected)


if __name__ == "__main__":
    unittest.main()
