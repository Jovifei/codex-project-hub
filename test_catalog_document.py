import json,unittest
from pathlib import Path

class CatalogDocumentTests(unittest.TestCase):
 def test_authorized_catalog_is_read_only_unconfirmed_and_separate_from_demo(self):
  data=json.loads(Path('docs/PROJECT_CATALOG_20261025.json').read_text(encoding='utf-8'))
  legacy={'jovi-automation','ai-photography-director-app','nightly-photo-intelligence-pipeline','openclaw-videofactory','star-photo-addr','matelink','etf-fund-analysis','tesla-speed','medcial-box'}
  self.assertEqual(data['candidate_count'],12);self.assertEqual(len(data['projects']),12);self.assertFalse(data['auto_import']);self.assertTrue(legacy<={p['id'] for p in data['projects']})
  for p in data['projects']:
   self.assertEqual(p['current_stage'],'unknown');self.assertEqual(p['execution_status'],'unknown');self.assertIsNone(p['completion_percentage']);self.assertNotEqual(p['goal_status'],'confirmed');self.assertIn(p['head_sha'],p['evidence_url']);self.assertLessEqual(len(p['open_prs']['items']),2)
  seed=json.loads(Path('seed.json').read_text(encoding='utf-8'));self.assertEqual(len(seed),9);self.assertTrue(all(p['project_id'].startswith('example-') for p in seed))

if __name__=='__main__':unittest.main()
