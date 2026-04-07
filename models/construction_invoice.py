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
        domain="[('project_id','=',project_id)]")
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


    @api.depends('expense_ids.amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.amount_total = sum(rec.expense_ids.mapped('amount'))

    @api.depends('project_id', 'site_ids')
    def _compute_expenses(self):
        for rec in self:
            domain = [('project_id', '=', rec.project_id.id)]
            if rec.site_ids:
                domain.append(('site_id', '=', rec.site_ids.ids))
            rec.expense_ids = self.env['construction.expense'].search(domain)

    def action_post(self):
        for rec in self:
            rec.state = 'posted'

    def action_paid(self):
        for rec in self:
            rec.state = 'paid'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
