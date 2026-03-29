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

    worker_ids = fields.Many2many('res.partner', string='Workers')
    engineer_ids = fields.Many2many('res.users', string='Engineers')
    worker_count = fields.Integer(string='Workers Count', compute='_compute_counts', readonly=True)
    engineer_count = fields.Integer(string='Engineers Count', compute='_compute_counts', readonly=True)

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

    @api.depends('worker_ids', 'engineer_ids')
    def _compute_counts(self):
        for rec in self:
            rec.worker_count = len(rec.worker_ids)
            rec.engineer_count = len(rec.engineer_ids)

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
