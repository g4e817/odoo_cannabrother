# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import os
from tools import config

from base_module_quality import base_module_quality
import pooler

class quality_test(base_module_quality.abstract_quality_check):

    def __init__(self):
        super(quality_test, self).__init__()
        self.bool_installed_only = True
        self.ponderation = 1.0
        self.result_det = {}
        return None

    def run_test(self, cr, uid, module_path):
        pool = pooler.get_pool(cr.dbname)
        module_name = module_path.split('/')[-1]
        obj_list = self.get_objects(cr, uid, module_name)
        ok_count = 0
        ex_count = 0
        for obj in obj_list:
            temp = []
            try:
                res = pool.get(obj).search(cr, uid, [])
                temp.append('Ok')
                ok_count += 1
            except:
                temp.append('Exception')
                ex_count += 1
            try:
                res1 = pool.get(obj).fields_view_get(cr, uid,)
                temp.append('Ok')
                ok_count += 1
            except:
                temp.append('Exception')
                ex_count += 1
            try:
                res2 = pool.get(obj).read(cr, uid, [])
                temp.append('Ok')
                ok_count += 1
            except:
                temp.append('Exception')
                ex_count += 1
            self.result_det[obj] = temp
        self.score = (ok_count + ex_count) and float(ok_count)/float(ok_count + ex_count) or 0.0
        self.result = self.get_result()
        self.result_details = self.get_result_details()

        return None


    def get_result(self):
        summary = """
===Method Test===:

This test checks if the module classes are raising exception when calling basic methods or no.

""" + "Score: " + str(self.score) + "/10\n"
        return summary

    def get_result_details(self):
        header_list = ['method', 'Object Name', 'search()', 'fields_view_get', 'read']
        detail = "\n===Method Test===\n"
        if not self.error:
            detail += self.format_table(header=header_list, data_list=[self.result_det])
        return detail

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

