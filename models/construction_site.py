from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionSite(models.Model):
    _name = 'construction.site'
    _description = 'Sites'
    _rec_name = 'site_name'

    project_id = fields.Many2one('construction.project', string='Projects')
    site_name = fields.Char(string='Site Name')
    site_code = fields.Char(default='New', string='Site Code', readonly=True)
    location = fields.Char(string='Location', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', required=True)

    worker_ids = fields.Many2many('res.partner', string='Workers')
    engineer_ids = fields.Many2many('res.users', string='Engineers')

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
