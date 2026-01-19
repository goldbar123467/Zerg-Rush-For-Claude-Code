"""Orson Daemons Module - Background processes for the swarm."""

from .researcher import ResearcherDaemon
from .teacher import TeacherDaemon

__all__ = ['ResearcherDaemon', 'TeacherDaemon']
