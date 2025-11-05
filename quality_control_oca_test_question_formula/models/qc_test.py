"""Extension of quality control test questions to support formula validation."""

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class QcTestQuestion(models.Model):
    _inherit = "qc.test.question"

    type = fields.Selection(
        selection_add=[("formula", "Formula")],
        ondelete={"formula": "cascade"},
    )
    formula_code = fields.Text(
        string="Formula (Python)",
        help=(
            "Python expression returning True or False. Available variables: "
            "value (inspection value), line (inspection line), inspection, test, "
            "question."
        ),
    )

    @api.constrains("formula_code", "type")
    def _check_formula_syntax(self):
        """Ensure the stored formula is a valid Python expression."""
        for question in self:
            if question.type != "formula" or not question.formula_code:
                continue
            try:
                compile(question.formula_code, "<formula>", "eval")
            except SyntaxError as error:
                raise exceptions.ValidationError(
                    _("Invalid formula for '%s': %s") % (question.display_name, error)
                ) from error

    def _formula_eval_context(self, inspection_line):
        """Build the evaluation context for a formula question."""
        return {
            "value": inspection_line.quantitative_value or 0.0,
            "line": inspection_line,
            "inspection": inspection_line.inspection_id,
            "test": inspection_line.test_line.test,
            "question": inspection_line.test_line,
        }

    def _evaluate_formula(self, inspection_line):
        """Evaluate the formula and return a boolean result."""
        self.ensure_one()
        if self.type != "formula" or not self.formula_code:
            return True
        try:
            result = safe_eval(
                self.formula_code,
                self._formula_eval_context(inspection_line),
                nocopy=True,
            )
        except Exception as error:  # pragma: no cover - rethrown for clarity
            raise exceptions.UserError(
                _("Error while evaluating formula for '%s': %s")
                % (self.display_name, error)
            ) from error
        if not isinstance(result, bool):
            raise exceptions.UserError(
                _("Formula for '%s' must return True or False, got %s.")
                % (self.display_name, type(result).__name__)
            )
        return result
