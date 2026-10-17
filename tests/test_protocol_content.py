"""Targeted clinical wording regressions against the linked primary sources."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('manage_protocol_content', ROOT / 'scripts/manage.py')
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


class ProtocolContentTests(unittest.TestCase):
    def test_pluvicto_four_week_stop_rule_is_limited_to_adverse_reaction_delays(self):
        # EMA Pluvicto SmPC 4.2: the >4-week discontinuation rule concerns an
        # adverse-reaction delay, not every logistical or other postponement.
        cases, _ = manage.load_and_validate(ROOT)
        regimen = next(r for e in manage.load_protocols(ROOT, cases)
                       for r in e['regimens'] if r['id'] == 'pca-lu177-psma-617')
        patterns = {
            'en': r'delay due to an adverse reaction.*more than 4 weeks',
            'de': r'Verschiebung wegen einer Nebenwirkung.*mehr als 4 Wochen',
            'es': r'retraso debido a una reacción adversa.*más de 4 semanas',
        }
        for language, pattern in patterns.items():
            with self.subTest(language=language):
                self.assertRegex(regimen['cautions'][language], pattern)
        self.assertIn('https://www.ema.europa.eu/en/documents/product-information/'
                      'pluvicto-epar-product-information_en.pdf',
                      [source['url'] for source in regimen['sources']])


if __name__ == '__main__':
    unittest.main()
