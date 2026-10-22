import unittest

from playend.common.paths import REPO, resolve, translate


class TranslateTest(unittest.TestCase):
    def test_old_folder_names_point_to_data(self):
        self.assertEqual(
            translate("Capture-dataset-jeux/dataset/session_x/images/frame_00000001.jpg"),
            "data/captures/session_x/images/frame_00000001.jpg",
        )
        self.assertEqual(
            translate("dossier_partie_VLM/codex_luna_eval/runs/lot/annotations/a.json"),
            "data/annotations/lots/lot/annotations/a.json",
        )
        self.assertEqual(
            translate("dossier_partie_VLM/codex_luna_eval/corrections/t/observations/a.json"),
            "data/annotations/corrections/t/observations/a.json",
        )

    def test_current_paths_are_unchanged(self):
        self.assertEqual(translate("data/annotations/lots/lot/a.json"), "data/annotations/lots/lot/a.json")
        self.assertEqual(translate("obs.json"), "obs.json")

    def test_resolve_joins_the_root(self):
        self.assertEqual(resolve("Capture-dataset-jeux/dataset/s"), REPO / "data" / "captures" / "s")

    def test_broken_capture_symlink_is_followed(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "data" / "captures" / "session_x" / "images" / "frame_00000001.jpg"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"jpeg")
            link = root / "data" / "annotations" / "lots" / "lot" / "images" / "frame_00000001.jpg"
            link.parent.mkdir(parents=True)
            link.symlink_to("/elsewhere/Capture-dataset-jeux/dataset/session_x/images/frame_00000001.jpg")
            stored = "dossier_partie_VLM/codex_luna_eval/runs/lot/images/frame_00000001.jpg"
            self.assertEqual(resolve(stored, root).read_bytes(), b"jpeg")


if __name__ == "__main__":
    unittest.main()
