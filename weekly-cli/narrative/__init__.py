"""
格物 (Dianalyze) Narrative Module
==================================

Renders WeeklyIssue analysis output into reader-facing Markdown articles
organized by the five-phase dialectical epistemological movement.

Phases:
  一、现象 - Phenomenon Grasping
  二、矛盾 - Contradiction Identification
  三、展开 - Dialectical Unfolding
  四、定位 - Historical Positioning
  五、方向 - Practice Orientation
"""

from narrative.article import generate_article

__all__ = ["generate_article"]
