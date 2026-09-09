{
    'name': 'Invoice Payment Reminder Notification',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Reminder Day field on invoices + Notification menu when due date approaches reminder day',
    'description': """
Invoice Payment Reminder Notification
======================================
- Adds a "Reminder Day" field on Customer Invoices (account.move), placed right
  after the "Payment Terms" field.
- A scheduled action (cron) checks daily how many days remain until the
  invoice due date (based on Payment Terms). When the remaining days match
  the value set in "Reminder Day", a Notification record is created.
- Adds a "Notification" menu (placed after "Import Module" in the Apps
  technical bar) listing all triggered reminder notifications.

Example: Payment Term = 10 days, Reminder Day = 3.
When the invoice has 3 days left before its due date, a notification is
generated automatically.
    """,
    'author': 'Custom Development',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/notification_views.xml',
        'data/ir_cron.xml',
    ],
    'assets': {
            'web.assets_backend': [
                'invoice_payment_reminder/static/src/js/reminder_notification.js',
            ],
        },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
