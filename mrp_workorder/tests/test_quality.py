# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestQuality(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_1 = cls.env['product.product'].create({'name': 'Table'})
        cls.product_2 = cls.env['product.product'].create({'name': 'Table top'})
        cls.product_3 = cls.env['product.product'].create({'name': 'Table leg'})
        cls.workcenter_1 = cls.env['mrp.workcenter'].create({
            'name': 'Test Workcenter',
            'capacity': 2,
            'time_start': 10,
            'time_stop': 5,
            'time_efficiency': 80,
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product_1.id,
            'product_tmpl_id': cls.product_1.product_tmpl_id.id,
            'product_uom_id': cls.product_1.uom_id.id,
            'product_qty': 1.0,
            'consumption': 'flexible',
            'operation_ids': [
                (0, 0, {'name': 'Assembly', 'workcenter_id': cls.workcenter_1.id, 'time_cycle': 15, 'sequence': 1}),
            ],
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': cls.product_2.id, 'product_qty': 1}),
                (0, 0, {'product_id': cls.product_3.id, 'product_qty': 4})
            ]
        })

    def test_quality_point_onchange(self):
        quality_point_form = Form(self.env['quality.point'].with_context(default_product_ids=[self.product_2.id]))
        # Form should keep the default products set
        self.assertEqual(len(quality_point_form.product_ids), 1)
        self.assertEqual(quality_point_form.product_ids[0].id, self.product_2.id)
        # Select a workorder operation
        quality_point_form.operation_id = self.bom.operation_ids[0]
        quality_point_form.product_ids
        # Product should be replaced by the product linked to the bom
        self.assertEqual(len(quality_point_form.product_ids), 1)
        self.assertEqual(quality_point_form.product_ids[0].id, self.bom.product_id.id)

    def test_delete_move_linked_to_quality_check(self):
        """
        Test that a quality check is deleted when its linked move is deleted.
        """
        self.bom.bom_line_ids.product_id.tracking = 'lot'
        self.bom.bom_line_ids.product_id.type = 'product'
        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = self.bom
        mo = mo_form.save()
        mo.action_confirm()
        qc = self.env['quality.check'].search([('product_id', '=', self.bom.product_id.id)])[-1]
        move = qc.move_id
        self.assertEqual(len(qc), 1)
        self.assertFalse(move.move_line_ids)
        move.state = 'draft'
        move.unlink()
        self.assertFalse(move.exists())
        self.assertFalse(qc.exists())
