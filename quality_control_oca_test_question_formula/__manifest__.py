# Copyright 2010 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014-2021 Tecnativa Pedro M. Baeza
# Copyright 2014 Oihane Crucelaegui - AvanzOSC
# Copyright 2017-2020 ForgeFlow S.L.
# Copyright 2017 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Quality Control OCA Test Question Formula",
    "version": "17.0.1.2.0",
    "category": "Quality Control",
    "license": "AGPL-3",
    "summary": "Extra question type for Quality Control Tests",
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/manufacture",
    "depends": ["quality_control_oca"],
    "data": [
        "views/qc_test_views.xml",
    ],
    "demo": ["demo/quality_control_demo.xml"],
    "installable": True,
}
