import hashlib,unittest
from pathlib import Path

def parse_manifest(text):
 entries={}
 for line in text.splitlines():
  line=line.strip()
  if not line or line.startswith('#'): continue
  digest,_,name=line.partition(' ')
  entries[name.strip().lstrip('*')]=digest
 return entries

class ManifestTests(unittest.TestCase):
 def test_manifest_entries_exist_and_match_modulo_line_endings(self):
  entries=parse_manifest(Path('MANIFEST.sha256').read_text(encoding='utf-8'))
  self.assertTrue(entries)
  for name,digest in entries.items():
   data=Path(name).read_bytes()
   raw=hashlib.sha256(data).hexdigest()
   normalized=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
   self.assertTrue(raw==digest or normalized==digest,msg=name)

if __name__=='__main__':unittest.main()
