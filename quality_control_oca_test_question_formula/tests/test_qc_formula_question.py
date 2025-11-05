# Copyright 2010 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014-2021 Tecnativa Pedro M. Baeza
# Copyright 2014 Oihane Crucelaegui - AvanzOSC
# Copyright 2017-2020 ForgeFlow S.L.
# Copyright 2017 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase


class TestQcFormulaQuestion(TransactionCase):
    def setUp(self):
        super().setUp()
        self.qc_test = self.env["qc.test"].create(
            {
                "name": "Test Formula Questions",
                "type": "generic",
            }
        )

    def test_formula_question_creation(self):
        """Ensure the formula type can be stored."""
        question = self.env["qc.test.question"].create(
            {
                "name": "Simple Formula",
                "test": self.qc_test.id,
                "type": "formula",
                "formula_code": "value > 10",
            }
        )
        self.assertEqual(question.type, "formula")
        self.assertEqual(question.formula_code, "value > 10")

    def test_invalid_formula_syntax(self):
        """Invalid expressions are rejected on save."""
        with self.assertRaises(ValidationError):
            self.env["qc.test.question"].create(
                {
                    "name": "Broken Formula",
                    "test": self.qc_test.id,
                    "type": "formula",
                    "formula_code": "value > (",
                }
            )

    def test_formula_evaluation_updates_success(self):
        """Formula evaluation drives the success flag."""
        question = self.env["qc.test.question"].create(
            {
                "name": "Threshold",
                "test": self.qc_test.id,
                "type": "formula",
                "formula_code": "value >= 5",
            }
        )
        inspection = self.env["qc.inspection"].create(
            {
                "name": "Inspection",
                "test": self.qc_test.id,
            }
        )
        line = self.env["qc.inspection.line"].create(
            {
                "inspection_id": inspection.id,
                "name": "Formula line",
                "test_line": question.id,
                "question_type": "formula",
                "quantitative_value": 8.0,
            }
        )
        line._compute_quality_test_check()
        self.assertTrue(line.success)
        line.quantitative_value = 2.0
        line._compute_quality_test_check()
        self.assertFalse(line.success)

    def test_formula_can_use_line_context(self):
        """The evaluation context exposes the inspection line."""
        question = self.env["qc.test.question"].create(
            {
                "name": "Line Based",
                "test": self.qc_test.id,
                "type": "formula",
                "formula_code": "line.quantitative_value == 3",
            }
        )
        inspection = self.env["qc.inspection"].create(
            {
                "name": "Inspection",
                "test": self.qc_test.id,
            }
        )
        line = self.env["qc.inspection.line"].create(
            {
                "inspection_id": inspection.id,
                "name": "Formula line",
                "test_line": question.id,
                "question_type": "formula",
                "quantitative_value": 3.0,
            }
        )
        line._compute_quality_test_check()
        self.assertTrue(line.success)

    def test_formula_must_return_boolean(self):
        """Non-boolean results raise a user error."""
        question = self.env["qc.test.question"].create(
            {
                "name": "Invalid Return",
                "test": self.qc_test.id,
                "type": "formula",
                "formula_code": "value + 1",
            }
        )
        inspection = self.env["qc.inspection"].create(
            {
                "name": "Inspection",
                "test": self.qc_test.id,
            }
        )
        line = self.env["qc.inspection.line"].create(
            {
                "inspection_id": inspection.id,
                "name": "Formula line",
                "test_line": question.id,
                "question_type": "formula",
                "quantitative_value": 1.0,
            }
        )
        with self.assertRaises(UserError):
            line._compute_quality_test_check()

    def test_inspection_success_with_formula(self):
        """Running set_test keeps original logic and marks success."""
        question = self.env["qc.test.question"].create(
            {
                "name": "Workflow Formula",
                "test": self.qc_test.id,
                "type": "formula",
                "formula_code": "value == 4",
                "sequence": 5,
            }
        )
        inspection = self.env["qc.inspection"].create({"name": "Inspection"})
        trigger_line = type(
            "MockTriggerLine",
            (),
            {
                "test": self.qc_test,
                "timing": "ready",
                "user": self.env.user,
            },
        )()
        inspection.set_test(trigger_line)
        self.assertEqual(len(inspection.inspection_lines), 1)
        line = inspection.inspection_lines
        line.quantitative_value = 4
        line._compute_quality_test_check()
        inspection._compute_success()
        self.assertTrue(inspection.success)
