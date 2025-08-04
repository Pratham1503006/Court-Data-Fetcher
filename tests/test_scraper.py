import unittest
from court_scraper import CourtScraper

class ScraperTestCase(unittest.TestCase):
    def test_parse_empty(self):
        scraper = CourtScraper()
        # Simulate page without results
        scraper.driver.page_source = "<html><body>No cases</body></html>"
        res = scraper._parse_results()
        self.assertFalse(res['success'])

if __name__ == '__main__':
    unittest.main()
