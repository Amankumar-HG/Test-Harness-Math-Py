import unittest
from app.quiz import grade_answer

class TestGradeAnswer(unittest.TestCase):
    def test_grade_answer_subtraction_zero(self):
        question = {"correct": 0}
        self.assertTrue(grade_answer(question, 0))  # 7 - 7 = 0

    def test_grade_answer_subtraction_non_zero(self):
        question = {"correct": 3}
        self.assertFalse(grade_answer(question, 0))  # 7 - 4 = 3

    def test_grade_answer_subtraction_negative(self):
        question = {"correct": -1}
        self.assertFalse(grade_answer(question, 0))  # 6 - 5 = -1

if __name__ == '__main__':
    unittest.main()
