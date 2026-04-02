from email.policy import default

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ConstructionSiteMaterial(models.Model):
    _name = 'construction.site.material'
    _description = 'Materials per Site '
    _rec_name = 'material_name'

    material_name = fields.Char(string='Material Name', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    total_price = fields.Float(string='Total Price', compute='_compute_total_price', store=True)
    site_id = fields.Many2one(comodel_name='construction.site', string='Site', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    note = fields.Text(string="Notes")

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = rec.quantity * rec.unit_price

    @api.constrains('material_name', 'site_id')
    def _check_unique_material_per_site(self):
        for rec in self:
            duplicate_material = self.search([
                ('material_name', '=', rec.material_name),
                ('site_id', '=', rec.site_id.id),
                ('date', '=', rec.date),
                ('id', '!=', rec.id),
            ])
            if duplicate_material:
                raise ValidationError(f"Material: '{rec.material_name}' already exists for this site.'")
