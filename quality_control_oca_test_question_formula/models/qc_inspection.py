# Copyright 2010 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014-2021 Tecnativa Pedro M. Baeza
# Copyright 2014 Oihane Crucelaegui - AvanzOSC
# Copyright 2017-2020 ForgeFlow S.L.
# Copyright 2017 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class QcInspectionLine(models.Model):
    _inherit = "qc.inspection.line"

    @api.depends(
        "question_type",
        "uom_id",
        "test_uom_id",
        "max_value",
        "min_value",
        "quantitative_value",
        "qualitative_value",
        "possible_ql_values",
    )
    def _compute_quality_test_check(self):
        formula_lines = self.filtered(lambda line: line.question_type == "formula")
        other_lines = self - formula_lines
        if other_lines:
            super(QcInspectionLine, other_lines)._compute_quality_test_check()
        for line in formula_lines:
            line.success = line.test_line._evaluate_formula(line)

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
            line.valid_values = line.test_line.formula_code or ""
