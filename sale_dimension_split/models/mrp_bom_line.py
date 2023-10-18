##############################################################################
#
# Copyright (c) 2023 Binhex System Solutions
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################


import logging
import math

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"
    _description = "Product dimension split lines"

    raw_product_length = fields.Float(
        related="product_id.product_length",
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        string=_("Length (cm)"),
    )
    raw_product_height = fields.Float(
        related="product_id.product_height",
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        string=_("Height (cm)"),
    )
    raw_product_uom_id = fields.Many2one(
        related="product_id.dimensional_uom_id", string="UoM", readonly=True
    )

    raw_product_area = fields.Float(
        "Product area", store=True, digits=(16, 4)
    )
    raw_product_usable_area = fields.Float(
        "Product usable area",
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    raw_area_orientation = fields.Selection(
        [
            ("h", "H"),
            ("v", "V"),
        ],
        string="Orientation",
        store=True,
    )
