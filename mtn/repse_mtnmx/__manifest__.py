# Copyright 2013-2025, MTNET SERVICES
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL.html).


{
    "name": "REPSE",
    "summary": "REPSE Management",
    "version": "17.0.1.0.1",
    "category": "Documents",
    "author": "Odoo Community Association (OCA),Nubuserp",
    "website": "https://nubuserp.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "portal",
        "contacts",
        "purchase",
        "mail",
        "mail_activity_team",
    ],
    "data": [
        "data/cron_data.xml",
        "data/data.xml",
        "security/repse_security.xml",
        "security/ir.model.access.csv",
        "views/account_view.xml",
        "views/partner_view.xml",
        "views/purchase_view.xml",
        "views/repse_view.xml",
        "views/portal_template.xml",
        "wizard/repse_wizard_view.xml",
    ],
    "installable": True,
}
