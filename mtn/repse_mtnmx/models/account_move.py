# Copyright 2013-2025, MTNET SERVICES
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL.html).

from datetime import date

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    repse_state = fields.Selection(
        [("process", "Process"), ("positive", "Positive"), ("cancel", "Cancelled")],
        string="Repse state",
        default="process",
    )
    repse_id = fields.Many2one("document.repse", string="REPSE")
    repse_in_process_count = fields.Integer(compute="_compute_repse")
    repse_ids = fields.One2many(
        "document.repse", "move_id", domain=[("state", "=", "process")], string="Repses", compute="_compute_repse"
    )
    repse_group = fields.Boolean()

    @api.depends('partner_id')
    def _compute_repse(self):
        for rec in self:
            repse_in_process_count = 0
            repse_state = False
            user_id = self.env["res.users"].search([("partner_id", "=", rec.partner_id.id)])
            
            if user_id.has_group("repse_mtnmx.group_repse_portal"):
                repse_ids = (
                    self.env["document.repse"]
                    .sudo()
                    .search(
                        [
                            ("state", "=", 'process'),
                            ("partner_id", "=", rec.partner_id.id),
                        ]
                    )
                )
                rec.repse_ids = repse_ids.ids
                repse_state = "process" if repse_ids.filtered(lambda x: x.state != 'positive') else "positive"

                repse_in_process_count = len(repse_ids.filtered(lambda x: x.state == "process").ids)
            rec.update({
                "repse_in_process_count": repse_in_process_count, 
                "repse_state": repse_state,
                "repse_group": user_id.has_group("repse_mtnmx.group_repse_portal")})

    def action_view_in_process(self):
        self.ensure_one()
        user_id = self.env["res.users"].search([("partner_id", "=", self.partner_id.id)])
        if user_id.has_group("repse_mtnmx.group_repse_portal"):
            action = self.env["ir.actions.act_window"]._for_xml_id("repse_mtnmx.action_document_repse")
            action["context"] = {
                "active_test": False,
            }
            action["domain"] = [("state", "=", "process"), ("partner_id", "=", self.partner_id.id)]
            return action

    def action_post(self):
        for move in self:
            if move.repse_in_process_count > 0:
                missing_repse = ""
                for nrepse in move.repse_ids:
                    missing_repse += nrepse.name + "\n"
                msg = _("This partner have incomplete repse documentationn: %s", missing_repse)
                move.message_post(body=msg, message_type="comment", author_id=self.env.ref("base.partner_root").id)
                self.env["bus.bus"]._sendone(
                    self.env.user.partner_id,
                    "simple_notification",
                    {
                        "type": "danger",
                        "title": _("Warning"),
                        "message": (
                            "This partner have incomplete repse documentation in the following documents: %s,",
                            missing_repse,
                        ),
                    },
                )
        return super().action_post()
