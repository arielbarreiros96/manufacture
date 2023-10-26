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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = "Product dimension split"

    product_pieces_length = fields.Float(_("Largo (cm)"), store=True, default=0.0)
    product_pieces_height = fields.Float(_("Alto (cm)"), store=True, default=0.0)
    product_pieces_width = fields.Float(_("Espesor (cm)"), store=True, default=0.0)
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
    product_pieces_width_value = fields.Float(_("Espesor (cm)"), store=True)

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

    bom_id = fields.Many2one(
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

    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        # Bypass Validation
        # if self.total_available == 0:
        #     pass
        # else:
        #     if self.total_available <= self.product_area:
        #         raise UserError(
        #             _(
        #                 "Los componentes disponibles no cubren el área total necesario para cubrir las necesidades del cliente"
        #             )
        #         )
        return res

    # def _computed_product_area_deprecated(self):
    #     # self.ensure_one()
    #     for line in self:
    #         # HOJAS DE CORTE
    #         if line.blade_affects_lenght:
    #             line.product_pieces_height_value = (
    #                 line.product_pieces_height + line.blade_width
    #             )
    #         else:
    #             line.product_pieces_height_value = (
    #                 line.product_pieces_height - line.blade_width
    #             )
    #
    #         if line.blade_affects_height:
    #             line.product_pieces_length_value = (
    #                 line.product_pieces_length + line.blade_width
    #             )
    #         else:
    #             line.product_pieces_length_value = (
    #                 line.product_pieces_length - line.blade_width
    #             )
    #
    #         line.product_pieces_area = (
    #             line.product_pieces_height * line.product_pieces_length / 10000
    #         )
    #         if (
    #             line.product_uom
    #             and line.product_uom.id
    #             == self.env.ref("sale_dimension_split.product_uom_area").id
    #         ):
    #             line.product_area = line.product_uom_qty
    #         else:
    #             line.product_area = (
    #                 line.product_uom_qty * line.product_pieces_height / 100
    #             )
    #         if line.product_uom_qty != 0 and line.product_pieces_length != 0:
    #             if (
    #                 line.product_uom
    #                 and line.product_uom.id
    #                 == self.env.ref("sale_dimension_split.product_uom_area").id
    #             ):
    #                 # metros cuadrados
    #                 if line.product_pieces_length and line.product_pieces_height:
    #                     line.product_number_of_pieces = math.ceil(
    #                         line.product_uom_qty
    #                         / (
    #                             (
    #                                 line.product_pieces_length
    #                                 * line.product_pieces_height
    #                             )
    #                             / 10000
    #                         )
    #                     )
    #             else:
    #                 line.product_number_of_pieces = math.ceil(
    #                     line.product_uom_qty / (line.product_pieces_length / 100)
    #                 )
    #
    #         if (
    #             line.product_uom
    #             and line.product_uom.id == self.env.ref("uom.product_uom_unit").id
    #         ):
    #             line.product_number_of_pieces = line.product_uom_qty
    #             line.product_area = 0.0
    #
    #         if (
    #             line.product_uom
    #             and line.product_uom.id == self.env.ref("uom.product_uom_unit").id
    #             and line.sale_line_bom_ids.product_id.uom_id.id
    #             == self.env.ref("sale_dimension_split.product_uom_area").id
    #         ):
    #             a = (
    #                 line.sale_line_bom_ids.raw_product_length
    #                 // line.product_pieces_length
    #             )
    #             b = (
    #                 line.sale_line_bom_ids.raw_product_height
    #                 // line.product_pieces_height
    #             )
    #             c = a * b
    #             if c != 0:
    #                 d = math.ceil(line.product_uom_qty / c)
    #             else:
    #                 d = 0
    #
    #             line.sale_line_bom_ids.product_qty = d * line.product_pieces_area
    #
    #         if (
    #             line.product_uom
    #             and line.product_uom.id == self.env.ref("uom.product_uom_unit").id
    #             and line.sale_line_bom_ids.product_id.uom_id.id
    #             == self.env.ref("uom.product_uom_meter").id
    #         ):
    #             a = (
    #                 line.sale_line_bom_ids.raw_product_length
    #                 // line.product_pieces_length
    #             )
    #
    #             line.sale_line_bom_ids.product_qty = (
    #                 a * line.product_uom_qty * line.product_pieces_length / 100
    #             )
    #
    #         if (
    #             line.product_uom
    #             and line.product_uom.id == self.env.ref("uom.product_uom_meter").id
    #             and line.sale_line_bom_ids.product_id.uom_id.id
    #             == self.env.ref("uom.product_uom_meter").id
    #         ):
    #             a = (
    #                 line.sale_line_bom_ids.raw_product_length
    #                 // line.product_pieces_length
    #             )
    #             b = (
    #                 line.sale_line_bom_ids.raw_product_height
    #                 // line.product_pieces_height
    #             )
    #             c = a * b
    #             if c!=0:
    #                 line.sale_line_bom_ids.product_qty = line.sale_line_bom_ids.raw_product_length / c

    # @api.onchange(
    #     "sale_line_bom_ids.product_id",
    # )
    # def _computed_set_sizes_default(self):
    #     for line in self:
    #         #Try to set the length and height of the raw material to some default values
    #         if not line.sale_line_bom_ids:
    #             line.product_pieces_length = line.product_id.product_length
    #             line.product_pieces_height = line.product_id.product_height
    #             line.product_pieces_width = line.product_id.product_width
    #         else:
    #             line.product_pieces_length = line.sale_line_bom_ids[0].product_id.product_length
    #             line.product_pieces_height = line.sale_line_bom_ids[0].product_id.product_height
    #             line.product_pieces_width = line.sale_line_bom_ids[0].product_id.product_width
    #
    # @api.onchange(
    #     "product_id",
    # )
    # def _rename_product_line(self):
    #     for line in self:
    #         # line.name = line.product_id.name
    #         line.name = "PEPE"


    @api.onchange(
        "product_id",
        "product_pieces_length",
        "product_pieces_height",
        "product_uom_qty",
        "blade_affects_lenght",
        "blade_affects_height",
        "sale_line_bom_ids",
        "sale_line_bom_ids.product_id",
    )
    def _computed_product_area(self):

        # Cálculo de area que se necesita consumir en cada linea
        for line in self:
            # Cálculo el area de las piezas a producir
            line.product_pieces_area = line.product_pieces_height * line.product_pieces_length / 10000

            # Cálculo del area total de las piezas, si aplica, segun los casos de uso
            if (
                line.product_uom
                and line.product_uom.id
                == self.env.ref("sale_dimension_split.product_uom_area").id
            ):
                line.product_area = line.product_uom_qty
                if line.product_pieces_length != 0 and line.product_pieces_height != 0:
                    line.product_number_of_pieces = math.ceil(
                        line.product_uom_qty
                        / (
                                (
                                        line.product_pieces_length
                                        * line.product_pieces_height
                                )
                                / 10000
                        )
                    )

            elif (
                line.product_uom
                and line.product_uom.id == self.env.ref("uom.product_uom_unit").id
            ):
                line.product_area = 0.0
                line.product_number_of_pieces = line.product_uom_qty

            else:
                # Este es el caso restante, m lineales
                if (
                    line.product_pieces_height != 0 and line.product_pieces_length != 0
                ):
                    line.product_number_of_pieces = math.ceil(
                        line.product_uom_qty / (max(line.product_pieces_length, line.product_pieces_height) / 100)
                    )
                    line.product_area = line.product_number_of_pieces * (
                        line.product_pieces_length * line.product_pieces_height / 10000
                    )

            # Cálculo de cuántas piezas se pueden sacar de cada componente
            # Init
            for bom_line in line.sale_line_bom_ids:

                pieces_from_hei1 = 0
                pieces_from_len1 = 0
                pieces_from_hei2 = 0
                pieces_from_len2 = 0
                pieces_needed = 0

                if line.product_pieces_length != 0:
                    pieces_from_len1 = bom_line.raw_product_length // line.product_pieces_length
                    pieces_from_hei2 = bom_line.raw_product_height // line.product_pieces_length
                if line.product_pieces_height != 0:
                    pieces_from_hei1 = bom_line.raw_product_height // line.product_pieces_height
                    pieces_from_len2 = bom_line.raw_product_length // line.product_pieces_height

                pieces_from_raw_material1 = pieces_from_len1 * pieces_from_hei1
                pieces_from_raw_material2 = pieces_from_len2 * pieces_from_hei2

                pieces_from_raw_material = max(pieces_from_raw_material1, pieces_from_raw_material2)
                if pieces_from_raw_material != 0:
                    pieces_needed = math.ceil(line.product_number_of_pieces / pieces_from_raw_material)

                # Casos de uso:
                # 1. Si la unidad de medida de la línea es m2 y la del componente es m2
                # 2. Si la unidad de medida de la línea es m2 y la del componente es m
                # 3. Si la unidad de medida de la línea es m y la del componente es m2
                # 4. Si la unidad de medida de la línea es m y la del componente es m
                # 5. Si la unidad de medida de la línea es ud y la del componente es m2
                # 6. Si la unidad de medida de la línea es ud y la del componente es m
                # 7. Si la unidad de medida de la línea es ud y la del componente es ud

                # 1. Si la unidad de medida de la línea es m2 y la del componente es m2
                if (
                    line.product_uom
                    and line.product_uom.id == self.env.ref("sale_dimension_split.product_uom_area").id
                    and bom_line.product_id.uom_id.id
                    == self.env.ref("sale_dimension_split.product_uom_area").id
                ):
                    bom_line.product_qty = pieces_needed * bom_line.raw_product_area

                # 2. Si la unidad de medida de la línea es m2 y la del componente es m
                if (
                    line.product_uom
                    and line.product_uom.id == self.env.ref("sale_dimension_split.product_uom_area").id
                    and bom_line.product_id.uom_id.id
                    == self.env.ref("uom.product_uom_meter").id
                ):
                    bom_line.product_qty = (pieces_needed
                                                          * bom_line.raw_product_length / 100)

                # 3. Si la unidad de medida de la línea es m y la del componente es m2
                if (
                    line.product_uom
                    and line.product_uom.id == self.env.ref("uom.product_uom_meter").id
                    and bom_line.product_id.uom_id.id
                    == self.env.ref("sale_dimension_split.product_uom_area").id
                ):
                    bom_line.product_qty = pieces_needed * bom_line.raw_product_area

                # 4. Si la unidad de medida de la línea es m y la del componente es m
                if (
                    line.product_uom
                    and line.product_uom.id == self.env.ref("uom.product_uom_meter").id
                    and bom_line.product_id.uom_id.id
                    == self.env.ref("uom.product_uom_meter").id
                ):
                    bom_line.product_qty = (pieces_needed
                                                          * bom_line.raw_product_length / 100)

                # 5. Si la unidad de medida de la línea es ud y la del componente es m2
                if (
                    line.product_uom
                    and line.product_uom.id == self.env.ref("uom.product_uom_unit").id
                    and bom_line.product_id.uom_id.id
                    == self.env.ref("sale_dimension_split.product_uom_area").id
                ):
                    bom_line.product_qty = pieces_needed * bom_line.raw_product_area

                # 6. Si la unidad de medida de la línea es ud y la del componente es m
                if (
                    line.product_uom
                    and line.product_uom.id == self.env.ref("uom.product_uom_unit").id
                    and bom_line.product_id.uom_id.id
                    == self.env.ref("uom.product_uom_meter").id
                ):
                    bom_line.product_qty = (pieces_needed
                                                          * bom_line.raw_product_length / 100)

                # 7. Si la unidad de medida de la línea es ud y la del componente es ud
                if (
                    line.product_uom
                    and line.product_uom.id == self.env.ref("uom.product_uom_unit").id
                    and bom_line.product_id.uom_id.id
                    == self.env.ref("uom.product_uom_unit").id
                ):
                    bom_line.product_qty = line.product_uom_qty

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
            if (
                self.product_uom
                and self.product_uom.id
                == self.env.ref("sale_dimension_split.product_uom_area").id
            ):
                line.raw_area_orientation = "h"
                temp = area_h
                if area_v >= area_h:
                    temp = area_v
                are = self.product_pieces_height * self.product_pieces_length / 10000
                line.raw_product_usable_area = temp * are

            else:
                if raw_product_usable_area_h >= raw_product_usable_area_v:
                    line.raw_product_usable_area = raw_product_usable_area_h
                    line.raw_area_orientation = "h"
                else:
                    line.raw_product_usable_area = raw_product_usable_area_v
                    line.raw_area_orientation = "v"
            line.raw_product_area = round(
                line.raw_product_length * line.raw_product_height / 10000 , 4
            )

            if self.product_area != 0 and line.raw_product_usable_area != 0:
                if (
                    self.product_uom
                    and self.product_uom.id
                    == self.env.ref("sale_dimension_split.product_uom_area").id
                ):
                    temp = area_h
                    if area_v >= area_h:
                        temp = area_v
                    line.product_qty = (
                        math.ceil((self.product_number_of_pieces / temp))
                        * line.raw_product_area
                    )

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id=group_id)
        values.update(
            {
                "group_id": group_id or False,
                "bom_id": self.bom_id or False,
                "product_pieces_length": self.product_pieces_length or 0.0,
                "product_pieces_height": self.product_pieces_height or 0.0,
                "product_pieces_width": self.product_pieces_width or 0.0,
                "product_number_of_pieces": self.product_number_of_pieces or 0.0,
            }
        )
        return values
