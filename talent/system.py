"""
pairwise-talent-system - TalentSystem

This module contains a deliberately broken implementation.
Fix all bugs so that tests pass.
"""


class TalentSystem:
    def __init__(self):
        self.state = {}

    def learn_talent(self, *args, **kwargs):
        """BUG: 学习天赋不做天赋树，任何天赋都能学"""
        return None

    def calculate_talent_tree(self, *args, **kwargs):
        """BUG: 天赋树不做前置，没学前置也能学高级"""
        return None

    def apply_glyph(self, *args, **kwargs):
        """BUG: 铭文不做槽位，任何铭文都能插任何槽"""
        return None

    def calculate_gear_stats(self, *args, **kwargs):
        """BUG: 配装不做套装效果，散件和套装一样"""
        return None

    def update_attributes(self, *args, **kwargs):
        """BUG: 属性不做换算，力量不加攻击力"""
        return None

