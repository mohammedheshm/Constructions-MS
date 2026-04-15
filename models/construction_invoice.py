from odoo import fields, api, models
from odoo.exceptions import ValidationError


class ConstructionInvoice(models.Model):
    _name = 'construction.invoice'
    _description = 'Invoices'
    _rec_name = 'invoice_number'
    _order = 'invoice_date desc'

    invoice_number = fields.Char(string='Invoice Number', required=True, default='New')
    project_id = fields.Many2one('construction.project', string='Project', required=True)
    site_ids = fields.Many2many(
        'construction.site',
        string='Sites',
        compute='_compute_sites',
        store=False,
        readonly=True
    )

    expense_ids = fields.One2many(
        'construction.expense',
        string='Related Expenses',
        compute='_compute_expenses'
    )
    invoice_date = fields.Date(string='Invoice Date', required=True, default=fields.Date.context_today)
    amount_total = fields.Float(string='Total Amount', readonly=True)
    notes = fields.Text(string='Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('paid', 'Paid'),
    ], default='draft', string='Status', tracking=True)

    paid_amount = fields.Float(
        string="Paid Amount",
        default=0.0,
    )
    payment_date = fields.Date(
        string="Payment Date",
    )

    @api.depends('project_id')
    def _compute_sites(self):
        for rec in self:
            if rec.project_id:
                rec.site_ids = rec.project_id.site_ids
            else:
                rec.site_ids = rec.env['construction.site'].browse([])

    @api.depends('project_id')
    def _compute_expenses(self):
        for rec in self:
            if rec.project_id:
                rec.expense_ids = self.env['construction.expense'].search([
                    ('project_id', '=', rec.project_id.id)
                ])
            else:
                rec.expense_ids = self.env['construction.expense'].browse([])

    def action_post(self):
        for rec in self:

            if not rec.project_id:
                raise ValidationError("Project is required.")

            if rec.amount_total <= 0:
                raise ValidationError("Invoice amount must be greater than 0.")

            remaining = rec.project_id.contract_value - rec.project_id.total_paid

            if remaining <= 0:
                raise ValidationError("Contract already fully paid.")

            if rec.amount_total > remaining:
                raise ValidationError(
                    f"Cannot post invoice. Amount ({rec.amount_total}) exceeds remaining contract ({remaining})."
                )

            rec.state = 'posted'

    def action_paid(self):
        for rec in self:

            if rec.project_id:
                remaining = rec.project_id.contract_value - rec.project_id.total_paid

                if rec.paid_amount > remaining:
                    raise ValidationError(
                        f"Paid Amount ({rec.paid_amount}) exceeds remaining contract ({remaining})!"
                    )

            rec.state = 'paid'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.constrains('paid_amount', 'state', 'project_id')
    def _check_paid_amount(self):
        for rec in self:

            if rec.state == 'paid' and rec.project_id:

                paid_so_far = sum(
                    rec.project_id.invoice_ids.filtered(
                        lambda i: i.state == 'paid' and i.id != rec.id
                    ).mapped('paid_amount')
                )

                remaining_contract = rec.project_id.contract_value - paid_so_far

                if rec.paid_amount > remaining_contract:
                    raise ValidationError(
                        f"Paid Amount ({rec.paid_amount}) exceeds remaining contract ({remaining_contract})!"
                    )


    def _get_remaining_contract(self, project):
        return project.contract_value - project.total_paid

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for rec in self:
            if rec.project_id:
                rec.amount_total = self._get_remaining_contract(rec.project_id)
            else:
                rec.amount_total = 0.0

    @api.model
    def create(self, vals):

        if vals.get('project_id'):
            project = self.env['construction.project'].browse(vals['project_id'])

            remaining = project.contract_value - project.total_paid

            amount = vals.get('amount_total')

            if amount in [None, False]:
                amount = remaining

            if amount <= 0:
                raise ValidationError("Invoice amount must be greater than 0.")

            if amount > remaining:
                raise ValidationError(
                    f"Cannot create invoice. Amount ({amount}) exceeds remaining contract ({remaining})."
                )

            vals['amount_total'] = amount

        return super().create(vals)
