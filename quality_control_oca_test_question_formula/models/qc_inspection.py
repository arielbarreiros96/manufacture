# Copyright 2010 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014-2021 Tecnativa Pedro M. Baeza
# Copyright 2014 Oihane Crucelaegui - AvanzOSC
# Copyright 2017-2020 ForgeFlow S.L.
# Copyright 2017 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    def action_confirm(self):
        """Apply core validation rules while allowing extra question types."""
        validators = {
            "qualitative": (
                lambda line: line.qualitative_value,
                _("You should provide an answer for all qualitative questions."),
            ),
            "quantitative": (
                lambda line: line.uom_id,
                _("You should provide a unit of measure for quantitative questions."),
            ),
        }
        for inspection in self:
            for line in inspection.inspection_lines:
                validator = validators.get(line.question_type)
                if validator and not validator[0](line):
                    raise exceptions.UserError(validator[1])
            inspection.state = "success" if inspection.success else "waiting"


class QcInspectionLine(models.Model):
    _inherit = "qc.inspection.line"

    question_type = fields.Selection(selection_add=[("formula", "Formula")])

    @api.depends(
        "question_type",
        "uom_id",
        "test_uom_id",
        "max_value",
        "min_value",
        "quantitative_value",
        "qualitative_value",
        "possible_ql_values",
        "inspection_id.write_date",
    )
    def _compute_quality_test_check(self):
        if not all(line.inspection_id.state == "ready" for line in self):
            return
        formula_lines = self.filtered(lambda line: line.question_type == "formula")
        other_lines = self - formula_lines
        if other_lines:
            super(QcInspectionLine, other_lines)._compute_quality_test_check()
        for line in formula_lines:
            if not line.test_line:
                line.success = False
                continue
            line.success = bool(line.test_line._evaluate_formula(line))

    @api.depends(
        "possible_ql_values",
        "min_value",
        "max_value",
        "test_uom_id",
        "question_type",
    )
    def _compute_valid_values(self):
        formula_lines = self.filtered(lambda line: line.question_type == "formula")
        other_lines = self - formula_lines
        if other_lines:
            super(QcInspectionLine, other_lines)._compute_valid_values()
        for line in formula_lines:
            line.valid_values = "-"
