# ruff: noqa: T201, INP001

import json
from pathlib import Path

from complete_business_analysis_tool.assessments.models import (
    AssessmentTemplate,
    Category,
    Question,
    QuestionOption,
    TemplateQuestion,
)

# Open the JSON file for reading
with Path("data/cba_questions.json").open() as file:
    data = json.load(file)  # Parse JSON into a Python dictionary or list

cba, _ = AssessmentTemplate.objects.get_or_create(
    title="CBA",
    description="Complete business analysis.",
)

order_cnt = 1
# Use the data
for d in data:
    category_name = d["section"]
    category, _ = Category.objects.get_or_create(name=category_name)
    for q in d["questions"]:
        question, _ = Question.objects.get_or_create(
            body=q["prompt"],
            category=category,
        )
        for answer in q["answers"]:
            QuestionOption.objects.get_or_create(
                question=question,
                text=answer["text"],
                rank=answer["points"],
                weight="100",
            )
        TemplateQuestion.objects.get_or_create(
            template=cba,
            question=question,
            order=order_cnt,
        )
        order_cnt += 1

print(cba.id)
