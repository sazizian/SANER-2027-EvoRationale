"""Raw-byte manifest tests, including line-ending and path failures."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC=importlib.util.spec_from_file_location('export_verify_bundle',Path(__file__).parents[1]/'verify_bundle.py')
VERIFY=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)

class ExportByteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.raw=b'first\r\nsecond\r\n'
        (self.root/'record.txt').write_bytes(self.raw)
        self.manifest={'artifact_kind':'EVORATIONALE_GITHUB_CODE_AND_DEVELOPMENT_EVIDENCE_EXPORT',
                       'member_sha256':{'record.txt':hashlib.sha256(self.raw).hexdigest()}}
        self.write()
    def write(self):
        (self.root/'ARTIFACT_MANIFEST.json').write_text(json.dumps(self.manifest),encoding='utf-8')
    def test_original_raw_bytes_pass_read_only(self):
        before=(self.root/'record.txt').read_bytes()
        self.assertEqual(VERIFY.verify_files(self.root),1)
        self.assertEqual((self.root/'record.txt').read_bytes(),before)
    def test_line_ending_normalization_fails(self):
        (self.root/'record.txt').write_bytes(self.raw.replace(b'\r\n',b'\n'))
        with self.assertRaisesRegex(ValueError,'Export member changed'):
            VERIFY.verify_files(self.root)
    def test_missing_member_fails(self):
        (self.root/'record.txt').unlink()
        with self.assertRaisesRegex(ValueError,'Missing/nonregular'):
            VERIFY.verify_files(self.root)
    def test_parent_escape_fails(self):
        self.manifest['member_sha256']={'../outside.txt':'0'*64}
        self.write()
        with self.assertRaisesRegex(ValueError,'Unsafe manifest path'):
            VERIFY.verify_files(self.root)
    def test_wrong_manifest_identity_fails(self):
        self.manifest['artifact_kind']='different-export'
        self.write()
        with self.assertRaisesRegex(ValueError,'Unexpected artifact manifest'):
            VERIFY.verify_files(self.root)

if __name__=='__main__':
    unittest.main()
