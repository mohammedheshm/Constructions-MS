from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionSite(models.Model):
    _name = 'construction.site'
    _description = 'Sites'
    _rec_name = 'site_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one('construction.project', string='Projects')
    site_name = fields.Char(string='Site Name', tracking=True)
    site_code = fields.Char(default='New', string='Site Code', readonly=True)
    location = fields.Char(string='Location', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    duration = fields.Integer(string="Duration (Days)", compute='_compute_duration', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', required=True, tracking=True)

    workforce_count = fields.Integer(string='Workforce Count', compute='_compute_workforce_counts', readonly=True)
    workforce_ids = fields.Many2many('construction.workforce', string='Workforce')

    expense_ids = fields.One2many(
        'construction.expense',
        'site_id',
        string='Expenses',
        readonly=True,
    )

    material_ids = fields.One2many(
        'construction.site.material',
        'site_id',
        string='Materials',
    )
    total_material_cost = fields.Float(
        string='Total Material Cost',
        compute='_compute_total_material_cost',
        readonly=True,
    )

    total_expense = fields.Float(
        string="Total Expense",
        compute="_compute_total_expense"
    )

    _sql_constraints = [
        ('unique_site_project',
         'unique(site_name,project_id)',
         'Site Name must be unique per Project!')
    ]

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
        if vals.get('site_code', 'New') == 'New':
            vals['site_code'] = self.env['ir.sequence'].next_by_code('site_seq') or 'New'
        return super(ConstructionSite, self).create(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError("End Date must be after Start Date!")

    @api.constrains('start_date')
    def _check_start_date(self):
        for rec in self:
            if rec.start_date and rec.start_date < fields.Date.today():
                raise ValidationError("Start Date cannot be in the past!")

    @api.depends('workforce_ids')
    def _compute_workforce_counts(self):
        for rec in self:
            rec.workforce_count = len(rec.workforce_ids)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.duration = (rec.end_date - rec.start_date).days
            else:
                rec.duration = 0

    def check_site_status(self):
        today = fields.Date.today()
        for rec in self.search([]):
            if rec.end_date and rec.end_date < today:
                rec.state = 'done'

    @api.depends('material_ids.total_price')
    def _compute_total_material_cost(self):
        for rec in self:
            rec.total_material_cost = sum(rec.material_ids.mapped('total_price'))

    @api.depends('expense_ids.amount')
    def _compute_total_expense(self):
        for rec in self:
            rec.total_expense = sum(rec.expense_ids.mapped('amount'))
