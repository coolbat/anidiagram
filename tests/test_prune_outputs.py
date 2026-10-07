import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('prune',Path(__file__).resolve().parents[1]/'scripts/prune_outputs.py')
prune=importlib.util.module_from_spec(spec);spec.loader.exec_module(prune)
class OutputCleanupTest(unittest.TestCase):
    def test_changed_candidate_blocks_all_moves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'outputs';root.mkdir();(root/'a').write_text('one');(root/'b').write_text('two')
            data=prune.manifest(root,['a','b']);(root/'b').write_text('changed')
            with self.assertRaisesRegex(ValueError,'changed'):prune.apply_manifest(root,data,Path(tmp)/'trash')
            self.assertTrue((root/'a').exists());self.assertFalse((Path(tmp)/'trash').exists())
    def test_reversible_move_and_reject_escaping_symlinks_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'outputs';root.mkdir();(root/'build').mkdir();(root/'build'/'proof').write_text('keep bytes')
            (root/'link').symlink_to(Path(tmp));
            for name in ['../escape','link','release-evidence','accuracy-study']:
                with self.assertRaises(ValueError):prune.manifest(root,[name])
            data=prune.manifest(root,['build']);trash=Path(tmp)/'trash';receipt=prune.apply_manifest(root,data,trash)
            self.assertFalse((root/'build').exists());self.assertEqual('keep bytes',(trash/'build'/'proof').read_text());self.assertEqual(str(root/'build'),receipt['moves'][0]['from']);self.assertTrue((trash/'restore-manifest.json').exists())
