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


class SaleOrderLineBom(models.Model):
    _name = "sale.order.line.bom"
    _description = "Product dimension split bom"

    def _get_default_product_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order="id").id

    product_id = fields.Many2one(
        "product.product", _("Componente"), required=True, check_company=True
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        _("Plantilla del producto"),
        related="product_id.product_tmpl_id",
    )
    company_id = fields.Many2one(
        related="sale_line_ids.order_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )
    product_qty = fields.Float(
        _("Necesario"), default=0.0, digits="Product Unit of Measure", required=True
    )
    product_qty_available = fields.Float(
        related="product_id.qty_available", string="Stock", readonly=True, store=True
    )
    product_qty_enter = fields.Float(
        _("A usar"), default=0.0, digits="Product Unit of Measure", required=True
    )
    product_uom_id = fields.Many2one(
        "uom.uom",
        _("Product Unit of Measure"),
        default=_get_default_product_uom_id,
        required=True,
        domain="[('category_id', '=', product_uom_category_id)]",
    )
    product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
    sequence = fields.Integer("Sequence", default=1)

    raw_product_length = fields.Float(
        related="product_id.product_length",
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        string=_("Largo (cm)"),
    )
    raw_product_height = fields.Float(
        related="product_id.product_height",
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        string=_("Alto (cm)"),
    )
    raw_product_uom_id = fields.Many2one(
        related="product_id.dimensional_uom_id", string="UoM", readonly=True
    )

    raw_product_area = fields.Float(
        _("Área de producto"),
        store=True,
        digits=(16, 4),
    )
    raw_product_usable_area = fields.Float(
        _("Área utilizable del producto"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    raw_area_orientation = fields.Selection(
        [
            ("h", "H"),
            ("v", "V"),
        ],
        string=_("H/V"),
        store=True,
    )
    sale_line_ids = fields.Many2many(
        "sale.order.line",
        "sale_order_line_bom_rel",
        "order_line_id",
        "sale_bom_line_id",
        string="Sales Order Lines",
        readonly=True,
        copy=False,
    )
    attachments_count = fields.Integer("Adjuntos", compute="_compute_attachments_count")

    @api.depends("product_id")
    def _compute_attachments_count(self):
        for line in self:
            nbr_attach = self.env["mrp.document"].search_count(
                [
                    "|",
                    "&",
                    ("res_model", "=", "product.product"),
                    ("res_id", "=", line.product_id.id),
                    "&",
                    ("res_model", "=", "product.template"),
                    ("res_id", "=", line.product_id.product_tmpl_id.id),
                ]
            )
            line.attachments_count = nbr_attach

    def action_see_attachments(self):
        domain = [
            "|",
            "&",
            ("res_model", "=", "product.product"),
            ("res_id", "=", self.product_id.id),
            "&",
            ("res_model", "=", "product.template"),
            ("res_id", "=", self.product_id.product_tmpl_id.id),
        ]
        attachment_view = self.env.ref("mrp.view_document_file_kanban_mrp")
        return {
            "name": _("Attachments"),
            "domain": domain,
            "res_model": "mrp.document",
            "type": "ir.actions.act_window",
            "view_id": attachment_view.id,
            "views": [(attachment_view.id, "kanban"), (False, "form")],
            "view_mode": "kanban,tree,form",
            "help": _(
                """<p class="o_view_nocontent_smiling_face">
                        Upload files to your product
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>"""
            ),
            "limit": 80,
            "context": "{'default_res_model': '%s','default_res_id': %d, 'default_company_id': %s}"
            % ("product.product", self.product_id.id, self.company_id.id),
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = "Product dimension split"

    product_pieces_length = fields.Float(_("Largo (cm)"), store=True, default=0.0)
    product_pieces_height = fields.Float(_("Alto (cm)"), store=True, default=0.0)
    product_pieces_area = fields.Float(
        # compute="_computed_product_area",
        string=_("Piece area (cm)"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    product_area = fields.Float(
        # compute="_computed_product_area",
        string=_("Total area (cm)"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        default=0.0,
    )
    product_number_of_pieces = fields.Float(
        # compute="_computed_product_area",
        string=_("Piezas finales del producto"),
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        default=0.0,
    )
    # HOJA DE CORTE
    blade_width = fields.Float(
        _("Ancho de la hoja (cm)"),
        store=True,
        default=0.0,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    blade_affects_lenght = fields.Boolean(
        _("La hoja afecta al largo"), store=True, default=False
    )
    blade_affects_height = fields.Boolean(
        _("La hoja afecta al alto"), store=True, default=False
    )
    product_pieces_length_value = fields.Float(_("Largo (cm)"), store=True)
    product_pieces_height_value = fields.Float(_("Alto (cm)"), store=True)

    sale_line_bom_ids = fields.Many2many(
        "sale.order.line.bom",
        "sale_order_line_bom_rel",
        "sale_bom_line_id",
        "order_line_id",
        string="Componentes",
        copy=False,
    )

    notes = fields.Text(_("Notas"))

    @api.depends("sale_line_bom_ids")
    def _compute_total_available(self):
        for order in self:
            available = 0.0
            for line in order.sale_line_bom_ids:
                available += line.product_qty_enter
                order.update(
                    {
                        "total_available": available,
                    }
                )

    total_available = fields.Float(
        string=_("Total disponible"),
        store=True,
        compute="_compute_total_available",
        tracking=True,
        digits="Product Unit of Measure",
    )

    bom = fields.Many2one(
        comodel_name="mrp.bom",
        string="BoM",
        domain="[('product_tmpl_id.product_variant_ids', '=', product_id),"
        "'|', ('product_id', '=', product_id), "
        "('product_id', '=', False)]",
    )

    @api.constrains("bom_id", "product_id")
    def _check_match_product_variant_ids(self):
        for line in self:
            if line.bom_id:
                bom_product_tmpl = line.bom_id.product_tmpl_id
                bom_product = bom_product_tmpl.product_variant_ids
            else:
                bom_product_tmpl, bom_product = None, None
            line_product = line.product_id
            if not bom_product or line_product == bom_product:
                continue
            raise ValidationError(
                _(
                    "Please select BoM that has matched product with the line `{}`"
                ).format(line_product.name)
            )

    @api.multi
    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        if self.total_available == 0:
            pass
        else:
            if self.total_available <= self.product_area:
                raise UserError(
                    _(
                        "Los componentes disponibles no cubren el área total necesario para cubrir las necesidades del cliente"
                    )
                )

        return res

    @api.onchange(
        "product_pieces_length",
        "product_pieces_height",
        "product_uom_qty",
        "blade_affects_lenght",
        "blade_affects_height",
        "sale_line_bom_ids",
        "sale_line_bom_ids.product_id",
    )
    def _computed_product_area(self):
        # self.ensure_one()
        for line in self:
            # HOJAS DE CORTE
            if line.blade_affects_lenght:
                line.product_pieces_height_value = (
                    line.product_pieces_height + line.blade_width
                )
            else:
                line.product_pieces_height_value = (
                    line.product_pieces_height - line.blade_width
                )

            if line.blade_affects_height:
                line.product_pieces_length_value = (
                    line.product_pieces_length + line.blade_width
                )
            else:
                line.product_pieces_length_value = (
                    line.product_pieces_length - line.blade_width
                )

            line.product_pieces_area = (
                line.product_pieces_height * line.product_pieces_length / 10000
            )
            line.product_area = line.product_uom_qty * line.product_pieces_height / 100
            # if line.product_uom_qty != 0 and line.product_pieces_length != 0:
            #     line.product_number_of_pieces = math.ceil(
            #         line.product_uom_qty / (line.product_pieces_length / 100)
            #     )

    @api.onchange(
        "sale_line_bom_ids.product_id",
        "sale_line_bom_ids",
        "product_pieces_length",
        "product_pieces_height",
        "product_uom_qty",
        "blade_affects_lenght",
        "blade_affects_height",
        "product_uom_id",
    )
    def _computed_raw_product_area(self):
        for line in self.sale_line_bom_ids:
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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for line in self.order_line:
            if not line.bom_id:
                if line.sale_line_bom_ids:
                    # saleorderline_id = self.env.context.get('active_id')
                    vals = {
                        "product_id": line.product_id.id,
                        "product_tmpl_id": line.product_id.product_tmpl_id.id,
                        "product_qty": line.product_uom_qty,
                        "product_uom_id": line.product_uom.id,
                        "code": self.name,
                    }
                    mrp_bom = self.env["mrp.bom"].create(vals)
                    line.write({"bom_id": mrp_bom.id})

                    mrp_bom_line = self.env["mrp.bom.line"]
                    for data in line.sale_line_bom_ids:
                        pdt_value = {
                            "bom_id": mrp_bom.id,
                            "product_id": data.product_id.id,
                            # 'raw_product_length': data.raw_product_length,
                            # 'raw_product_height': data.raw_product_height,
                            "raw_product_uom_id": data.raw_product_uom_id.id,
                            "raw_product_area": data.raw_product_area,
                            "raw_product_usable_area": data.raw_product_usable_area,
                            "raw_area_orientation": data.raw_area_orientation,
                            "product_qty": data.product_qty,
                        }
                        mrp_bom_line.create(pdt_value)

        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        if self.sale_line_id and self.sale_line_id.bom_id:
            values["bom_id"] = self.sale_line_id.bom_id
        return values
