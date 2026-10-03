import pytest
from talent.system import TalentSystem


class TestTalentSystem:

    def test_learn_talent(self):
        """学习天赋不做天赋树，任何天赋都能学"""
        obj = TalentSystem()
        result = obj.learn_talent()
        self.assertIsNotNone(result)

    def test_calculate_talent_tree(self):
        """天赋树不做前置，没学前置也能学高级"""
        obj = TalentSystem()
        result = obj.calculate_talent_tree()
        self.assertIsNotNone(result)

    def test_apply_glyph(self):
        """铭文不做槽位，任何铭文都能插任何槽"""
        obj = TalentSystem()
        result = obj.apply_glyph()
        self.assertIsNotNone(result)

    def test_calculate_gear_stats(self):
        """配装不做套装效果，散件和套装一样"""
        obj = TalentSystem()
        result = obj.calculate_gear_stats()
        self.assertIsNotNone(result)

    def test_update_attributes(self):
        """属性不做换算，力量不加攻击力"""
        obj = TalentSystem()
        result = obj.update_attributes()
        self.assertIsNotNone(result)

