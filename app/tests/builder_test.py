from query.builder import (
    filter_negation_is_present,
    get_style_filter,
    get_boolean_filter,
)
import unittest


class TestBuilderModule(unittest.TestCase):
    def test_filter_negation_is_present(self):
        self.assertEqual(
            filter_negation_is_present(
                "vegetarion", "Find a non-vegetarion open at 8 AM"
            ),
            True,
        )
        self.assertEqual(
            filter_negation_is_present(
                "vegetarion", "Find a not vegetarion open at 8 AM"
            ),
            True,
        )

        self.assertEqual(
            filter_negation_is_present("vegetarion", "Find a vegetarion open at 8 AM"),
            False,
        )

    def test_get_boolean_filter(self):
        filter = get_boolean_filter(
            "vegetarion", "Find a non-vegetarion restaurant open at 8 AM"
        )
        self.assertEqual(filter, False)

        filter = get_boolean_filter(
            "vegetarion", "Find a vegetarion restaurant open at 8 AM"
        )
        self.assertEqual(filter, True)

        filter = get_boolean_filter("vegetarion", "Find a restaurant open at 8 AM")
        self.assertEqual(filter, None)

    def test_get_style_filter(self):
        filter = get_style_filter("Find an Italian French restaurant open at 8 AM")
        self.assertEqual(filter, (False, ["italian", "french"]))

        filter = get_style_filter("Find an Italian not French restaurant open at 8 AM")
        self.assertEqual(filter, (False, ["italian"]))

        filter = get_style_filter("Find an restaurant open at 8 AM")
        self.assertEqual(filter, (True, []))


if __name__ == "__main__":
    unittest.main()
