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
