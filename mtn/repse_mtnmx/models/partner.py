from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    repse_count = fields.Integer(compute="_compute_repse")
    repse_positive_count = fields.Integer(compute="_compute_repse")
    repse_cancelled_count = fields.Integer(compute="_compute_repse")
    repse_process_count = fields.Integer(compute="_compute_repse")
    repse_ids = fields.One2many("document.repse", "partner_id", string="Repses")
    repse_group = fields.Boolean()

    api.depends("name")
    def _compute_repse(self):
        for rec in self:
            rec.repse_count = 0
            rec.repse_positive_count = 0
            rec.repse_cancelled_count = 0
            rec.repse_process_count = 0
            if self.env.user.has_group("repse_mtnmx.group_repse_manager") or self.env.user.has_group(
                "repse_mtnmx.group_repse_user"
            ):
                user_id = self.env["res.users"].sudo().search([("partner_id", "=", rec.id)])
                repse_group = bool(user_id.has_group("repse_mtnmx.group_repse_portal"))

                repse_data = self.env["document.repse"].sudo().search([("partner_id", "=", rec.id)])
                rec.sudo().update(
                    {
                        "repse_count": len(repse_data),
                        "repse_positive_count": len(repse_data.filtered(lambda x: x.state == "positive")),
                        "repse_cancelled_count": len(repse_data.filtered(lambda x: x.state == "cancel")),
                        "repse_process_count": len(repse_data.filtered(lambda x: x.state == "process")),
                        "repse_group": repse_group,
                    }
                )

    @api.onchange("name")
    def onchange_repse(self):
        for rec in self:
            rec._compute_repse()

    def action_view_repse(self, repses=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        action = self.env["ir.actions.act_window"]._for_xml_id("repse_mtnmx.action_document_repse")
        action["context"] = {
            "active_test": False,
        }
        action["domain"] = [("partner_id.id", "=", self.id)]
        return action
