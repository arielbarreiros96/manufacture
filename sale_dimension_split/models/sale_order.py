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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        
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
                            "product_qty": data.product_qty_enter,
                        }
                        mrp_bom_line.create(pdt_value)

        res = super(SaleOrder, self).action_confirm()
        
        return res
