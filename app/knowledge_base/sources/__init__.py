from .github_ml import fetch as fetch_github
from .kaggle_swe import fetch as fetch_kaggle
from .thinkcloudly import fetch as fetch_thinkcloudly

ALL_SOURCES = [
    ("github:youssefHosni/Data-Science-Educational-Repo", fetch_github),
    ("kaggle:syedmharis/software-engineer-interview-questions", fetch_kaggle),
    ("blog:thinkcloudly.com", fetch_thinkcloudly),
]
