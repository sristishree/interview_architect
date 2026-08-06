from enum import Enum

class Difficulty(str, Enum):
    easy = "Easy"
    medium = "Medium"
    hard = "Hard"

class Category(str, Enum):
    python = "Python"
    sql = "SQL"
    ml = "ML"
    system_design = "SystemDesign"
    leadership = "Leadership"
    llm = "LLM"
    cloud = "Cloud"
    general = "General"

class QuestionType(str, Enum):
    implementation = "implementation"
    theory = "theory"
    design = "design"
    optimization = "optimization"
    behavioral = "behavioral"
    case_study = "case_study"

class Source(str, Enum):
    skill = "skill"
    project = "project"
    experience = "experience"
    leadership = "leadership"