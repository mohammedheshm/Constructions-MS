from odoo import api, fields, models, exceptions
from odoo.exceptions import ValidationError


class ConstructionProject(models.Model):
    _name = 'construction.project'
    _description = 'Projects'
    _rec_name = 'project_name'

    site_ids = fields.One2many('construction.site', 'project_id', string='Sites')
    workforce_ids = fields.Many2many(
        'construction.workforce',
        string='Workforce',
        compute='_compute_workforce',
        store=False,
        readonly=True,
    )
    expense_ids = fields.One2many(
        'construction.expense',
        'project_id',
        string='Expenses',
        readonly=True,
    )

    project_name = fields.Char(string='Project Name', required=True)
    project_code = fields.Char(default='New', string='Project Code', readonly=True)
    customer = fields.Char(string='Customer')
    project_manager = fields.Many2one('res.users', string='Project Manager')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    budget = fields.Float(string='Budget')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('closed', 'Closed'),
    ], string='State', default='draft', required=True)
    description = fields.Text(string='Description', required=True)

    total_expense = fields.Float(
        string="Total Expense",
        compute="_compute_total_expense"
    )
    total_material_cost = fields.Float(
        string="Total Material Cost",
        compute="_compute_total_material_cost"
    )

    total_project_cost = fields.Float(
        string="Total Project Cost",
        compute="_compute_total_project_cost"
    )

    contract_value = fields.Float(
        string="Contract Value",
        required=True
    )

    invoice_ids = fields.One2many(
        'construction.invoice',
        'project_id',
        string='Invoices'
    )

    total_paid = fields.Float(
        string="Total Paid",
        compute="_compute_total_paid",
        store=True
    )

    remaining_amount = fields.Float(
        string="Remaining Amount",
        compute="_compute_remaining_amount",
        store=True
    )

    net_profit = fields.Float(
        string="Net Profit",
        compute="_compute_net_profit",
        store=True
    )

    remaining_status = fields.Char(
        string="Payment Status",
        compute="_compute_remaining_status",
        store=True
    )

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_done(self):
        for rec in self:
            if rec.state != 'done':
                rec.state = 'done'

    def action_close(self):
        for rec in self:
            rec.state = 'closed'

    @api.model
    def create(self, vals):
        if vals.get('project_code', 'New') == 'New':
            vals['project_code'] = self.env['ir.sequence'].next_by_code('project_seq') or 'New'
        return super(ConstructionProject, self).create(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError('End Date must be after Start Date!')

    @api.depends('site_ids.workforce_ids')
    def _compute_workforce(self):
        for project in self:
            project.workforce_ids = project.site_ids.mapped('workforce_ids')

    @api.depends('expense_ids.amount')
    def _compute_total_expense(self):
        for rec in self:
            rec.total_expense = sum(rec.expense_ids.mapped('amount'))

    @api.depends('site_ids.total_material_cost')
    def _compute_total_material_cost(self):
        for rec in self:
            rec.total_material_cost = sum(rec.site_ids.mapped('total_material_cost'))

    @api.depends('total_material_cost', 'total_expense')
    def _compute_total_project_cost(self):
        for rec in self:
            rec.total_project_cost = rec.total_material_cost + rec.total_expense

    @api.depends('invoice_ids.paid_amount', 'invoice_ids.state', 'total_project_cost')
    def _compute_total_paid(self):
        for rec in self:
            total_paid = sum(rec.invoice_ids.filtered(lambda i: i.state == 'paid').mapped('paid_amount'))
            rec.total_paid = total_paid
            rec.remaining_amount = max(rec.total_project_cost - total_paid, 0.0)

    @api.depends('contract_value', 'total_paid')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.contract_value - rec.total_paid

    @api.depends('total_paid', 'total_project_cost')
    def _compute_net_profit(self):
        for rec in self:
            rec.net_profit = rec.total_paid - rec.total_project_cost

    @api.depends('remaining_amount')
    def _compute_remaining_status(self):
        for rec in self:
            if rec.remaining_amount <= 0:
                rec.remaining_status = "Fully Paid ✅"
            else:
                rec.remaining_status = f"Remaining: {rec.remaining_amount}"
