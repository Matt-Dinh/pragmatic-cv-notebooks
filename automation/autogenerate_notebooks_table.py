from __future__ import annotations

import argparse

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

NOTEBOOKS_ROOT_PATH = "https://github.com/roboflow-ai/notebooks/blob/main/notebooks"
NOTEBOOKS_COLAB_ROOT_PATH = "github/roboflow-ai/notebooks/blob/main/notebooks"


WARNING_HEADER = [
    "<!---",
    "   WARNING: DO NOT EDIT THIS TABLE MANUALLY. IT IS AUTOMATICALLY GENERATED.",
    "   HEAD OVER TO CONTRIBUTING.MD FOR MORE DETAILS ON HOW TO MAKE CHANGES PROPERLY.",
    "-->"
]

TABLE_HEADER = [
    "| **notebook** | **colab / kaggle** | **blog / youtube** | **repository / paper** |",
    "|:------------:|:-------------------------------------------------:|:---------------------------:|:----------------------:|"
]

MODELS_SECTION_HEADER = "## Model Experiments ({} notebooks)"
APPLIED_SECTION_HEADER = "## Applied computer vision in real world scenarios ({} notebooks)"

NOTEBOOK_LINK_PATTERN = "[{}]({}/{})"
OPEN_IN_COLAB_BADGE_PATTERN = "[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/{}/{})"
OPEN_IN_KAGGLE_BADGE_PATTERN = "[![Kaggle](https://kaggle.com/static/images/open-in-kaggle.svg)](https://kaggle.com/kernels/welcome?src={}/{})"
ROBOFLOW_BADGE_PATTERN = "[![Roboflow](https://raw.githubusercontent.com/roboflow-ai/notebooks/main/assets/badges/roboflow-blogpost.svg)]({})"
YOUTUBE_BADGE_PATTERN = "[![YouTube](https://badges.aleen42.com/src/youtube.svg)]({})"
GITHUB_BADGE_PATTERN = "[![GitHub](https://badges.aleen42.com/src/github.svg)]({})"
ARXIV_BADGE_PATTERN = "[![arXiv](https://img.shields.io/badge/arXiv-{}-b31b1b.svg)](https://arxiv.org/abs/{})"

AUTOGENERATED_NOTEBOOKS_TABLE_TOKEN = "<!--- AUTOGENERATED-NOTEBOOKS-TABLE -->"


class READMESection(Enum):
    MODELS = "models"
    APPLIED = "applied"

    @classmethod
    def from_value(cls, value: str) -> READMESection:
        try:
            return cls(value=value.lower())
        except (AttributeError, ValueError):
            raise Exception(f"{cls.__name__} must be one of {READMESection.list()}, {value} given.")

    @staticmethod
    def list():
        return list(map(lambda entry: entry.value, READMESection))


@dataclass(frozen=True)
class TableEntry:
    display_name: str
    notebook_name: str
    roboflow_blogpost_path: Optional[str]
    youtube_video_path: Optional[str]
    github_repository_path: Optional[str]
    arxiv_index: Optional[str]
    readme_section: READMESection

    @classmethod
    def from_csv_line(cls, csv_line: str) -> TableEntry:
        csv_fields = [
            field.strip()
            for field
            in csv_line.split(",")
        ]
        if len(csv_fields) != 7:
            raise Exception("Every csv line must contain 7 fields")
        return TableEntry(
            display_name=csv_fields[0],
            notebook_name=csv_fields[1],
            roboflow_blogpost_path=csv_fields[2],
            youtube_video_path=csv_fields[3],
            github_repository_path=csv_fields[4],
            arxiv_index=csv_fields[5],
            readme_section=READMESection(csv_fields[6])
        )

    def format(self) -> str:
        notebook_link = NOTEBOOK_LINK_PATTERN.format(self.display_name, NOTEBOOKS_ROOT_PATH, self.notebook_name)
        open_in_colab_badge = OPEN_IN_COLAB_BADGE_PATTERN.format(NOTEBOOKS_COLAB_ROOT_PATH, self.notebook_name)
        open_in_kaggle_badge = OPEN_IN_KAGGLE_BADGE_PATTERN.format(NOTEBOOKS_ROOT_PATH, self.notebook_name)
        roboflow_badge = ROBOFLOW_BADGE_PATTERN.format(self.roboflow_blogpost_path) if self.roboflow_blogpost_path else ""
        youtube_badge = YOUTUBE_BADGE_PATTERN.format(self.youtube_video_path) if self.youtube_video_path else ""
        github_badge = GITHUB_BADGE_PATTERN.format(self.github_repository_path) if self.github_repository_path else ""
        arxiv_badge = ARXIV_BADGE_PATTERN.format(self.arxiv_index, self.arxiv_index) if self.arxiv_index else ""
        return f"| {notebook_link} | {open_in_colab_badge} {open_in_kaggle_badge} | {roboflow_badge} {youtube_badge} | {github_badge} {arxiv_badge}|"


def read_lines_from_file(path: str) -> List[str]:
    with open(path) as file:
        return [line.rstrip() for line in file]


def save_lines_to_file(path: str, lines: List[str]) -> None:
    with open(path, "w") as f:
        for line in lines:
            f.write("%s\n" % line)


def parse_csv_lines(csv_lines: List[str]) -> List[TableEntry]:
    return [
        TableEntry.from_csv_line(csv_line=csv_line)
        for csv_line
        in csv_lines
    ]

def search_lines_with_token(lines: List[str], token: str) -> List[int]:
    result = []
    for line_index, line in enumerate(lines):
        if token in line:
            result.append(line_index)
    return result


def inject_markdown_table_into_readme(readme_lines: List[str], table_lines: List[str]) -> List[str]:
    lines_with_token_indexes = search_lines_with_token(lines=readme_lines, token=AUTOGENERATED_NOTEBOOKS_TABLE_TOKEN)
    if len(lines_with_token_indexes) != 2:
        raise Exception(f"Please inject two {AUTOGENERATED_NOTEBOOKS_TABLE_TOKEN} "
                        f"tokens to signal start and end of autogenerated table.")

    [table_start_line_index, table_end_line_index] = lines_with_token_indexes
    return readme_lines[:table_start_line_index + 1] + table_lines + readme_lines[table_end_line_index:]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data_path', default='automation/notebooks-table-data.csv')
    parser.add_argument('-r', '--readme_path', default='README.md')
    args = parser.parse_args()

    csv_lines = read_lines_from_file(path=args.data_path)[1:]
    readme_lines = read_lines_from_file(path=args.readme_path)
    table_entries = parse_csv_lines(csv_lines=csv_lines)
    models_lines = [
        entry.format()
        for entry
        in table_entries
        if entry.readme_section == READMESection.MODELS
    ]
    APPLIED_lines = [
        entry.format()
        for entry
        in table_entries
        if entry.readme_section == READMESection.APPLIED
    ]
    table_lines = WARNING_HEADER + \
                  [MODELS_SECTION_HEADER.format(len(models_lines))] + TABLE_HEADER + models_lines + \
                  [APPLIED_SECTION_HEADER.format(len(APPLIED_lines))] + TABLE_HEADER + APPLIED_lines
    readme_lines = inject_markdown_table_into_readme(readme_lines=readme_lines, table_lines=table_lines)
    save_lines_to_file(path=args.readme_path, lines=readme_lines)
