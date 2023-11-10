##############################################################################
#
# Copyright (c) 2023 Binhex System Solutions
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################


import logging

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    product_pieces_length = fields.Float(
        _("Largo (cm)"),
        related="sale_line_id.product_pieces_length",
        store=True,
        default=0.0,
    )
    product_pieces_height = fields.Float(
        _("Alto (cm)"),
        related="sale_line_id.product_pieces_height",
        store=True,
        default=0.0,
    )
    product_pieces_width = fields.Float(_("Ancho (cm)"), store=True, default=0.0)
    product_number_of_pieces = fields.Float(
        # compute="_computed_product_area",
        string=_("Piezas finales del producto"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        default=0.0,
    )
    price_unit = fields.Float(
        "Unit Price",
        related="sale_line_id.price_unit",
        digits="Product Price",
        default=0.0,
    )

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        if self.sale_line_id and self.sale_line_id.bom_id:
            values["bom_id"] = self.sale_line_id.bom_id
        return values


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_pieces_length = fields.Float(
        _("Largo (cm)"),
        related="move_id.product_pieces_length",
        store=True,
        default=0.0,
    )
    product_pieces_height = fields.Float(
        _("Alto (cm)"), related="move_id.product_pieces_height", store=True, default=0.0
    )
    product_pieces_width = fields.Float(
        _("Espesor (cm)"), related="move_id.product_pieces_width", store=True, default=0.0
    )
    
    product_number_of_pieces = fields.Float(
        # compute="_computed_product_area",
        string=_("Piezas finales del producto"),
        related="move_id.product_number_of_pieces",
    )
    price_unit = fields.Float(
        "Unit Price",
        related="move_id.price_unit",
        
    )

    def _get_aggregated_product_quantities(self, **kwargs):
        aggregated_move_lines = super(
            StockMoveLine, self
        )._get_aggregated_product_quantities(**kwargs)
        for move_line in self:
            name = move_line.product_id.display_name
            description = move_line.move_id.description_picking
            if description == name or description == move_line.product_id.name:
                description = False
            uom = move_line.product_uom_id
            line_key = (
                str(move_line.product_id.id)
                + "_"
                + name
                + (description or "")
                + "uom "
                + str(uom.id)
            )
            if line_key in aggregated_move_lines:
                aggregated_move_lines[line_key][
                    "product_pieces_length"
                ] = move_line.product_pieces_length
                aggregated_move_lines[line_key][
                    "product_pieces_height"
                ] = move_line.product_pieces_height
                aggregated_move_lines[line_key][
                    "product_pieces_width"
                ] = move_line.product_pieces_width
                aggregated_move_lines[line_key][
                    "product_number_of_pieces"
                ] = move_line.product_number_of_pieces
                aggregated_move_lines[line_key]["price_unit"] = move_line.price_unit

        return aggregated_move_lines