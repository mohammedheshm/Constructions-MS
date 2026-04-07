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
    amount_total = fields.Float(string='Total Amount', compute='_compute_total_amount', readonly=True)
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
    def _compute_total_amount(self):
        for rec in self:
            if rec.project_id:
                rec.amount_total = rec.project_id.total_project_cost
            else:
                rec.amount_total = 0.0

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
            rec.state = 'posted'

    def action_paid(self):
        for rec in self:
            if rec.project_id:
                # مجموع المدفوع بالفعل بدون هذه الفاتورة
                paid_so_far = sum(rec.project_id.invoice_ids.filtered(
                    lambda i: i.state == 'paid' and i.id != rec.id
                ).mapped('paid_amount'))

                remaining_for_project = rec.project_id.total_project_cost - paid_so_far
                if rec.paid_amount > remaining_for_project:
                    raise ValidationError(
                        f"Paid Amount ({rec.paid_amount}) cannot exceed remaining project cost ({remaining_for_project})!"
                    )
            rec.state = 'paid'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.constrains('paid_amount', 'state', 'project_id')
    def _check_paid_amount(self):
        for rec in self:
            if rec.state == 'paid' and rec.project_id:
                paid_so_far = sum(rec.project_id.invoice_ids.filtered(
                    lambda i: i.state == 'paid' and i.id != rec.id
                ).mapped('paid_amount'))

                remaining_for_project = rec.project_id.total_project_cost - paid_so_far

                if rec.paid_amount > remaining_for_project:
                    raise ValidationError(
                        f"Paid Amount ({rec.paid_amount}) cannot exceed remaining project cost ({remaining_for_project})!"
                    )
