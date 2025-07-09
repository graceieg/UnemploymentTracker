import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import networkx as nx

@dataclass
class Skill:
    """Class representing a skill with its properties."""
    id: str
    name: str
    category: str
    description: Optional[str] = None
    importance: Optional[float] = None
    level: Optional[float] = None  # 0-1 scale

@dataclass
class JobProfile:
    """Class representing a job profile with required skills."""
    id: str
    title: str
    industry: str
    required_skills: Dict[str, Skill]  # skill_id -> Skill
    description: Optional[str] = None
    average_salary: Optional[float] = None
    growth_rate: Optional[float] = None  # Annual growth rate
    
    def add_skill(self, skill: Skill):
        """Add a skill to the job profile."""
        self.required_skills[skill.id] = skill
    
    def get_skill_ids(self) -> Set[str]:
        """Get set of skill IDs required for this job."""
        return set(self.required_skills.keys())

@dataclass
class TransitionPath:
    """Class representing a career transition path."""
    source_job: str
    target_job: str
    skill_overlap: Set[str]
    missing_skills: Set[str]
    transition_difficulty: float  # 0-1 scale, higher is more difficult
    skill_gap: float  # Percentage of skills missing (0-1)
    common_skills_count: int
    missing_skills_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for easier serialization."""
        return {
            'source_job': self.source_job,
            'target_job': self.target_job,
            'skill_overlap': list(self.skill_overlap),
            'missing_skills': list(self.missing_skills),
            'transition_difficulty': self.transition_difficulty,
            'skill_gap': self.skill_gap,
            'common_skills_count': self.common_skills_count,
            'missing_skills_count': self.missing_skills_count
        }

class SkillMatcher:
    """Class for matching skills between jobs and recommending transitions."""
    
    def __init__(self, job_profiles: Optional[Dict[str, JobProfile]] = None):
        """Initialize the SkillMatcher with optional job profiles."""
        self.job_profiles = job_profiles or {}
        self.skill_graph = nx.Graph()
        self._build_skill_graph()
    
    def add_job_profile(self, profile: JobProfile):
        """Add a job profile to the matcher."""
        self.job_profiles[profile.id] = profile
        self._update_skill_graph(profile)
    
    def _build_skill_graph(self):
        """Build a graph of skills based on job profiles."""
        # Add all skills as nodes
        for job_id, profile in self.job_profiles.items():
            for skill_id, skill in profile.required_skills.items():
                self.skill_graph.add_node(skill_id, **skill.__dict__)
        
        # Add edges between skills that appear together in job profiles
        for job_id, profile in self.job_profiles.items():
            skills = list(profile.required_skills.keys())
            for i in range(len(skills)):
                for j in range(i + 1, len(skills)):
                    if self.skill_graph.has_edge(skills[i], skills[j]):
                        self.skill_graph[skills[i]][skills[j]]['weight'] += 1
                    else:
                        self.skill_graph.add_edge(skills[i], skills[j], weight=1)
    
    def _update_skill_graph(self, profile: JobProfile):
        """Update the skill graph with a new job profile."""
        # Add new skills as nodes
        for skill_id, skill in profile.required_skills.items():
            if not self.skill_graph.has_node(skill_id):
                self.skill_graph.add_node(skill_id, **skill.__dict__)
        
        # Update edges
        skills = list(profile.required_skills.keys())
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                if self.skill_graph.has_edge(skills[i], skills[j]):
                    self.skill_graph[skills[i]][skills[j]]['weight'] += 1
                else:
                    self.skill_graph.add_edge(skills[i], skills[j], weight=1)
    
    def find_similar_jobs(self, 
                         source_job_id: str, 
                         top_n: int = 5,
                         min_skill_overlap: float = 0.3) -> List[Tuple[str, float]]:
        """Find jobs similar to the source job based on skill overlap.
        
        Args:
            source_job_id: ID of the source job
            top_n: Number of similar jobs to return
            min_skill_overlap: Minimum skill overlap ratio (0-1) to consider
            
        Returns:
            List of (job_id, similarity_score) tuples, sorted by similarity
        """
        if source_job_id not in self.job_profiles:
            return []
            
        source_skills = self.job_profiles[source_job_id].get_skill_ids()
        similarities = []
        
        for job_id, profile in self.job_profiles.items():
            if job_id == source_job_id:
                continue
                
            target_skills = profile.get_skill_ids()
            if not target_skills:
                continue
                
            # Calculate Jaccard similarity
            intersection = len(source_skills & target_skills)
            union = len(source_skills | target_skills)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= min_skill_overlap:
                similarities.append((job_id, similarity))
        
        # Sort by similarity (descending) and return top N
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_n]
    
    def find_transition_paths(self, 
                            source_job_id: str,
                            target_job_id: str,
                            max_hops: int = 2) -> List[TransitionPath]:
        """Find possible transition paths between two jobs.
        
        Args:
            source_job_id: ID of the source job
            target_job_id: ID of the target job
            max_hops: Maximum number of intermediate jobs to consider
            
        Returns:
            List of TransitionPath objects representing possible transitions
        """
        if (source_job_id not in self.job_profiles or 
            target_job_id not in self.job_profiles):
            return []
            
        source_skills = self.job_profiles[source_job_id].get_skill_ids()
        target_skills = self.job_profiles[target_job_id].get_skill_ids()
        
        # Direct transition
        direct_path = self._create_transition_path(
            source_job_id, 
            target_job_id, 
            source_skills, 
            target_skills
        )
        
        if max_hops <= 0:
            return [direct_path] if direct_path.transition_difficulty < 1.0 else []
        
        # Find intermediate jobs that could bridge the gap
        intermediate_paths = []
        
        for job_id, profile in self.job_profiles.items():
            if job_id in [source_job_id, target_job_id]:
                continue
                
            job_skills = profile.get_skill_ids()
            
            # Check if this job could be a good intermediate step
            to_intermediate = self._create_transition_path(
                source_job_id, job_id, source_skills, job_skills)
            
            intermediate_to_target = self._create_transition_path(
                job_id, target_job_id, job_skills, target_skills)
            
            # Only consider if both steps are feasible
            if (to_intermediate.transition_difficulty < 1.0 and 
                intermediate_to_target.transition_difficulty < 1.0):
                
                # Combine the two steps
                combined_difficulty = max(
                    to_intermediate.transition_difficulty,
                    intermediate_to_target.transition_difficulty
                )
                
                combined_path = TransitionPath(
                    source_job=source_job_id,
                    target_job=target_job_id,
                    skill_overlap=to_intermediate.skill_overlap | intermediate_to_target.skill_overlap,
                    missing_skills=to_intermediate.missing_skills | intermediate_to_target.missing_skills,
                    transition_difficulty=combined_difficulty,
                    skill_gap=max(to_intermediate.skill_gap, intermediate_to_target.skill_gap),
                    common_skills_count=to_intermediate.common_skills_count + intermediate_to_target.common_skills_count,
                    missing_skills_count=to_intermediate.missing_skills_count + intermediate_to_target.missing_skills_count
                )
                
                intermediate_paths.append(combined_path)
        
        # Combine direct and intermediate paths, remove duplicates, and sort by difficulty
        all_paths = [p for p in [direct_path] + intermediate_paths 
                    if p.transition_difficulty < 1.0]
        
        # Remove duplicate paths (same missing skills)
        unique_paths = {}
        for path in all_paths:
            key = frozenset(path.missing_skills)
            if key not in unique_paths or \
               path.transition_difficulty < unique_paths[key].transition_difficulty:
                unique_paths[key] = path
        
        return sorted(unique_paths.values(), 
                     key=lambda x: (x.transition_difficulty, -x.common_skills_count))
    
    def _create_transition_path(self, 
                              source_job_id: str,
                              target_job_id: str,
                              source_skills: Set[str],
                              target_skills: Set[str]) -> TransitionPath:
        """Create a TransitionPath between two sets of skills."""
        common_skills = source_skills & target_skills
        missing_skills = target_skills - source_skills
        
        skill_gap = len(missing_skills) / len(target_skills) if target_skills else 1.0
        
        # Calculate transition difficulty based on skill gap and skill levels
        difficulty = skill_gap  # Base difficulty on skill gap
        
        return TransitionPath(
            source_job=source_job_id,
            target_job=target_job_id,
            skill_overlap=common_skills,
            missing_skills=missing_skills,
            transition_difficulty=min(1.0, difficulty),  # Cap at 1.0
            skill_gap=skill_gap,
            common_skills_count=len(common_skills),
            missing_skills_count=len(missing_skills)
        )
    
    def recommend_training(self, 
                         source_job_id: str,
                         target_job_id: str,
                         available_courses: List[Dict]) -> List[Dict]:
        """Recommend training courses to bridge skill gaps.
        
        Args:
            source_job_id: ID of the source job
            target_job_id: ID of the target job
            available_courses: List of course dictionaries with 'skills_covered' field
            
        Returns:
            List of recommended courses with relevance scores
        """
        if (source_job_id not in self.job_profiles or 
            target_job_id not in self.job_profiles):
            return []
            
        source_skills = self.job_profiles[source_job_id].get_skill_ids()
        target_skills = self.job_profiles[target_job_id].get_skill_ids()
        missing_skills = target_skills - source_skills
        
        if not missing_skills:
            return []
        
        # Score each course based on how many missing skills it covers
        course_scores = []
        
        for course in available_courses:
            if 'skills_covered' not in course:
                continue
                
            covered_skills = set(course['skills_covered']) & missing_skills
            if not covered_skills:
                continue
                
            # Calculate relevance score
            relevance = len(covered_skills) / len(missing_skills)
            
            course_scores.append({
                'course_id': course.get('id'),
                'title': course.get('title', 'Untitled Course'),
                'provider': course.get('provider', 'Unknown'),
                'url': course.get('url', ''),
                'skills_covered': list(covered_skills),
                'relevance_score': relevance,
                'missing_skills_covered': len(covered_skills),
                'total_missing_skills': len(missing_skills)
            })
        
        # Sort by relevance (descending)
        return sorted(course_scores, key=lambda x: x['relevance_score'], reverse=True)
