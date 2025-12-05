# Copyright 2013-2025, MTNET SERVICES
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL.html).

import calendar
import logging

from odoo import _, api, fields, models

logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    repse_line_ids = fields.One2many('document.repse.line','purchase_order_id', string="Purchases")
    repse_state = fields.Char(compute="_compute_repse_count")
    repse_count = fields.Integer(compute="_compute_repse_count")

    @api.depends('repse_line_ids')
    def _compute_repse_count(self):
        for rec in self:
            repse_ids = []
            for line in rec.sudo().repse_line_ids.filtered(lambda x: x.repse_document_id.state == 'process' and x.repse_document_id.state):
                if not line.repse_document_id.id in repse_ids:
                    repse_ids.append(line.repse_document_id.id)
            
            rec.update({'repse_count': len(repse_ids), 'repse_state': 'In Process' if any(rec.repse_line_ids.filtered(lambda x: x.repse_document_id.state != 'positive')) else 'Valid'})

    def action_view_repse_documents(self):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        self.ensure_one()
        repse_ids = []
        for line in self.repse_line_ids.filtered(lambda x: x.repse_document_id.state == 'process'):
            if not line.repse_document_id.id in repse_ids:
                repse_ids.append(line.repse_document_id.id)
        action = self.env["ir.actions.act_window"]._for_xml_id("repse_mtnmx.action_document_repse")
        action["context"] = {
            "active_test": False,
        }
        action["domain"] = [("id", "in", repse_ids)]
        return action

    def button_confirm(self):
        res = super().button_confirm()
        for rec in self:
            rec.action_create_repse(rec)

        return res

    def button_cancel(self):
        self.ensure_one()
        if self.repse_line_ids:
            for line in self.repse_line_ids:
                if not line.repse_document_id.repse_line_ids:
                    line.repse_document_id.write({"state": "cancel"})

        return super().button_cancel()

    def action_create_repse(self, purchase_id=False):
        for rec in purchase_id:
            user_id = self.env["res.users"].search([("partner_id", "=", rec.partner_id.id)])
            if user_id.has_group("repse_mtnmx.group_repse_portal"):
                sp_cont_product_ids = self.env["product.product"].search(
                    [("purchase_ok", "=", True), ("default_code", "ilike", "SP Cont")]
                )
                if any(line.product_id.id in sp_cont_product_ids.ids for line in rec.order_line):
                    purchase_date = rec.date_approve.date()
                    year = str(purchase_date.year)
                    month = str(purchase_date.month) if purchase_date.month >= 10 else "0" + str(purchase_date.month)

                    last_day = calendar.monthrange(int(year), int(month))
                    repse_date_start = year + "-" + month + "-01"
                    repse_date_end = year + "-" + month + "-" + str(last_day[1])

                    repse_id = (
                        self.env["document.repse"]
                        .sudo()
                        .search(
                            [
                                ("partner_id", "=", rec.partner_id.id),
                                ("repse_date", ">=", repse_date_start),
                                ("repse_date", "<=", repse_date_end),
                            ]
                        )
                    )

                    if not repse_id:
                        repse_id = (
                            self.env["document.repse"]
                            .sudo()
                            .create(
                                {
                                    "partner_id": rec.partner_id.id,
                                    "repse_date": rec.date_approve.date(),
                                }
                            )
                        )

                    if repse_id.state == "cancel":
                        repse_id.write({"state": "process"})

                    repse_line_id = (
                        self.env["document.repse.line"]
                        .sudo()
                        .search([("repse_document_id", "=", repse_id.id), ("purchase_order_id", "=", rec.id)])
                    )

                    if not repse_line_id:
                        repse_line_id = (
                            self.env["document.repse.line"]
                            .sudo()
                            .create(
                                {
                                    "name": rec.name,
                                    "repse_document_id": repse_id.id,
                                    "purchase_order_id": rec.id,
                                }
                            )
                        )

                    repse_id.sudo().message_post(
                        body=_("Purchase order {} added").format(repse_line_id.purchase_order_id.display_name),
                        message_type="notification",
                        author_id=user_id.partner_id.id,
                    )

        return True

    def action_add_repse(self):
        purchase_order_ids = self.env["purchase.order"].search([("id", "in", self.env.context.get("active_ids"))])
        for purchase_order_id in purchase_order_ids.filtered(lambda x: x.state in ["purchase", "done"]):
            self.action_create_repse(purchase_order_id)
