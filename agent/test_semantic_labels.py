import unittest
from unittest.mock import patch

import vision


class SemanticLabelSuggestionsTest(unittest.TestCase):
    def test_recognises_aliases_numbers_and_associates_nearest(self):
        regions = [
            vision.Region([], 100, 10, 90, 20, 20, True),
            vision.Region([], 100, 90, 10, 20, 20, True),
        ]
        # Vision boxes have a bottom-left origin. These land near the two regions.
        rows = [
            {"text": "CAM 2", "confidence": .93, "box": [0, 0, .2, .2]},
            {"text": "aud", "confidence": .72, "box": [.8, .8, .2, .2]},
        ]
        got = vision.semantic_label_suggestions(b"", regions, (100, 100), rows)
        self.assertEqual([x["role"] for x in got], ["camera", "audience"])
        self.assertEqual(got[0]["label"], "CAM 2")
        self.assertEqual(got[0]["targetIndex"], 1)
        self.assertEqual(got[1]["targetIndex"], 2)
        self.assertTrue(got[0]["highConfidence"])
        self.assertFalse(got[1]["highConfidence"])

    def test_every_supported_term_is_a_reviewable_proposal(self):
        text = "LED PROJ TRACK STAGE WALL SCREEN audience seating"
        rows = [{"text": text, "confidence": .88, "box": [.4, .4, .2, .2]}]
        got = vision.semantic_label_suggestions(b"", [], (200, 100), rows)
        self.assertEqual(len(got), 8)
        self.assertTrue(all(x["status"] == "proposed" for x in got))
        self.assertTrue(all(x["source"] == "ocr" for x in got))
        self.assertTrue(all(x["actions"] == ["accept", "edit", "reassign", "reject"]
                            for x in got))
        self.assertTrue(all(x["targetId"] is None for x in got))

    def test_read_exposes_suggestions_without_changing_region_role(self):
        region = vision.Region([], 100, 50, 50, 20, 20, True)
        with patch.object(vision, "trace", return_value=([region], (100, 100), object())), \
             patch.object(vision, "available", return_value=False), \
             patch.object(vision, "_ocr_rows", return_value=[]), \
             patch.object(vision, "semantic_label_suggestions", return_value=[{"id": "ocr-1"}]):
            got = vision.read(b"image", want_model=False)
        self.assertEqual(got.suggestions, [{"id": "ocr-1"}])
        self.assertEqual(region.role_from, "layout")


if __name__ == "__main__":
    unittest.main()
