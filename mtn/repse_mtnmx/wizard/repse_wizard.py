import calendar
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class RepseWizard(models.TransientModel):
    _name = "repse.wizard"
    _description = "Repse wizard for extemporaneous documents"

    partner_id = fields.Many2one("res.partner", string="Supplier")
    all_partners = fields.Boolean(
        help="""With this option all partner that apply for repse and do not has their four period documents,
         gonna be retrieve to create their missing document"""
    )
    all_periods = fields.Boolean(
        help="""With this option all periods will be considered to create their corresponding documents in case
        they have not been created previously."""
    )
    date = fields.Date(string="Repse Date", default=date.today())
    repse_partners = fields.Integer(compute="_compute_repse_partners")

    @api.depends('date')
    def _compute_repse_partners(self):
        for rec in self:
            repse_group_id = self.env.ref("repse_mtnmx.group_repse_portal")
            for user in repse_group_id.users.filtered(lambda x: not x.partner_id.repse_group):
                user.partner_id.sudo().write({'repse_group':True})
            rec.repse_partners = len(repse_group_id.users)

    def action_process(self):
        for rec in self:
            partner_ids = (
                self.env["res.users"].search([]).filtered(lambda x: x.has_group("repse_mtnmx.group_repse_portal"))
                if rec.all_partners
                else [rec.partner_id]
            )
            for partner in partner_ids:
                p_id = partner.partner_id.id if rec.all_partners else partner.id
                year = str(rec.date.year)
                ratio = 1
                wizard_date = rec.date
                if rec.all_periods:
                    ratio = wizard_date.month
                    wizard_date -= relativedelta(months=ratio - 1)

                for mon in range(ratio):
                    wizard_date += relativedelta(months=1 if mon > 0 else 0)
                    month = "0" + str(wizard_date.month) if wizard_date.month < 10 else str(wizard_date.month)

                    last_day = calendar.monthrange(wizard_date.year, wizard_date.month)
                    repse_date_start = year + "-" + month + "-01"
                    repse_date_end = year + "-" + month + "-" + str(last_day[1])

                    bp_repse_id = (
                        self.env["document.repse"]
                        .sudo()
                        .search(
                            [
                                ("repse_date", ">=", repse_date_start),
                                ("repse_date", "<=", repse_date_end),
                                ("partner_id", "=", p_id),
                            ]
                        )
                    )

                    if not bp_repse_id:
                        bp_repse_id = (
                            self.env["document.repse"]
                            .sudo()
                            .create(
                                {
                                    "partner_id": p_id,
                                    "repse_date": wizard_date,
                                }
                            )
                        )

            return {
                "type": "ir.actions.client",
                "tag": "reload",
            }
