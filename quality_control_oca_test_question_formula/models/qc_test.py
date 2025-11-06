"""Extension of quality control test questions to support formula validation."""

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import (
    datetime as safe_datetime,
)
from odoo.tools.safe_eval import (
    dateutil as safe_dateutil,
)
from odoo.tools.safe_eval import (
    pytz as safe_pytz,
)
from odoo.tools.safe_eval import (
    safe_eval,
)
from odoo.tools.safe_eval import (
    time as safe_time,
)

FORMULA_TEMPLATE = (
    "# Write Python code that assigns True or False to the variable `result`.\n"
    "# Available variables:\n"
    "#   line -> quality inspection line (qc.inspection.line).\n"
    "#   inspection -> inspection record (qc.inspection).\n"
    "#   test -> quality test (qc.test).\n"
    "#   question -> test line definition (qc.test.line).\n"
    "#   env -> Odoo environment.\n"
    "#   datetime -> Safe wrapper around the datetime module.\n"
    "#   time -> Safe wrapper around selected functions of time module.\n"
    "#   dateutil -> Safe wrapper around python-dateutil helpers.\n"
    "#   timezone -> Safe pytz.timezone helper.\n"
    "# You must set `result` to a boolean value.\n"
    "# Example:\n"
    "# result = inspection.qty > 0\n"
    "result = True\n"
)


def _contains_expression(code):
    """Return True when the string contains any non-comment expression."""
    for line in (code or "").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return True
    return False


class QcTestQuestion(models.Model):
    _inherit = "qc.test.question"

    type = fields.Selection(
        selection_add=[("formula", "Formula")],
        ondelete={"formula": "cascade"},
    )
    formula_code = fields.Text(
        string="Formula",
        help=(
            "Python code that sets a boolean in the variable `result`. Available "
            "variables: line (inspection line), inspection, test, question, env, "
            "datetime, time, dateutil, timezone."
        ),
        default=FORMULA_TEMPLATE,
    )

    @api.constrains("formula_code", "type")
    def _check_formula_syntax(self):
        """Ensure the stored formula is a valid Python expression."""
        for question in self:
            if question.type != "formula" or not question.formula_code:
                continue
            if not _contains_expression(question.formula_code):
                continue
            try:
                compile(question.formula_code, "<formula>", "exec")
            except SyntaxError as error:
                raise exceptions.ValidationError(
                    _("Invalid formula for '%s': %s") % (question.display_name, error)
                ) from error

    @api.onchange("type")
    def _onchange_type_set_formula_template(self):
        """Pre-fill template instructions when switching to formula type."""
        for question in self:
            if question.type == "formula" and not question.formula_code:
                question.formula_code = FORMULA_TEMPLATE

    def _formula_eval_context(self, inspection_line):
        """Build the evaluation context for a formula question."""
        return {
            "line": inspection_line,
            "inspection": inspection_line.inspection_id,
            "test": inspection_line.test_line.test,
            "question": inspection_line.test_line,
            "env": self.env,
            "datetime": safe_datetime,
            "time": safe_time,
            "dateutil": safe_dateutil,
            "timezone": safe_pytz.timezone,
            "result": False,
        }

    def _evaluate_formula(self, inspection_line):
        """Evaluate the formula and return a boolean result."""
        self.ensure_one()
        if self.type != "formula" or not self.formula_code:
            return True
        if not _contains_expression(self.formula_code):
            return True
        context = self._formula_eval_context(inspection_line)
        try:
            safe_eval(
                self.formula_code,
                context,
                mode="exec",
                nocopy=True,
            )
        except Exception as error:
            raise exceptions.UserError(
                _("Error while evaluating formula for '%s': %s")
                % (self.display_name, error)
            ) from error
        result_value = context.get("result")
        if result_value is None:
            raise exceptions.UserError(
                _("Formula for '%s' must assign a boolean to the variable `result`.")
                % self.display_name
            )
        if not isinstance(result_value, bool):
            raise exceptions.UserError(
                _("Formula for '%s' must set `result` to True or False, got %s.")
                % (self.display_name, type(result_value).__name__)
            )
        return result_value
