# -*- coding: utf-8 -*-
{
    'name': "Payroll - Shariah / International Deduction System",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': "Adds Shariah / International payroll type to hr.payslip with "
               "late-minute, day-off and sandwich-leave deduction logic.",
    'description': """
Adds a choice (radio button) on hr.payslip to select:
  - Shariah Payroll System
  - International Payroll System

Shariah System
--------------
* Late check-in/check-out minutes are deducted from wage on a per-minute basis.
* A full day with no attendance (day off / absence) deducts one full day wage.

International System
---------------------
* Late minutes (<= 30 min) are deducted on a per-minute basis, same as Shariah.
* If an employee checks in more than 30 minutes late, the ENTIRE day is
  treated as absent (day-off deduction) instead of a minute deduction.
* Sandwich Leave Rule: if the employee takes leave on the working day right
  before a weekend and the working day right after it (e.g. Friday and the
  following Monday, with Saturday/Sunday as weekend), all days in between
  (Fri, Sat, Sun, Mon = 4 days) are counted and deducted as leave, not just
  the 2 requested days.

Both systems pull their data live from hr.payslip (attendances + leaves in
the payslip's date range) and compute deduction amounts that feed into the
payslip's salary rules.
""",
    'author': "Your Company",
    'depends': ['hr_payroll_community', 'hr_attendance', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_salary_rule_data.xml',
        'views/hr_payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
