from src.gradio_ui import load_frequent_questions


def test_load_frequent_questions():
    questions = load_frequent_questions()
    assert isinstance(questions, list)
    assert questions[0] == "Jak się walczy?"
    assert all(isinstance(q, str) for q in questions)
