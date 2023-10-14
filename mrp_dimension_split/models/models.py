# Copyright 2023 Nicolás Ramos - (https://binhex.es)

import logging
import math

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = "mrp.bom"
    _description = "Product dimension split"

    product_pieces_length = fields.Float(_("Length (cm)"), store=True, default=0.0)
    product_pieces_height = fields.Float(_("Height (cm)"), store=True, default=0.0)
    product_pieces_area = fields.Float(
        compute="_computed_product_area",
        string=_("Piece area (cm)"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    product_area = fields.Float(
        compute="_computed_product_area",
        string=_("Total area (cm)"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        default=0.0,
    )
    product_number_of_pieces = fields.Float(
        compute="_computed_product_area",
        string=_("Product final pieces"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        default=0.0,
    )
    # HOJA DE CORTE
    blade_width = fields.Float(
        _("Blade Width (cm)"),
        store=True,
        default=0.0,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    blade_affects_lenght = fields.Boolean(
        _("Blade Affects lenght"), store=True, default=False
    )
    blade_affects_height = fields.Boolean(
        _("Blade Affects height"), store=True, default=False
    )
    product_pieces_length_value = fields.Float(_("Length (cm)"), store=True)
    product_pieces_height_value = fields.Float(_("Height (cm)"), store=True)

    @api.onchange(
        "product_pieces_length",
        "product_pieces_height",
        "product_qty",
        "blade_affects_lenght",
        "blade_affects_height",
    )
    def _computed_product_area(self):
        self.ensure_one()
        for line in self:
            # HOJAS DE CORTE
            if self.blade_affects_lenght:
                line.product_pieces_height_value = (
                    self.product_pieces_height + self.blade_width
                )
            else:
                line.product_pieces_height_value = (
                    self.product_pieces_height - self.blade_width
                )

            if self.blade_affects_height:
                line.product_pieces_length_value = (
                    self.product_pieces_length + self.blade_width
                )
            else:
                line.product_pieces_length_value = (
                    self.product_pieces_length - self.blade_width
                )

            # FIN HOJAS DE CORTE
            # if self.product_uom_id.uom_type == "reference":
            #     line.product_qty = line.product_qty * 100
            # raise UserError(_("The quantities established in meters will be converted to centimeters automatically."))
            line.product_pieces_area = (
                line.product_pieces_height * line.product_pieces_length / 10000
            )
            line.product_area = line.product_qty * line.product_pieces_height / 100
            if line.product_qty != 0 and line.product_pieces_length != 0:
                line.product_number_of_pieces = math.ceil(
                    line.product_qty / (line.product_pieces_length / 100)
                )

    @api.onchange(
        "bom_line_ids.product_id",
        "bom_line_ids",
        "product_pieces_length",
        "product_pieces_height",
        "product_qty",
        "blade_affects_lenght",
        "blade_affects_height",
        "product_uom_id",
    )
    def _computed_raw_product_area(self):
        for line in self.bom_line_ids:
            if line.raw_product_uom_id.uom_type == "reference":
                line.raw_product_length = line.product_id.product_length
                line.raw_product_height = line.product_id.product_height
            else:
                line.raw_product_length = line.raw_product_length
                line.raw_product_height = line.raw_product_height
            try:
                na0 = math.floor(
                    line.raw_product_length / self.product_pieces_length_value + 0.001
                )
                nl0 = math.floor(
                    line.raw_product_height / self.product_pieces_height_value + 0.001
                )
                na1 = math.floor(
                    line.raw_product_length / self.product_pieces_height_value + 0.001
                )
                nl1 = math.floor(
                    line.raw_product_height / self.product_pieces_length_value + 0.001
                )
            except ZeroDivisionError:
                na0 = 0
                nl0 = 0
                na1 = 0
                nl1 = 0

            area_h = na0 * nl0
            area_v = na1 * nl1
            raw_product_usable_area_h = area_h * self.product_pieces_area
            raw_product_usable_area_v = area_v * self.product_pieces_area
            if raw_product_usable_area_h >= raw_product_usable_area_v:
                line.raw_product_usable_area = raw_product_usable_area_h
                line.raw_area_orientation = "h"
            else:
                line.raw_product_usable_area = raw_product_usable_area_v
                line.raw_area_orientation = "v"
            line.raw_product_area = (
                line.raw_product_length * line.raw_product_height / 10000
            )


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
        "Product area", store=True, digits=dp.get_precision("Product Unit of Measure")
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
